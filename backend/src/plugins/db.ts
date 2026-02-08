import fp from 'fastify-plugin';
import { type FastifyInstance } from 'fastify';
import { createDb, type Database } from '../db/index.js';

declare module 'fastify' {
  interface FastifyInstance {
    db: Database;
  }
}

export default fp(async (fastify: FastifyInstance) => {
  const { db, pool } = createDb(fastify.config.DATABASE_URL);

  fastify.decorate('db', db);

  fastify.addHook('onClose', async () => {
    await pool.end();
  });
});
