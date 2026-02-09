import { describe, it, expect, afterAll } from 'vitest';
import { buildApp } from '../src/app.js';

const app = await buildApp();

afterAll(async () => {
  await app.close();
});

describe('GET /health', () => {
  it('returns status ok', async () => {
    const response = await app.inject({
      method: 'GET',
      url: '/api/health',
    });

    expect(response.statusCode).toBe(200);
    expect(response.json()).toEqual({ status: 'ok' });
  });
});

describe('GET /health/db', () => {
  it('returns db connected when database is reachable', async () => {
    const response = await app.inject({
      method: 'GET',
      url: '/api/health/db',
    });

    expect(response.statusCode).toBe(200);
    expect(response.json()).toEqual({ status: 'ok', db: 'connected' });
  });
});
