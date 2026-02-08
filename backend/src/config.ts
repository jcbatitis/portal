export const envSchema = {
  type: 'object',
  required: [],
  properties: {
    PORT: {
      type: 'number',
      default: 3000,
    },
    HOST: {
      type: 'string',
      default: '0.0.0.0',
    },
    DATABASE_URL: {
      type: 'string',
      default: 'postgres://localhost:5432/portal',
    },
    NODE_ENV: {
      type: 'string',
      default: 'development',
    },
    SESSION_SECRET: {
      type: 'string',
      default: 'dev-secret-change-me-in-production!!',
    },
    RATE_LIMIT_MAX: {
      type: 'integer',
      default: 100,
    },
    RATE_LIMIT_LOGIN_MAX: {
      type: 'integer',
      default: 5,
    },
  },
} as const;

declare module 'fastify' {
  interface FastifyInstance {
    config: {
      PORT: number;
      HOST: string;
      DATABASE_URL: string;
      NODE_ENV: string;
      SESSION_SECRET: string;
      RATE_LIMIT_MAX: number;
      RATE_LIMIT_LOGIN_MAX: number;
    };
  }
}
