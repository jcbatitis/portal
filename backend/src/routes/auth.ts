import { type FastifyInstance } from 'fastify';
import { eq } from 'drizzle-orm';
import bcrypt from 'bcrypt';
import { users } from '../db/schema.js';

export default async function authRoutes(fastify: FastifyInstance) {
  fastify.post<{ Body: { username: string; password: string } }>(
    '/login',
    {
      schema: {
        body: {
          type: 'object',
          required: ['username', 'password'],
          properties: {
            username: { type: 'string', examples: ['admin'] },
            password: { type: 'string', examples: ['changeme'] },
          },
        },
      },
      config: {
        rateLimit: { max: fastify.config.RATE_LIMIT_LOGIN_MAX, timeWindow: '1 minute' },
      },
    },
    async (request, reply) => {
      const { username, password } = request.body;

      const [user] = await fastify.db
        .select()
        .from(users)
        .where(eq(users.username, username))
        .limit(1);

      if (!user) {
        return reply.code(401).send({ error: 'Invalid credentials' });
      }

      const valid = await bcrypt.compare(password, user.passwordHash);
      if (!valid) {
        return reply.code(401).send({ error: 'Invalid credentials' });
      }

      request.session.userId = user.id;
      request.session.username = user.username;

      return { username: user.username };
    },
  );

  fastify.post('/logout', { preHandler: [fastify.requireAuth] }, async (request) => {
    await request.session.destroy();
    return { status: 'logged out' };
  });

  fastify.get('/me', { preHandler: [fastify.requireAuth] }, async (request) => {
    return {
      userId: request.session.userId,
      username: request.session.username,
    };
  });
}
