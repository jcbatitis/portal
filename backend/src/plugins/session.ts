import fp from 'fastify-plugin';
import { type FastifyInstance } from 'fastify';
import cookie from '@fastify/cookie';
import session from '@fastify/session';
import connectPgSimple from 'connect-pg-simple';

declare module 'fastify' {
  interface Session {
    userId: number;
    username: string;
  }
}

const PGStore = connectPgSimple(session as never);

export default fp(async (fastify: FastifyInstance) => {
  await fastify.register(cookie);
  await fastify.register(session, {
    secret: fastify.config.SESSION_SECRET,
    cookie: {
      maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
      secure: fastify.config.NODE_ENV === 'production',
      httpOnly: true,
      sameSite: 'lax',
    },
    saveUninitialized: false,
    store: new PGStore({
      pool: fastify.pgPool,
      tableName: 'session',
      createTableIfMissing: true,
    }),
  });
});
