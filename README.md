# Portal

Personal services portal — a monorepo with a Fastify backend and frontend client.

## Prerequisites

- Node.js >= 22
- PostgreSQL >= 16

## Setup

```bash
# Install dependencies
npm install

# Create the database
createdb portal

# Run migrations
npm run db:migrate -w backend
```

## Development

```bash
# Start backend with hot reload
npm run dev:backend

# Run backend tests
npm run test:backend
```

The backend runs on `http://localhost:3000` by default.

## Environment Variables

Create a `.env` file in `backend/` to override defaults:

```env
PORT=3000
HOST=0.0.0.0
DATABASE_URL=postgres://localhost:5432/portal
NODE_ENV=development

# Postman sync (optional)
POSTMAN_API_KEY=
POSTMAN_WORKSPACE_ID=
```

See `backend/.env.example` for a full template.

## Project Structure

```
portal/
├── backend/          # Fastify API (TypeScript)
├── frontend/         # Frontend client (TBD)
└── docs/plans/       # Design documents
```

## API Endpoints

| Method | Path         | Description              |
|--------|--------------|--------------------------|
| GET    | /health      | Server health check      |
| GET    | /health/db   | Database connectivity check |

## Postman Sync

Routes are automatically synced to a Postman collection on every git commit via a pre-commit hook. To set up:

1. Get your [Postman API key](https://go.postman.co/settings/me/api-keys)
2. Find your workspace ID from the Postman workspace URL
3. Add both to `backend/.env`

You can also run `npm run postman:sync` manually.
