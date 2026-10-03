---
description: Scaffold a fresh PayloadCMS v3 project with create-payload-app, walking through database adapter, template, and package manager choices.
argument-hint: [project-name]
allowed-tools: [Bash, Read, Write, Edit, AskUserQuestion, Skill]
---

# /payloadcms-dev:scaffold

Bootstrap a new PayloadCMS v3 project from zero. Wraps the official `create-payload-app` scaffolder with the recommended Next.js App Router defaults and walks the user through every decision before running it — passing every choice as a flag so the run never stops on an interactive prompt.

## Step 1 — Collect Inputs

Use `AskUserQuestion` to gather (skip any the user already supplied as `$ARGUMENTS`):

1. **Project name** — kebab-case directory name (e.g. `my-cms`). If `$ARGUMENTS` is non-empty, use it as the default.
2. **Database adapter** — options:
   - **PostgreSQL** (recommended for prod) — needs a `DATABASE_URI` connection string.
   - **MongoDB** — needs an `mongodb://` URI, ideally a replica set for transactions.
   - **SQLite** (libSQL) — `file:./payload.db` for local, `libsql://…` + auth token for Turso.
3. **Template** — `blank` (recommended for custom builds) / `website` (marketing site demo) / `ecommerce` (Stripe demo). (The CLI's own template list is `blank`, `website`, `ecommerce`, `with-cloudflare-d1` and `plugin`. The 3.x branch of the payload repo also holds `with-postgres`, `with-vercel-mongodb`, `with-vercel-postgres` and `with-vercel-website`, cloned manually rather than via the prompts; `blank-tanstack` exists only on the `main` branch — the Payload 4 canary — so skip it for production work.)
4. **Package manager** — pnpm (default) / npm / yarn / bun.
5. **Coding-agent skill** — the scaffolder can install the official Payload skill plus a `CLAUDE.md` / `AGENTS.md` for one coding agent (`-a claude|codex|cursor`). This plugin already ships Payload skills, and `-a claude` would add a second, overlapping set under `.claude/skills/payload`, so recommend **None (`--no-agent`)** unless the user explicitly wants the official skill too.

## Step 2 — Verify Prerequisites

Run a Bash check before scaffolding:

```bash
node --version          # Recommend Node 22 or 24 LTS (payload engines allow ^18.20.2 || >=20.9.0; Node 18 and 20 are end-of-life)
which pnpm || which npm || which yarn || which bun
```

If Node is below the supported range (`^18.20.2 || >=20.9.0`), tell the user to install LTS Node via `nvm install --lts && nvm use --lts` and stop here. If it is Node 18 or 20 (both end-of-life — still accepted by the engines field), recommend upgrading to a 22/24 LTS before going to production.

## Step 3 — Run the Scaffolder

Construct and run the `create-payload-app` command from the chosen inputs. Every prompt the scaffolder can ask has a flag, and a missing flag makes a non-interactive run (CI, an agent shell) hang on the prompt — so always pass all of them:

```bash
npx create-payload-app@latest --no-agent --use-pnpm \
  -n <project-name> \
  -t <blank|website|ecommerce> \
  -d <postgres|mongodb|sqlite> \
  --db-accept-recommended
```

- **`--no-agent`** (default, see Step 1) skips the "Select a coding agent to install the Payload skill for" prompt. To install the official Payload skill for one agent instead, replace it with `--agent claude` (or `-a claude`; `codex` and `cursor` are the other values) — `npx create-payload-app@latest --agent claude --use-pnpm …` writes `.claude/skills/payload/` and a `CLAUDE.md`.
- **`--db-accept-recommended`** accepts the local default connection string for the chosen database (skips the "Enter … connection string" prompt); pass `--db-connection-string '<uri>'` instead when the user already has one. Step 4 has the user confirm `DATABASE_URI` either way.
- `-n` / `-t` / `-d` are short for `--name` / `--template` / `--db`. Add `--no-deps` to skip installing dependencies and `--no-git` to skip `git init`.
- Substitute `--use-npm` / `--use-yarn` / `--use-bun` for `--use-pnpm` as appropriate. Run in the user's current working directory.

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

- **Scaffolder sits at "Select a coding agent…" or another prompt** → a flag is missing; rerun with `--no-agent` (or `-a <agent>`), `-t`, `-d` and `--db-accept-recommended` so nothing is asked.
- **`create-payload-app` errors with EACCES** → suggest `sudo chown -R $(whoami) ~/.npm` and rerun.
- **`Node version too low`** → install a 22/24 LTS via nvm (engines allow `^18.20.2 || >=20.9.0`; Node 18 and 20 are end-of-life).
- **`Cannot find module 'sharp'`** after install → run `pnpm add sharp` inside the project, then retry `pnpm dev`.
- **Database connection refused** → confirm the DB is reachable from the dev machine and the URI matches.

## Notes

- Do not modify `payload.config.ts` automatically — the scaffolder writes a known-good config. Customizations belong in follow-up skill-driven work.
- Do not enable `db.push: false` until the user has migrations in place — for dev, `push: true` is the right default (the scaffolder sets this).
- Do not run `pnpm migrate` on a fresh project — the dev server's auto-push handles dev schema sync.

## $ARGUMENTS

If $ARGUMENTS contains a project name, use it as the default for Step 1 and proceed.
