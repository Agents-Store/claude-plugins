---
description: Scaffold a fresh PayloadCMS v3 project with create-payload-app, walking through database adapter, template, and package manager choices.
argument-hint: [project-name]
allowed-tools: [Bash, Read, Write, Edit, AskUserQuestion, Skill]
---

# /payloadcms-dev:scaffold

Bootstrap a new PayloadCMS v3 project from zero. Wraps `npx create-payload-app@latest` with the recommended Next.js App Router defaults and walks the user through every decision before running the scaffolder.

## Step 1 — Collect Inputs

Use `AskUserQuestion` to gather (skip any the user already supplied as `$ARGUMENTS`):

1. **Project name** — kebab-case directory name (e.g. `my-cms`). If `$ARGUMENTS` is non-empty, use it as the default.
2. **Database adapter** — options:
   - **PostgreSQL** (recommended for prod) — needs a `DATABASE_URI` connection string.
   - **MongoDB** — needs an `mongodb://` URI, ideally a replica set for transactions.
   - **SQLite** (libSQL) — `file:./payload.db` for local, `libsql://…` + auth token for Turso.
3. **Template** — `blank` (recommended for custom builds) / `website` (marketing site demo) / `ecommerce` (Stripe demo). (The payload repo also has `plugin`, `with-cloudflare-d1`, `with-vercel-*`, and the experimental `blank-tanstack` templates, cloned manually rather than via the prompts.)
4. **Package manager** — pnpm (default) / npm / yarn / bun.

## Step 2 — Verify Prerequisites

Run a Bash check before scaffolding:

```bash
node --version          # Recommended >= 20.9.0 (payload engines allow ^18.20.2 || >=20.9.0)
which pnpm || which npm || which yarn || which bun
```

If Node is below the supported range (`^18.20.2 || >=20.9.0`), tell the user to install LTS Node via `nvm install --lts && nvm use --lts` and stop here. Node 20 LTS+ is the recommended baseline.

## Step 3 — Run the Scaffolder

Construct and run the `create-payload-app` command from the chosen inputs:

```bash
pnpm create payload-app@latest <project-name> \
  --template <blank|website|ecommerce> \
  --db <postgres|mongodb|sqlite> \
  --use-pnpm
```

Substitute `--use-npm` / `--use-yarn` / `--use-bun` as appropriate. Run in the user's current working directory.

## Step 4 — Post-Install Walkthrough

After the scaffolder finishes:

1. **Show generated `.env`** — read it back and explain each var.
2. **Generate `PAYLOAD_SECRET`** if the placeholder is still there:
   ```bash
   openssl rand -hex 32
   ```
   Write it into `.env` with `Edit`.
3. **Confirm `DATABASE_URI`** — prompt the user to fill in their actual connection string. If they're using Postgres and need a local DB, suggest a Docker one-liner:
   ```bash
   docker run --name payload-postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:16
   # → postgres://postgres:postgres@localhost:5432/postgres
   ```
4. **Install dependencies** if `--no-deps` was used:
   ```bash
   cd <project-name> && pnpm install
   ```
5. **Run the dev server**:
   ```bash
   cd <project-name> && pnpm dev
   ```
6. **Tell the user to open `http://localhost:3000/admin`** and create the first admin user.

## Step 5 — Suggest Next Steps

Don't auto-invoke other skills. Tell the user to invoke the relevant ones based on what they want to do next:

- "Design my first content collection" → invoke `collections` skill.
- "Pick the right field types" → invoke `fields` skill.
- "Decide what storage adapter to use for uploads" → invoke `adapters` skill.
- "Wire access control" → invoke `access-control` skill.
- "Browse a complete blog example" → invoke `examples` skill.

## Failure Modes

- **`create-payload-app` errors with EACCES** → suggest `sudo chown -R $(whoami) ~/.npm` and rerun.
- **`Node version too low`** → install Node 20 LTS+ via nvm (engines allow `^18.20.2 || >=20.9.0`).
- **`Cannot find module 'sharp'`** after install → run `pnpm add sharp` inside the project, then retry `pnpm dev`.
- **Database connection refused** → confirm the DB is reachable from the dev machine and the URI matches.

## Notes

- Do not modify `payload.config.ts` automatically — the scaffolder writes a known-good config. Customizations belong in follow-up skill-driven work.
- Do not enable `db.push: false` until the user has migrations in place — for dev, `push: true` is the right default (the scaffolder sets this).
- Do not run `pnpm migrate` on a fresh project — the dev server's auto-push handles dev schema sync.

## $ARGUMENTS

If $ARGUMENTS contains a project name, use it as the default for Step 1 and proceed.
