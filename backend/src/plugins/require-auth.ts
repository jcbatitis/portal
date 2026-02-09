import fp from 'fastify-plugin';
import { type FastifyInstance, type preHandlerHookHandler } from 'fastify';

declare module 'fastify' {
  interface FastifyInstance {
    requireAuth: preHandlerHookHandler;
  }
}

export default fp(async (fastify: FastifyInstance) => {
  const requireAuth: preHandlerHookHandler = async (request, reply) => {
    if (!request.session.userId) {
      return reply.code(401).send({ error: 'Not authenticated' });
    }
  };

  fastify.decorate('requireAuth', requireAuth);
});
