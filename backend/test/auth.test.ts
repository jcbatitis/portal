import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import bcrypt from 'bcrypt';
import { buildApp } from '../src/app.js';
import { users } from '../src/db/schema.js';

const app = await buildApp();

beforeAll(async () => {
  // Seed a test user directly
  const passwordHash = await bcrypt.hash('testpass', 10);
  await app.db
    .insert(users)
    .values({ username: 'testuser', passwordHash })
    .onConflictDoNothing({ target: users.username });
});

afterAll(async () => {
  await app.close();
});

function extractCookie(response: { headers: Record<string, string | string[] | undefined> }): string {
  const setCookie = response.headers['set-cookie'];
  if (!setCookie) return '';
  const header = Array.isArray(setCookie) ? setCookie[0] : setCookie;
  return header.split(';')[0];
}

describe('POST /login', () => {
  it('returns username on valid credentials', async () => {
    const response = await app.inject({
      method: 'POST',
      url: '/login',
      payload: { username: 'testuser', password: 'testpass' },
    });

    expect(response.statusCode).toBe(200);
    expect(response.json()).toEqual({ username: 'testuser' });
    expect(response.headers['set-cookie']).toBeDefined();
  });

  it('returns 401 on wrong password', async () => {
    const response = await app.inject({
      method: 'POST',
      url: '/login',
      payload: { username: 'testuser', password: 'wrong' },
    });

    expect(response.statusCode).toBe(401);
    expect(response.json()).toEqual({ error: 'Invalid credentials' });
  });

  it('returns 401 on nonexistent user', async () => {
    const response = await app.inject({
      method: 'POST',
      url: '/login',
      payload: { username: 'nobody', password: 'whatever' },
    });

    expect(response.statusCode).toBe(401);
    expect(response.json()).toEqual({ error: 'Invalid credentials' });
  });

  it('returns 400 when username or password is missing', async () => {
    const response = await app.inject({
      method: 'POST',
      url: '/login',
      payload: { username: 'testuser' },
    });

    expect(response.statusCode).toBe(400);
  });
});

describe('GET /me', () => {
  it('returns user info with valid session', async () => {
    const loginResponse = await app.inject({
      method: 'POST',
      url: '/login',
      payload: { username: 'testuser', password: 'testpass' },
    });

    const cookie = extractCookie(loginResponse);

    const meResponse = await app.inject({
      method: 'GET',
      url: '/me',
      headers: { cookie },
    });

    expect(meResponse.statusCode).toBe(200);
    const body = meResponse.json();
    expect(body.username).toBe('testuser');
    expect(body.userId).toBeDefined();
  });

  it('returns 401 without session', async () => {
    const response = await app.inject({
      method: 'GET',
      url: '/me',
    });

    expect(response.statusCode).toBe(401);
    expect(response.json()).toEqual({ error: 'Not authenticated' });
  });
});

describe('POST /logout', () => {
  it('destroys session and returns logged out', async () => {
    const loginResponse = await app.inject({
      method: 'POST',
      url: '/login',
      payload: { username: 'testuser', password: 'testpass' },
    });

    const cookie = extractCookie(loginResponse);

    const logoutResponse = await app.inject({
      method: 'POST',
      url: '/logout',
      headers: { cookie },
    });

    expect(logoutResponse.statusCode).toBe(200);
    expect(logoutResponse.json()).toEqual({ status: 'logged out' });

    // Session should be invalidated
    const meResponse = await app.inject({
      method: 'GET',
      url: '/me',
      headers: { cookie },
    });

    expect(meResponse.statusCode).toBe(401);
  });

  it('returns 401 without session', async () => {
    const response = await app.inject({
      method: 'POST',
      url: '/logout',
    });

    expect(response.statusCode).toBe(401);
  });
});
