# Frontend Docker Setup Design

## Goal

Dockerize the frontend with a multi-stage Dockerfile (dev + prod), add it to the existing Docker Compose stack, and prepare Traefik labels for future homelab deployment.

## Decisions

- **Multi-stage Dockerfile**: 4 stages (deps → dev → build → prod), mirroring the backend pattern.
- **Dev target**: Vite dev server with hot reload via volume mounts.
- **Prod target**: nginx serving built static assets with SPA fallback routing.
- **Traefik**: External instance, labels commented out by default. Uncomment when deploying to homelab VM.
- **No new scripts**: Existing `docker:up/down/reset` in root `package.json` covers the new service automatically.

## New Files

### `frontend/Dockerfile`

4-stage multi-stage build:

| Stage   | Base            | Purpose                              |
| ------- | --------------- | ------------------------------------ |
| `deps`  | node:22-alpine  | Install npm dependencies             |
| `dev`   | deps            | Vite dev server, `--host 0.0.0.0`   |
| `build` | deps            | `npm run build` → outputs to `dist/` |
| `prod`  | nginx:alpine    | Serve `dist/` with SPA routing       |

- Dev stage exposes port 5173.
- Prod stage exposes port 80.
- `--host 0.0.0.0` required so Vite is reachable from outside the container.

### `frontend/nginx.conf`

Minimal nginx config for prod stage:

- Serve files from `/usr/share/nginx/html`.
- SPA fallback: `try_files $uri $uri/ /index.html`.
- Cache static assets (js, css, images) with long expiry.
- No caching on `index.html` so deploys pick up immediately.

## Modified Files

### `docker-compose.yml`

Add `frontend` service:

- Build from `./frontend`, target: `dev`.
- Port: `${VITE_PORT:-5173}:5173`.
- Volume mounts for hot reload:
  - `./frontend/src:/app/src`
  - `./frontend/index.html:/app/index.html`

Add commented-out Traefik configuration to both services:

- `frontend`: `PathPrefix(/)` with low priority.
- `backend`: `PathPrefix(/api)`.
- External `traefik` network.

## Dev Workflow

```bash
npm run docker:up     # Starts db + backend + frontend
                      # Frontend: localhost:5173
                      # Backend:  localhost:3000
```

## Homelab Deployment

Uncomment Traefik labels and network block in `docker-compose.yml`. Access all services through Traefik.
