import fastify, { type FastifyInstance } from 'fastify';
import fastifyEnv from '@fastify/env';
import { envSchema } from './config.js';
import dbPlugin from './plugins/db.js';
import healthRoutes from './routes/health.js';

export async function buildApp(app?: FastifyInstance) {
  const instance = app ?? fastify({ logger: true });

  await instance.register(fastifyEnv, { schema: envSchema, dotenv: true });
  await instance.register(dbPlugin);
  await instance.register(healthRoutes);

  return instance;
}
