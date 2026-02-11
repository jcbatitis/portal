# ── Stage 1: Dependencies ────────────────────────────────────────────
FROM node:22-alpine AS deps

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install

# ── Stage 2: Development (hot reload) ───────────────────────────────
FROM deps AS dev

WORKDIR /app
COPY . .
CMD ["npx", "vite", "--host", "0.0.0.0"]

# ── Stage 3: Production build ───────────────────────────────────────
FROM deps AS build

WORKDIR /app
COPY . .
RUN npm run build

# ── Stage 4: Production run ─────────────────────────────────────────
FROM nginx:alpine AS prod

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
