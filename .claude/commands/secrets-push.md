---
description: Push local .env values back up to Infisical (dry-run unless --yes)
argument-hint: [env] [--yes] [--all-envs] [--only KEY,KEY] [--force]
allowed-tools: Bash, Read
---

Push locally-edited secrets back into Infisical. Arguments: $ARGUMENTS

Runs `./scripts/secrets-push.sh` — the reverse of `/setup-tokens`. Infisical is the
source of truth, so anything added or fixed in `.env` has to go up or the next pull
throws it away.

Project `claude-plugins`. The instance URL comes from `INFISICAL_DOMAIN` (environment, machine-identity file, or the gitignored `.env`) — it is not committed.

## Always dry-run first

```bash
./scripts/secrets-push.sh            # prints the plan, writes nothing
./scripts/secrets-push.sh --yes      # applies it
```

Show the user the plan (NEW / UPDATE / SKIPPED counts) and confirm before adding `--yes`,
unless they already asked for the write in this turn.

## Flags

- `--all-envs` — write to `dev`, `staging` and `prod`. This project keeps the three
  identical, so prefer this over pushing to one and letting them drift.
- `--only KEY,KEY` — push just these keys.
- `--env-file .env.local` — a source other than `.env`.
- `--force` — also push keys whose local value is a placeholder over a real remote value.

## Semantics worth stating in the report

- `infisical secrets set` is an **upsert**: keys only present in Infisical are untouched.
  Deleting a key from `.env` does **not** delete it remotely — do that explicitly.
- Keys whose local value is a placeholder (`replace-me`, `your-…example.com`, empty) and
  whose remote value is real are **skipped by default**, so a stale template never wipes a
  live credential.
- Secrets reach the CLI through a mode-600 temp file, never argv — they do not appear in `ps`.

## After running

Re-run `./scripts/secrets-pull.sh` so `.env` and `.claude/settings.local.json` match what
Infisical now holds, then report the result.

Related: `/setup-tokens` (pull), `/secrets-audit` (drift report).
