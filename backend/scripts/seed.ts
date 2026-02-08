import 'dotenv/config';
import { Pool } from 'pg';
import { drizzle } from 'drizzle-orm/node-postgres';
import bcrypt from 'bcrypt';
import { users } from '../src/db/schema.js';

const SEED_USERS = [
  { username: 'admin', password: 'admin123' },
];

async function seed() {
  const connectionString = process.env.DATABASE_URL ?? 'postgres://localhost:5432/portal';
  const pool = new Pool({ connectionString });
  const db = drizzle({ client: pool });

  for (const { username, password } of SEED_USERS) {
    const passwordHash = await bcrypt.hash(password, 10);
    await db
      .insert(users)
      .values({ username, passwordHash })
      .onConflictDoNothing({ target: users.username });

    console.log(`Seeded user: ${username}`);
  }

  await pool.end();
  console.log('Seed complete.');
}

seed().catch((err) => {
  console.error('Seed failed:', err);
  process.exit(1);
});
