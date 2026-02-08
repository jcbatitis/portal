# Rate Limiting Design

## Context

The API has no request throttling. Any client can hit any endpoint without limit, leaving `POST /login` vulnerable to brute-force attacks and all endpoints exposed to abuse.

## Approach

Use `@fastify/rate-limit` with an in-memory store. Two tiers: a global baseline limit on all routes plus a stricter override on login.

- **Global**: 100 requests per minute per IP (configurable via `RATE_LIMIT_MAX` env var)
- **Login**: 5 requests per minute per IP on `POST /login` (configurable via `RATE_LIMIT_LOGIN_MAX` env var)
- **Store**: In-memory (default). Counters reset on restart. Swap to Redis later by changing one config option.
- **Key**: `request.ip`

## Changes

### 1. `backend/src/plugins/rate-limit.ts` (new)

Fastify plugin that registers `@fastify/rate-limit` globally:

- `max`: reads from `fastify.config.RATE_LIMIT_MAX` (default 100)
- `timeWindow`: `'1 minute'`
- `errorResponseBuilder`: returns `{ statusCode: 429, error: 'Too many requests, please try again later' }`
- Uses `fp` wrapper so the plugin applies across all route scopes

### 2. `backend/src/routes/auth.ts`

Add route-level rate limit override to `POST /login`:

```ts
{
  schema: { /* existing */ },
  config: {
    rateLimit: { max: fastify.config.RATE_LIMIT_LOGIN_MAX, timeWindow: '1 minute' }
  }
}
```

### 3. `backend/src/app.ts`

Register `rateLimitPlugin` after `sessionPlugin`, before route plugins.

### 4. `backend/src/config.ts`

Add `RATE_LIMIT_MAX` (integer, default 100) and `RATE_LIMIT_LOGIN_MAX` (integer, default 5) to env schema.

### 5. No changes to `health.ts` (covered by global limit)

## Testing

### `backend/test/rate-limit.test.ts` (new)

Dedicated app instance to isolate rate limit counters from other test files.

Uses `RATE_LIMIT_MAX=10` to keep iterations low.

1. **Global limit**: Send 11 `GET /health` requests. Assert request 11 returns 429.
2. **Login limit**: Send 6 `POST /login` requests. Assert request 6 returns 429.
3. Verify 429 response includes `Retry-After` header.
4. Verify `x-ratelimit-limit` and `x-ratelimit-remaining` headers on normal responses.

Auth tests set `RATE_LIMIT_LOGIN_MAX=50` to avoid being throttled by the login limit.

## Response Behavior

- 429 body: `{ error: 'Too many requests, please try again later' }`
- Auto-added headers on all responses: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- `Retry-After` header on 429 responses

## Verification

1. `npm run test:backend` passes (existing + new tests)
2. Manual test: `for i in $(seq 1 6); do curl -s -o /dev/null -w "%{http_code}\n" -X POST localhost:3000/login -H 'Content-Type: application/json' -d '{"username":"x","password":"x"}'; done` — 6th request returns 429
