# Auth Login Design

## Overview

Session + cookie authentication with username/password login, PostgreSQL session store, and a seed script for a test user.

## Database Schema

### `users` table (Drizzle-managed)

| Column        | Type         | Constraints              |
|---------------|--------------|--------------------------|
| id            | serial       | PRIMARY KEY              |
| username      | varchar(255) | UNIQUE NOT NULL          |
| password_hash | varchar(255) | NOT NULL                 |
| created_at    | timestamp    | DEFAULT now()            |
| updated_at    | timestamp    | DEFAULT now()            |

### `session` table (managed by connect-pg-simple)

| Column | Type      | Constraints |
|--------|-----------|-------------|
| sid    | varchar   | PRIMARY KEY |
| sess   | json      | NOT NULL    |
| expire | timestamp | NOT NULL    |

## Dependencies

- `@fastify/session` — session management
- `@fastify/cookie` — cookie parsing (required by session)
- `connect-pg-simple` — PostgreSQL session store
- `bcrypt` — password hashing
- `@types/bcrypt`, `@types/connect-pg-simple` — dev types

## New Environment Variables

- `SESSION_SECRET` — required, random string for signing cookies

## New Files

```
backend/src/
├── plugins/
│   └── session.ts      # Fastify plugin: cookie + session with pg store
├── routes/
│   └── auth.ts         # POST /login, POST /logout, GET /me
backend/scripts/
└── seed.ts             # Idempotent test user seed (admin / admin123)
```

## API Endpoints

| Method | Path     | Auth | Description                                    |
|--------|----------|------|------------------------------------------------|
| POST   | /login   | No   | `{ username, password }` → creates session     |
| POST   | /logout  | Yes  | Destroys session, clears cookie                |
| GET    | /me      | Yes  | Returns current user from session or 401       |

## Login Flow

1. Look up user by username
2. `bcrypt.compare()` against stored hash
3. If valid → set `request.session.userId` and `request.session.username`, return `{ username }`
4. If invalid → 401 `{ error: "Invalid credentials" }`

## Plugin Registration Order

```
1. @fastify/env       ← config + dotenv
2. dbPlugin           ← fastify.db
3. sessionPlugin      ← cookie + session with pg store (needs DATABASE_URL)
4. healthRoutes       ← GET /health, GET /health/db
5. authRoutes         ← POST /login, POST /logout, GET /me
```

## Seed Script

- `backend/scripts/seed.ts` creates user `admin` / `admin123` (bcrypt-hashed)
- Uses `INSERT ... ON CONFLICT (username) DO NOTHING` — idempotent
- New npm script: `db:seed`
- Runs automatically in Docker on container start

## Auth Guard

No shared `preHandler` hook for now — `/logout` and `/me` check `request.session.userId` inline. Extract a reusable `requireAuth` hook when 3+ routes need protection.

## Testing

New `backend/test/auth.test.ts` using `buildApp()` + `inject()`:
- Login with valid credentials
- Login with invalid credentials (wrong password, nonexistent user)
- GET /me with and without session
- POST /logout clears session
