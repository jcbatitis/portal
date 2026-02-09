import { describe, it, expect, afterAll } from 'vitest';
import { buildApp } from '../src/app.js';

// Use a low global limit so we don't need 101 requests.
process.env.RATE_LIMIT_MAX = '10';

const app = await buildApp();

afterAll(async () => {
  await app.close();
});

describe('Global rate limit', () => {
  it('returns 429 after exceeding the global limit', async () => {
    const max = 10;

    for (let i = 0; i < max; i++) {
      const res = await app.inject({ method: 'GET', url: '/api/health' });
      expect(res.statusCode).toBe(200);
    }

    const blocked = await app.inject({ method: 'GET', url: '/api/health' });
    expect(blocked.statusCode).toBe(429);
    expect(blocked.json()).toMatchObject({ error: 'Too many requests, please try again later' });
    expect(blocked.headers['retry-after']).toBeDefined();
  });

  it('includes rate limit headers on normal responses', async () => {
    // Use a different route to avoid the exhausted /health counter.
    const res = await app.inject({ method: 'GET', url: '/api/me' });
    expect(res.headers['x-ratelimit-limit']).toBeDefined();
    expect(res.headers['x-ratelimit-remaining']).toBeDefined();
  });
});

describe('Login rate limit', () => {
  it('returns 429 after exceeding the login limit', async () => {
    const max = 5;

    for (let i = 0; i < max; i++) {
      await app.inject({
        method: 'POST',
        url: '/api/login',
        payload: { username: 'nobody', password: 'wrong' },
      });
    }

    const blocked = await app.inject({
      method: 'POST',
      url: '/api/login',
      payload: { username: 'nobody', password: 'wrong' },
    });

    expect(blocked.statusCode).toBe(429);
    expect(blocked.json()).toMatchObject({ error: 'Too many requests, please try again later' });
  });
});
