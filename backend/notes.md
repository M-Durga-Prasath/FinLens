# Prisma + PostgreSQL Setup Cheat Sheet (Prisma 7)

## 1. Install Prisma

```bash
npm install prisma @prisma/client
```

Initialize Prisma:

```bash
npx prisma init
```

This creates:

```
prisma/
    schema.prisma
prisma.config.ts
.env
```

---

# 2. Configure `.env`

Example:

```env
DATABASE_URL="postgresql://postgres:password@localhost:5432/financerag"
```

Connection string format:

```
postgresql://USERNAME:PASSWORD@HOST:PORT/DATABASE
```

Example:

```env
DATABASE_URL="postgresql://postgres:admin123@localhost:5432/postgres"
```

---

# 3. Configure `prisma.config.ts`

```ts
import "dotenv/config";
import { defineConfig } from "prisma/config";

export default defineConfig({
  schema: "prisma/schema.prisma",
  migrations: {
    path: "prisma/migrations",
  },
  datasource: {
    url: process.env.DATABASE_URL,
  },
});
```

---

# 4. Create Your Schema

```prisma
generator client {
  provider = "prisma-client"
  output   = "../generated/prisma"
}

datasource db {
  provider = "postgresql"
}

model User {
  id        String   @id @default(uuid()) @db.Uuid
  email     String   @unique
  name      String?
  createdAt DateTime @default(now())

  @@map("users")
}
```

---

# 5. Create the First Migration

```bash
npx prisma migrate dev --name init
```

Creates:

```
prisma/
└── migrations/
    └── <timestamp>_init/
```

---

# 6. Generate Prisma Client

Normally automatic after migration.

If needed:

```bash
npx prisma generate
```

---

# 7. Open Prisma Studio

```bash
npx prisma studio
```

Opens a web UI to view and edit your database.

---

# Common Commands

## Create a Migration

```bash
npx prisma migrate dev --name migration_name
```

Example:

```bash
npx prisma migrate dev --name add_documents
```

---

## Reset Database (Development Only)

Deletes all data and reapplies every migration.

```bash
npx prisma migrate reset
```

Use when:

- Migrations are broken
- Database schema is inconsistent
- You don't mind losing development data

---

## Generate Prisma Client

```bash
npx prisma generate
```

Use after:

- Updating Prisma
- Changing generator settings
- Changing output path

---

## Pull Existing Database

Reverse engineers an existing database into `schema.prisma`.

```bash
npx prisma db pull
```

---

## Push Schema (Without Migrations)

```bash
npx prisma db push
```

Good for quick prototypes.

Avoid in production.

---

## Validate Schema

```bash
npx prisma validate
```

Checks only the schema syntax.

---

## Format Schema

```bash
npx prisma format
```

Automatically formats `schema.prisma`.

---

# Useful SQL Queries

Current database:

```sql
SELECT current_database();
```

Current schema:

```sql
SELECT current_schema();
```

List all tables:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public';
```

Show all rows:

```sql
SELECT * FROM users;
```

Describe a table (psql):

```sql
\d users
```

---

# Common Errors

## Migration says success but tables aren't visible

✅ Check `DATABASE_URL`.

A wrong `.env` usually means Prisma migrated a different database.

---

## `relation "_prisma_migrations" does not exist`

Prisma is pointing to the wrong database, or migrations have never run there.

---

## `extension "vector" is not available`

Install the `pgvector` extension, or remove:

```prisma
extensions = [vector]
```

until `pgvector` is installed.

---

## `Can't reach database server`

Check:

- PostgreSQL is running.
- Host and port are correct.
- Username/password are correct.
- `DATABASE_URL` is correct.

---

# Typical Development Workflow

```text
Create/Update model
        ↓
npx prisma migrate dev --name <migration_name>
        ↓
Prisma Client generated
        ↓
Use Prisma Client in your application
        ↓
Repeat whenever schema changes
```

---

# Project Structure

```
project/
│
├── prisma/
│   ├── schema.prisma
│   └── migrations/
│
├── prisma.config.ts
├── .env
├── package.json
└── src/
```