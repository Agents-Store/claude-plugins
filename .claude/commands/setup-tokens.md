---
description: Pull secrets from Infisical into .env and settings.local.json
allowed-tools: Bash, Read
---

Run the secrets setup script. Argument: $ARGUMENTS

## Defaults

If no arguments provided, run with defaults:

```bash
./scripts/setup.sh dev .env .claude/settings.local.json
```

**Before running with defaults, inform the user:**

> Running `setup.sh` with default parameters:
> - Environment: `dev`
> - Env file: `.env`
> - Settings file: `.claude/settings.local.json`
>
> To customize, run: `/setup-tokens <environment> <env-file> <settings-file>`
> Examples:
> - `/setup-tokens staging` — staging env, default file paths
> - `/setup-tokens prod .env.production .claude/settings.local.json` — production env with custom env file
> - `/setup-tokens dev "" .claude/settings.local.json` — skip writing .env, only update settings

Then execute the script.

## With Arguments

Parse `$ARGUMENTS` as: `<environment> [env-file] [settings-file]`

- First arg: environment (`dev`, `staging`, `prod`) — required if any args given
- Second arg: env file path (default: `.env`). Pass `""` to skip writing the env file.
- Third arg: settings file path (default: `.claude/settings.local.json`). Pass `""` to skip updating settings.

Run `./scripts/setup.sh <environment> <env-file> <settings-file>`.

## Prerequisites

Before running, check:
1. `scripts/setup.sh` exists and is executable
2. If not executable, run `chmod +x scripts/setup.sh`

## After Running

Report the result to the user (success or failure with error details).
