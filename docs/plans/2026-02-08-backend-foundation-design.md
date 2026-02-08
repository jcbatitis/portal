# Backend Foundation Design

## Overview

Personal services portal backend using Fastify, TypeScript, PostgreSQL (via Drizzle ORM), in an npm workspaces monorepo. Initial scope: health check endpoints.

## Project Structure

```
portal/
├── CLAUDE.md
├── package.json               # Root workspace config
├── .gitignore
├── backend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── drizzle.config.ts
│   ├── src/
│   │   ├── index.ts           # Server entry point
│   │   ├── config.ts          # Env vars & configuration
│   │   ├── db/
│   │   │   ├── index.ts       # Drizzle client setup
│   │   │   └── schema.ts      # Drizzle schema (empty for now)
│   │   ├── routes/
│   │   │   └── health.ts      # GET /health & GET /health/db
│   │   └── plugins/
│   │       └── db.ts          # Fastify plugin decorating with db client
│   └── test/
│       └── health.test.ts
└── frontend/
    └── .gitkeep
```

## Dependencies

### Production
- `fastify` — web framework
- `drizzle-orm` + `pg` — ORM and PostgreSQL driver
- `@fastify/env` — schema-validated environment variables

### Development
- `typescript`, `tsx` — compilation and dev runner
- `drizzle-kit` — migrations CLI
- `@types/pg`, `@types/node`
- `vitest` — test runner

## Configuration

| Variable | Default | Description |
|---|---|---|
| `PORT` | `3000` | Server port |
| `HOST` | `0.0.0.0` | Bind address |
| `DATABASE_URL` | `postgres://localhost:5432/portal` | PostgreSQL connection string |
| `NODE_ENV` | `development` | Environment |

Validated at startup via `@fastify/env` with JSON schema. Server fails fast on missing config.

## Scripts

### backend/package.json
- `dev` — `tsx watch src/index.ts`
- `build` — `tsc`
- `start` — `node dist/index.js`
- `test` — `vitest run`
- `db:generate` — `drizzle-kit generate`
- `db:migrate` — `drizzle-kit migrate`

### Root package.json
- `dev:backend` — `npm run dev -w backend`
- `test:backend` — `npm run test -w backend`

## Architecture

### Plugin Pattern
Fastify's plugin system structures the app into self-contained modules:

1. **Database plugin** (`src/plugins/db.ts`) — Creates Drizzle client from `DATABASE_URL`, decorates Fastify instance with `fastify.db`. Closes the `pg` pool on server shutdown.

2. **Route plugins** (`src/routes/health.ts`) — Each route file exports a Fastify plugin. Health routes register under a `/health` prefix.

### Server Bootstrap (`src/index.ts`)
- `buildApp()` — Creates Fastify instance, registers env plugin, db plugin, and routes. Returns the app instance (testable without binding to a port).
- `start()` — Calls `buildApp()`, then `listen()` on configured HOST:PORT.

### Endpoints

- **`GET /health`** — Returns `{ status: "ok" }`. No DB call.
- **`GET /health/db`** — Runs `SELECT 1` via Drizzle. Returns `{ status: "ok", db: "connected" }` or error response.

## Testing

Uses `vitest` + Fastify's `inject()` for in-memory HTTP simulation:
- `GET /health` returns 200 with `{ status: "ok" }`
- `GET /health/db` returns 200 when DB is reachable

No mocking — real database connections in tests.
