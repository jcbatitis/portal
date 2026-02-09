import { type FastifyInstance } from 'fastify';
import { eq } from 'drizzle-orm';
import { userSettings } from '../db/schema.js';

const SETTINGS_VALIDATORS: Record<
  string,
  { default: string; validate: (v: string) => boolean; errorHint: string }
> = {
  theme: {
    default: 'system',
    validate: (v) => ['light', 'dark', 'system'].includes(v),
    errorHint: 'must be one of light, dark, system',
  },
  display_name: {
    default: '',
    validate: (v) => v.length > 0 && v.length <= 255,
    errorHint: 'must be a non-empty string (max 255 chars)',
  },
};

function buildSettingsObject(rows: { key: string; value: string }[]): Record<string, string> {
  const settings: Record<string, string> = {};
  for (const key of Object.keys(SETTINGS_VALIDATORS)) {
    settings[key] = SETTINGS_VALIDATORS[key].default;
  }
  for (const row of rows) {
    settings[row.key] = row.value;
  }
  return settings;
}

export default async function settingsRoutes(fastify: FastifyInstance) {
  fastify.get('/settings', { preHandler: [fastify.requireAuth] }, async (request) => {
    const userId = request.session.userId!;

    const rows = await fastify.db
      .select({ key: userSettings.key, value: userSettings.value })
      .from(userSettings)
      .where(eq(userSettings.userId, userId));

    return buildSettingsObject(rows);
  });

  fastify.patch<{ Body: Record<string, string> }>(
    '/settings',
    {
      preHandler: [fastify.requireAuth],
      schema: {
        body: {
          type: 'object',
          additionalProperties: { type: 'string' },
        },
      },
    },
    async (request, reply) => {
      const userId = request.session.userId!;
      const updates = request.body;
      const keys = Object.keys(updates);

      if (keys.length === 0) {
        return reply.code(400).send({ error: 'No settings provided' });
      }

      for (const key of keys) {
        if (!(key in SETTINGS_VALIDATORS)) {
          return reply.code(400).send({ error: `Unknown setting: ${key}` });
        }
      }

      for (const [key, value] of Object.entries(updates)) {
        if (!SETTINGS_VALIDATORS[key].validate(value)) {
          return reply
            .code(400)
            .send({ error: `Invalid value for ${key}: ${SETTINGS_VALIDATORS[key].errorHint}` });
        }
      }

      const rows = await fastify.db.transaction(async (tx) => {
        for (const [key, value] of Object.entries(updates)) {
          await tx
            .insert(userSettings)
            .values({ userId, key, value })
            .onConflictDoUpdate({
              target: [userSettings.userId, userSettings.key],
              set: { value, updatedAt: new Date() },
            });
        }

        return tx
          .select({ key: userSettings.key, value: userSettings.value })
          .from(userSettings)
          .where(eq(userSettings.userId, userId));
      });

      return buildSettingsObject(rows);
    },
  );
}
