# Docker Setup Design

## Overview

Docker Compose configuration to run PostgreSQL and the backend together, with convenience scripts for build, up, down, and reset workflows.

## Services

### docker-compose.yml

**db** — PostgreSQL 16 Alpine
- Port: 5432:5432
- Persistent volume for data
- Healthcheck via pg_isready
- Credentials from root .env

**backend** — Node.js 22 Alpine (multi-stage Dockerfile)
- Port: 3000:3000
- Depends on db (waits for healthy)
- Volume mount for hot reload in dev
- DATABASE_URL injected by compose

### backend/Dockerfile (multi-stage)

1. **deps** — Install node_modules
2. **dev** — Run tsx watch (used in development with volume mount)
3. **prod** — Build TypeScript, run compiled JS

## Convenience Scripts

`scripts.sh` at project root:

| Command | Action |
|---|---|
| `./scripts.sh up` | Build and start all services |
| `./scripts.sh down` | Stop containers, keep data |
| `./scripts.sh reset` | Down + delete volumes + rebuild + up |
| `./scripts.sh build` | Force rebuild images |
| `./scripts.sh logs` | Tail all service logs |
| `./scripts.sh db:shell` | Open psql shell into running db |

Root package.json aliases: `docker:up`, `docker:down`, `docker:reset`.
