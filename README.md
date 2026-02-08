# Portal

Personal services portal — a monorepo with a Fastify backend and frontend client.

## Prerequisites

- Docker and Docker Compose
- Node.js >= 22 (for local development without Docker)

## Quick Start (Docker)

```bash
# Start everything (PostgreSQL + backend)
./scripts.sh up

# Stop
./scripts.sh down

# Nuke and rebuild from scratch
./scripts.sh reset
```

The backend runs on `http://localhost:3000`.

## Local Development (without Docker)

```bash
npm install
createdb portal
npm run db:migrate -w backend
npm run dev:backend
```

## Docker Commands

| Command | Description |
|---|---|
| `./scripts.sh up` | Build and start all services |
| `./scripts.sh down` | Stop containers, keep data |
| `./scripts.sh reset` | Down + delete data + rebuild + up |
| `./scripts.sh build` | Force rebuild images |
| `./scripts.sh logs` | Tail all service logs |
| `./scripts.sh db:shell` | Open psql shell |

## Environment Variables

Copy `.env.example` to `.env` at the project root and adjust as needed:

```env
# Docker / PostgreSQL
POSTGRES_DB=portal
POSTGRES_USER=portal
POSTGRES_PASSWORD=portal

# Session
SESSION_SECRET=change-me-to-a-random-32-char-string

# Postman sync (optional)
POSTMAN_API_KEY=
POSTMAN_WORKSPACE_ID=
```

For local development (without Docker), also create `backend/.env` — see `backend/.env.example`.

## Project Structure

```
portal/
├── backend/          # Fastify API (TypeScript)
├── frontend/         # Frontend client (TBD)
└── docs/plans/       # Design documents
```

## API Endpoints

| Method | Path         | Auth | Description                          |
|--------|--------------|------|--------------------------------------|
| GET    | /health      | No   | Server health check                  |
| GET    | /health/db   | No   | Database connectivity check          |
| POST   | /login       | No   | Login with `{ username, password }`  |
| POST   | /logout      | Yes  | Destroy session                      |
| GET    | /me          | Yes  | Current user info                    |

### Test User

Docker automatically seeds a test user on first start:
- **Username:** `admin`
- **Password:** `admin123`

## Postman Sync

Routes are automatically synced to a Postman collection on every git commit via a pre-commit hook. To set up:

1. Get your [Postman API key](https://go.postman.co/settings/me/api-keys)
2. Find your workspace ID from the Postman workspace URL
3. Add both to `backend/.env`

You can also run `npm run postman:sync` manually.
