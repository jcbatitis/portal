import fp from 'fastify-plugin';
import { type FastifyInstance } from 'fastify';
import { type Pool } from 'pg';
import { createDb, type Database } from '../db/index.js';

declare module 'fastify' {
  interface FastifyInstance {
    db: Database;
    pgPool: Pool;
  }
}

export default fp(async (fastify: FastifyInstance) => {
  const { db, pool } = createDb(fastify.config.DATABASE_URL);

  fastify.decorate('db', db);
  fastify.decorate('pgPool', pool);

  fastify.addHook('onClose', async () => {
    await pool.end();
  });
});
