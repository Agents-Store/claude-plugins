---
name: cli-recipes
description: This skill should be used when the user asks about "payload migrate", "payload generate:types", "payload generate:importmap", "payload migrate:create", "payload migrate:down", "payload migrate:reset", "payload migrate:refresh", "payload migrate:status", "Payload CLI commands", or needs to run the Payload command-line tool for schema migrations or codegen.
---

# PayloadCMS — CLI Recipes

The `payload` CLI ships as a binary in the `payload` npm package. Run it via the project's package manager so it picks up your `payload.config.ts`:

```bash
pnpm payload <command>
# or
npx payload <command>
```

The scaffolder wires the most-used commands into `package.json` scripts:
```json
{
  "scripts": {
    "generate:types":      "payload generate:types",
    "generate:importmap":  "payload generate:importmap",
    "migrate":             "payload migrate",
    "migrate:create":      "payload migrate:create",
    "migrate:down":        "payload migrate:down",
    "migrate:refresh":     "payload migrate:refresh",
    "migrate:reset":       "payload migrate:reset",
    "migrate:status":      "payload migrate:status"
  }
}
```

## Code Generation

### `generate:types`

Regenerates `src/payload-types.ts` from your collections, globals, and locales. Run after any schema change:
```bash
pnpm generate:types
```

Output path comes from `payload.config.ts`:
```ts
typescript: {
  outputFile: path.resolve(dirname, 'payload-types.ts'),
  declare: false,                  // Skip `declare module 'payload'` block
}
```

Commit `payload-types.ts` — your app code imports from it.

### `generate:importmap`

Builds `src/app/(payload)/admin/importMap.js` from string-path component references in your config. Required after adding any:
- Custom field component
- Custom view
- Custom admin component (`beforeDashboard`, etc.)
- Plugin that registers components

```bash
pnpm generate:importmap
```

If the admin panel says "Could not resolve component X" — you forgot to run this. Commit `importMap.js`.

### `generate:graphql-schema`

Writes the GraphQL schema to a file (useful for `graphql-codegen`):
```bash
pnpm payload generate:graphql-schema
```

## Migrations

Migrations are SQL/Mongo scripts checked into `src/migrations/`. **Required** for Postgres/SQLite in production — `db.push` is dev-only.

### `migrate:create`

Generate a new migration from your current code vs DB state:
```bash
pnpm migrate:create add-tags-collection
```

Writes two files:
- `src/migrations/<timestamp>_add-tags-collection.ts`
- `src/migrations/<timestamp>_add-tags-collection.json` (snapshot)

The generated file contains `up` and `down` functions. Inspect — and edit when needed — before committing.

### `migrate`

Apply all pending migrations:
```bash
pnpm migrate
```

Run on deploy, before starting the app. Recommended deploy script:
```bash
pnpm migrate && pnpm build && pnpm start
```

### `migrate:status`

List which migrations are pending vs. applied:
```bash
pnpm migrate:status
```

### `migrate:down`

Roll back the most recently applied migration:
```bash
pnpm migrate:down
```

Useful when a deploy goes wrong. Each migration's `down` function must reverse the `up` function. Always test rollback in staging before production.

### `migrate:refresh`

Roll back ALL applied migrations, then re-apply them. Destructive in production — typically only for dev resets:
```bash
pnpm migrate:refresh
```

### `migrate:reset`

Roll back ALL applied migrations (without re-applying). Even more destructive:
```bash
pnpm migrate:reset
```

### `migrate:fresh`

Drop the entire DB and rerun migrations. **NEVER in prod**:
```bash
pnpm migrate:fresh
```

## Workflow Cheat Sheets

### Adding a field

```bash
# 1. Edit src/collections/Posts.ts to add the field
# 2. Regenerate types so app code compiles
pnpm generate:types
# 3. Create a migration capturing the schema delta
pnpm migrate:create add-posts-published-at
# 4. Inspect the generated migration, commit
git add src/migrations/ src/collections/Posts.ts src/payload-types.ts
git commit -m "feat(posts): add publishedAt"
# 5. In CI / on prod boot:
pnpm migrate
```

### Adding a custom admin component

```bash
# 1. Add the component file, e.g. src/components/CustomField.tsx
# 2. Reference it by string path in payload.config.ts
# 3. Rebuild the import map
pnpm generate:importmap
git add src/app/\(payload\)/admin/importMap.js src/components/CustomField.tsx
git commit -m "feat(admin): custom field component"
```

### Bootstrapping a new dev machine

```bash
pnpm install
cp .env.example .env             # Then edit
pnpm migrate                      # Apply existing migrations
pnpm generate:importmap           # If components changed since last commit
pnpm dev
```

### Fixing a broken migration

```bash
# Migration partially applied, blocked further deploys
pnpm migrate:status               # See which one is stuck
pnpm migrate:down                 # Roll back the bad one
# Edit src/migrations/<broken>.ts to fix
pnpm migrate                      # Reapply
```

## CI Integration

GitHub Actions:
```yaml
- name: Run migrations
  run: pnpm migrate
  env:
    DATABASE_URI: ${{ secrets.DATABASE_URI }}
    PAYLOAD_SECRET: ${{ secrets.PAYLOAD_SECRET }}

- name: Generate types
  run: pnpm generate:types

- name: Verify import map is fresh
  run: pnpm generate:importmap && git diff --exit-code src/app/\(payload\)/admin/importMap.js
```

The last step catches forgotten `generate:importmap` runs at PR time.

## Custom CLI Scripts via Local API

Need to do a one-off task (data backfill, audit, export)? Write a script in `scripts/`:

```ts
// scripts/backfill-slugs.ts
import { getPayload } from 'payload'
import config from '../src/payload.config'
import slugify from 'slugify'

async function run() {
  const payload = await getPayload({ config })
  const { docs } = await payload.find({
    collection: 'posts',
    where: { slug: { exists: false } },
    limit: 10000,
  })
  for (const doc of docs) {
    await payload.update({
      collection: 'posts',
      id: doc.id,
      data: { slug: slugify(doc.title, { lower: true, strict: true }) },
    })
    console.log('Slugged', doc.id)
  }
  process.exit(0)
}

run().catch((err) => {
  console.error(err)
  process.exit(1)
})
```

Run it:
```bash
pnpm tsx scripts/backfill-slugs.ts
```

Add as a package script when reusable. Use this pattern for any "do X to every document" job that doesn't deserve a migration.

## Notes

- The CLI loads `payload.config.ts` via your project's TypeScript runner — make sure `tsx` (or your loader) is available.
- Migration files are TypeScript by default. Compile-time errors stop the migration.
- On Postgres, `migrate` runs in a transaction per migration. SQLite has the same behavior with `transactionOptions`.
- MongoDB migrations are schemaless transformations — write your own data normalization in `up`/`down`.

## See Also

- The `adapters` skill — `push` vs migrations decision.
- The `setup` skill — scaffolder-installed scripts.
- The `troubleshoot` skill — common migration errors.
