import fastify, { type FastifyInstance } from 'fastify';
import fastifyEnv from '@fastify/env';
import { envSchema } from './config.js';
import dbPlugin from './plugins/db.js';
import sessionPlugin from './plugins/session.js';
import rateLimitPlugin from './plugins/rate-limit.js';
import healthRoutes from './routes/health.js';
import authRoutes from './routes/auth.js';

export async function buildApp(app?: FastifyInstance) {
  const instance = app ?? fastify({ logger: true });

  await instance.register(fastifyEnv, { schema: envSchema, dotenv: true });
  await instance.register(dbPlugin);
  await instance.register(sessionPlugin);
  await instance.register(rateLimitPlugin);
  await instance.register(healthRoutes);
  await instance.register(authRoutes);

  return instance;
}
