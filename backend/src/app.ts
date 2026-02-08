import fastify from 'fastify';
import fastifyEnv from '@fastify/env';
import { envSchema } from './config.js';
import dbPlugin from './plugins/db.js';
import healthRoutes from './routes/health.js';

export async function buildApp() {
  const app = fastify({ logger: true });

  await app.register(fastifyEnv, { schema: envSchema, dotenv: true });
  await app.register(dbPlugin);
  await app.register(healthRoutes);

  return app;
}
