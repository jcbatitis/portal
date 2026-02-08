# Portal — Claude Guide

## Tech Stack

- **Monorepo**: npm workspaces (`backend/`, `frontend/`)
- **Backend**: Node.js, Fastify v5, TypeScript (strict)
- **Database**: PostgreSQL via Drizzle ORM with `pg` (node-postgres) driver
- **Auth**: Session + cookie via `@fastify/session`, PostgreSQL session store (`connect-pg-simple`), bcrypt password hashing
- **Testing**: Vitest with Fastify's `inject()` for in-memory HTTP

## Commands

```bash
npm run dev:backend        # Hot reload backend (tsx watch)
npm run test:backend       # Run backend tests (vitest)
npm run build -w backend   # TypeScript compile
npm run db:generate -w backend  # Generate Drizzle migrations
npm run db:migrate -w backend   # Run Drizzle migrations
npm run postman:sync            # Sync routes to Postman (also runs on pre-commit)
npm run db:seed -w backend      # Seed test user (admin/admin123)

# Docker
./scripts.sh up                 # Build and start PostgreSQL + backend
./scripts.sh down               # Stop containers, keep data
./scripts.sh reset              # Nuke everything, rebuild, start fresh
./scripts.sh logs               # Tail all service logs
./scripts.sh db:shell           # psql into running database
npm run docker:up               # Alias for ./scripts.sh up
npm run docker:down             # Alias for ./scripts.sh down
npm run docker:reset            # Alias for ./scripts.sh reset
```

## Architecture

### Backend Structure

```
backend/src/
├── app.ts             # buildApp() factory — creates and configures the Fastify instance
├── index.ts           # Entry point — imports buildApp(), calls start()
├── config.ts          # @fastify/env schema and type declarations
├── db/
│   ├── index.ts       # createDb() — Drizzle client with pg Pool
│   └── schema.ts      # Drizzle table definitions
├── plugins/
│   ├── db.ts          # Fastify plugin: decorates `fastify.db` and `fastify.pgPool`
│   └── session.ts     # Fastify plugin: cookie + session with PostgreSQL store
└── routes/
    ├── health.ts      # GET /health, GET /health/db
    └── auth.ts        # POST /login, POST /logout, GET /me
backend/scripts/
├── postman-sync.ts    # Syncs registered routes to Postman collection
└── seed.ts            # Seeds test user (admin/admin123), idempotent
```

### Key Patterns

- **Fastify plugins**: Each concern (db, routes) is a self-contained plugin via `fastify.register()`. Use `fastify-plugin` (`fp`) only when decorators must be visible outside the plugin scope (e.g., `db.ts`). Route files should NOT use `fp`.
- **app.ts / index.ts split**: `buildApp()` lives in `app.ts` so tests can import it without triggering `start()`. Tests import from `app.ts`, never `index.ts`.
- **Drizzle ORM**: Schema in `db/schema.ts`. Use `db.execute()` for raw SQL, typed queries for everything else.
- **Type augmentation**: Extend Fastify types via `declare module 'fastify'` in the file that introduces the decorator (see `config.ts` and `plugins/db.ts`).
- **buildApp(app?)**: Accepts an optional Fastify instance so callers (like `postman-sync.ts`) can pre-attach hooks before plugin registration. Normal usage passes no argument.
- **Postman sync**: `scripts/postman-sync.ts` boots the app with an `onRoute` hook, collects all routes, then syncs to Postman via API. Runs on every git commit (pre-commit hook) and gracefully skips if API key is missing.
- **Session auth**: `plugins/session.ts` sets up `@fastify/cookie` + `@fastify/session` with `connect-pg-simple` for PostgreSQL-backed sessions. Session data typed via `declare module 'fastify' { interface Session }`. The session store shares the same `pg.Pool` as Drizzle ORM via `fastify.pgPool`.
- **Auth routes**: No shared auth middleware yet — `/logout` and `/me` check `request.session.userId` inline. Extract a `requireAuth` preHandler when 3+ routes need protection.
- **Seed script**: `scripts/seed.ts` creates a test user (`admin`/`admin123`) using `INSERT ... ON CONFLICT DO NOTHING`. Runs automatically in Docker on container start (after migrations).

## Conventions

- TypeScript strict mode, ESM (`"type": "module"`)
- Use `.js` extensions in import paths (required for Node16 module resolution)
- Routes organized by domain in `src/routes/`
- Tests in `backend/test/` using Vitest + `app.inject()`
- No mocking — real database connections in tests
- Environment config validated at startup via `@fastify/env` JSON schema
