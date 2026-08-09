---
description: Read-only drift report — .env vs Infisical vs .mcp.json vs settings.local.json
argument-hint: [env] [--offline]
allowed-tools: Bash, Read
---

Audit secret drift. Arguments: $ARGUMENTS

Runs `./scripts/secrets-audit.sh`. Read-only: it compares key names and value *kind*
(real vs placeholder) and never prints a secret value.

```bash
./scripts/secrets-audit.sh              # default environment (dev)
./scripts/secrets-audit.sh prod
./scripts/secrets-audit.sh --offline    # local files only, no Infisical call
```

## What the four sections mean

1. **MCP requirements not satisfied** — a `${VAR}` in the root `.mcp.json` or in a
   `plugins/*/.mcp.json` has no real value in `.env`. That MCP server will not start.
   `[ROOT]` entries break the shared project config; `[plugin]` ones only affect that plugin.
2. **Local `.env` vs Infisical** — each row ends in a verdict: `push` (local value is real,
   remote is a placeholder), `pull` (the reverse), or `review` (both real but different —
   decide by hand, do not guess).
3. **Catalogue coverage** — `.env.example` is the committed, documented key list. Keys used
   but undocumented belong in it; keys documented but absent from `.env` are gaps to fill.
4. **Claude Code settings** — the `env` block of `settings.local.json` is what actually
   resolves `${VAR}` at runtime. Missing or stale entries there are why an MCP server fails
   even when `.env` looks right; the fix is `/setup-tokens` plus a Claude Code restart.

Duplicate assignments in `.env` are flagged separately — the last one silently wins.

## Fix order

`./scripts/secrets-push.sh --yes` → `./scripts/secrets-pull.sh` → restart Claude Code.

Report the findings grouped as above, and name the single next command to run.
