import { type FastifyInstance } from 'fastify';

export default async function healthRoutes(fastify: FastifyInstance) {
  fastify.get('/health', async () => {
    return { status: 'ok' };
  });

  fastify.get('/health/db', async () => {
    try {
      await fastify.db.execute('select 1');
      return { status: 'ok', db: 'connected' };
    } catch (err) {
      fastify.log.error(err, 'Database health check failed');
      return { status: 'error', db: 'disconnected' };
    }
  });
}
