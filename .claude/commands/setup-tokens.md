---
description: Pull secrets from Infisical into .env and settings.local.json
argument-hint: [env] [env-file] [settings-file] [--force] [--dry-run]
allowed-tools: Bash, Read
---

Pull secrets down from Infisical. Arguments: $ARGUMENTS

Runs `./scripts/secrets-pull.sh`, which writes **both** targets from a single fetch:

- `.env` — for the shell tooling plugins invoke (`nb`, `gws`, `docker compose`, curl recipes)
- `.claude/settings.local.json` — the `env` block Claude Code expands `${VAR}` in `.mcp.json` from

Instance `https://k.macstack.ai`, project `claude-plugins`
(`5374e01e-dd78-494c-a589-b29c5dd431bf`, pinned in `.infisical.json`).

## Defaults

With no arguments:

```bash
./scripts/secrets-pull.sh
```

That is environment `dev` (from `.infisical.json`), `.env`, `.claude/settings.local.json`.

## With arguments

Positional: `<environment> [env-file] [settings-file]`, plus flags.

- environment — `dev` | `staging` | `prod` (all three are kept identical in this project)
- env-file — default `.env`; pass `""` to skip writing it
- settings-file — default `.claude/settings.local.json`; pass `""` to skip it
- `--dry-run` — print the plan, write nothing
- `--force` — allow a placeholder from Infisical to overwrite a real local value

Examples:

```bash
./scripts/secrets-pull.sh prod                    # a different environment
./scripts/secrets-pull.sh dev .env ""             # only .env
./scripts/secrets-pull.sh --dry-run               # what would change
```

## Guard rails to explain if they fire

- **Exit 3 / "BLOCKED"** — a real local value would be replaced by a placeholder from
  Infisical. Nothing was written. Either push the local values up first
  (`./scripts/secrets-push.sh --yes`) or re-run with `--force`.
- A failed or empty fetch never touches the files; the previous `.env` is kept as `.env.bak`.

## After running

1. Report what changed (count of keys, any blocked/downgraded values).
2. Remind the user to **restart Claude Code** — the `env` block is read at startup, so
   new MCP servers stay unavailable until then.
3. If MCP servers still fail, run `/secrets-audit` to see which variable is unset.

Related: `/secrets-push` (the reverse), `/secrets-audit` (drift report).
