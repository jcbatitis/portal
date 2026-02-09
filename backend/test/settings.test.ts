import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import bcrypt from 'bcrypt';
import { buildApp } from '../src/app.js';
import { users, userSettings } from '../src/db/schema.js';
import { eq } from 'drizzle-orm';

process.env.RATE_LIMIT_LOGIN_MAX = '50';

const app = await buildApp();

beforeAll(async () => {
  const passwordHash = await bcrypt.hash('testpass', 10);
  await app.db
    .insert(users)
    .values({ username: 'settingsuser', passwordHash })
    .onConflictDoNothing({ target: users.username });
});

afterAll(async () => {
  // Clean up settings created during tests
  const [user] = await app.db
    .select({ id: users.id })
    .from(users)
    .where(eq(users.username, 'settingsuser'))
    .limit(1);
  if (user) {
    await app.db.delete(userSettings).where(eq(userSettings.userId, user.id));
  }
  await app.close();
});

function extractCookie(response: Awaited<ReturnType<typeof app.inject>>): string {
  const setCookie = response.headers['set-cookie'];
  if (!setCookie) return '';
  const header = Array.isArray(setCookie) ? setCookie[0] : setCookie;
  return header.split(';')[0];
}

async function login(): Promise<string> {
  const response = await app.inject({
    method: 'POST',
    url: '/api/login',
    payload: { username: 'settingsuser', password: 'testpass' },
  });
  return extractCookie(response);
}

describe('GET /api/settings', () => {
  it('returns defaults when no settings exist', async () => {
    const cookie = await login();

    const response = await app.inject({
      method: 'GET',
      url: '/api/settings',
      headers: { cookie },
    });

    expect(response.statusCode).toBe(200);
    expect(response.json()).toEqual({
      theme: 'system',
      display_name: '',
    });
  });

  it('returns 401 without session', async () => {
    const response = await app.inject({
      method: 'GET',
      url: '/api/settings',
    });

    expect(response.statusCode).toBe(401);
    expect(response.json()).toEqual({ error: 'Not authenticated' });
  });
});

describe('PATCH /api/settings', () => {
  it('upserts a single setting', async () => {
    const cookie = await login();

    const response = await app.inject({
      method: 'PATCH',
      url: '/api/settings',
      headers: { cookie },
      payload: { theme: 'dark' },
    });

    expect(response.statusCode).toBe(200);
    expect(response.json()).toEqual({
      theme: 'dark',
      display_name: '',
    });
  });

  it('upserts multiple settings', async () => {
    const cookie = await login();

    const response = await app.inject({
      method: 'PATCH',
      url: '/api/settings',
      headers: { cookie },
      payload: { theme: 'light', display_name: 'Test User' },
    });

    expect(response.statusCode).toBe(200);
    expect(response.json()).toEqual({
      theme: 'light',
      display_name: 'Test User',
    });
  });

  it('rejects unknown keys', async () => {
    const cookie = await login();

    const response = await app.inject({
      method: 'PATCH',
      url: '/api/settings',
      headers: { cookie },
      payload: { foo: 'bar' },
    });

    expect(response.statusCode).toBe(400);
    expect(response.json()).toEqual({ error: 'Unknown setting: foo' });
  });

  it('rejects invalid theme values', async () => {
    const cookie = await login();

    const response = await app.inject({
      method: 'PATCH',
      url: '/api/settings',
      headers: { cookie },
      payload: { theme: 'neon' },
    });

    expect(response.statusCode).toBe(400);
    expect(response.json()).toEqual({
      error: 'Invalid value for theme: must be one of light, dark, system',
    });
  });

  it('rejects empty display_name', async () => {
    const cookie = await login();

    const response = await app.inject({
      method: 'PATCH',
      url: '/api/settings',
      headers: { cookie },
      payload: { display_name: '' },
    });

    expect(response.statusCode).toBe(400);
    expect(response.json()).toEqual({
      error: 'Invalid value for display_name: must be a non-empty string (max 255 chars)',
    });
  });

  it('rejects display_name exceeding 255 chars', async () => {
    const cookie = await login();

    const response = await app.inject({
      method: 'PATCH',
      url: '/api/settings',
      headers: { cookie },
      payload: { display_name: 'a'.repeat(256) },
    });

    expect(response.statusCode).toBe(400);
    expect(response.json()).toEqual({
      error: 'Invalid value for display_name: must be a non-empty string (max 255 chars)',
    });
  });

  it('returns 400 with empty body', async () => {
    const cookie = await login();

    const response = await app.inject({
      method: 'PATCH',
      url: '/api/settings',
      headers: { cookie },
      payload: {},
    });

    expect(response.statusCode).toBe(400);
    expect(response.json()).toEqual({ error: 'No settings provided' });
  });

  it('returns 401 without session', async () => {
    const response = await app.inject({
      method: 'PATCH',
      url: '/api/settings',
      payload: { theme: 'dark' },
    });

    expect(response.statusCode).toBe(401);
    expect(response.json()).toEqual({ error: 'Not authenticated' });
  });

  it('response always includes all keys with defaults filled in', async () => {
    const cookie = await login();

    // Set only theme
    const response = await app.inject({
      method: 'PATCH',
      url: '/api/settings',
      headers: { cookie },
      payload: { theme: 'system' },
    });

    const body = response.json();
    expect(body).toHaveProperty('theme');
    expect(body).toHaveProperty('display_name');
  });
});
