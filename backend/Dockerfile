# ── Stage 1: Dependencies ────────────────────────────────────────────
FROM node:22-alpine AS deps

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install

# ── Stage 2: Development (hot reload) ───────────────────────────────
FROM deps AS dev

WORKDIR /app
COPY . .
CMD ["npx", "tsx", "watch", "src/index.ts"]

# ── Stage 3: Production build ───────────────────────────────────────
FROM deps AS build

WORKDIR /app
COPY . .
RUN npm run build

# ── Stage 4: Production run ─────────────────────────────────────────
FROM node:22-alpine AS prod

WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY package.json ./
CMD ["node", "dist/index.js"]
