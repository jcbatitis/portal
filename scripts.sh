#!/bin/sh
set -e

case "$1" in
  up)
    echo "Building and starting services..."
    docker compose up --build -d
    echo "Services are running. Backend: http://localhost:${PORT:-3000}"
    ;;
  down)
    echo "Stopping services..."
    docker compose down
    ;;
  reset)
    echo "Resetting everything (destroying data)..."
    docker compose down -v
    docker compose build --no-cache
    docker compose up -d
    echo "Fresh start complete. Backend: http://localhost:${PORT:-3000}"
    ;;
  build)
    echo "Rebuilding images..."
    docker compose build --no-cache
    ;;
  logs)
    docker compose logs -f
    ;;
  db:shell)
    docker compose exec db psql -U "${POSTGRES_USER:-portal}" -d "${POSTGRES_DB:-portal}"
    ;;
  *)
    echo "Usage: ./scripts.sh {up|down|reset|build|logs|db:shell}"
    exit 1
    ;;
esac
