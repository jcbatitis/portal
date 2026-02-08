# Portal — Personal Services Portal

## What is this?

A monorepo for a personal services portal. Backend API + frontend client managed via npm workspaces.

## Tech Stack

- **Monorepo**: npm workspaces (`backend/`, `frontend/`)
- **Backend**: Node.js, Fastify, TypeScript
- **Database**: PostgreSQL via Drizzle ORM
- **Testing**: Vitest

## Project Structure

```
portal/
├── backend/          # Fastify API server
│   ├── src/
│   │   ├── app.ts         # buildApp() factory (used by tests)
│   │   ├── index.ts       # Entry point (imports app.ts, calls start)
│   │   ├── config.ts      # Environment config via @fastify/env
│   │   ├── db/            # Drizzle client and schema
│   │   ├── plugins/       # Fastify plugins (db, etc.)
│   │   └── routes/        # Route handlers
│   └── test/
├── frontend/         # Frontend (TBD)
└── docs/plans/       # Design documents
```

## Commands

```bash
# From root
npm run dev:backend        # Start backend with hot reload
npm run test:backend       # Run backend tests

# From backend/
npm run dev                # tsx watch src/index.ts
npm run build              # tsc
npm run start              # node dist/index.js
npm run test               # vitest run
npm run db:generate        # drizzle-kit generate
npm run db:migrate         # drizzle-kit migrate
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PORT` | `3000` | Server port |
| `HOST` | `0.0.0.0` | Bind address |
| `DATABASE_URL` | `postgres://localhost:5432/portal` | PostgreSQL connection |
| `NODE_ENV` | `development` | Environment |

## Architecture Patterns

- **Fastify plugins**: Each concern (db, routes) is a self-contained plugin registered via `fastify.register()`
- **Separated app/start**: `buildApp()` in `app.ts` returns a testable instance, `index.ts` calls `start()` to bind a port. Tests import from `app.ts` to avoid triggering the server
- **Drizzle ORM**: Type-safe SQL with `pg` driver. Schema in `src/db/schema.ts`, migrations via `drizzle-kit`

## Conventions

- TypeScript strict mode
- ESM modules
- Routes organized by domain in `src/routes/`
- Tests colocated in `test/` using Vitest + Fastify's `inject()`
