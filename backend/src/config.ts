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
  },
} as const;

declare module 'fastify' {
  interface FastifyInstance {
    config: {
      PORT: number;
      HOST: string;
      DATABASE_URL: string;
      NODE_ENV: string;
    };
  }
}
