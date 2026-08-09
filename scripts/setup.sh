#!/usr/bin/env bash
# scripts/setup.sh — backwards-compatible alias for scripts/secrets-pull.sh.
#
# The pull/push/audit trio lives in:
#   scripts/secrets-pull.sh    Infisical -> .env + .claude/settings.local.json
#   scripts/secrets-push.sh    .env      -> Infisical (dry-run unless --yes)
#   scripts/secrets-audit.sh   read-only drift report
#
# Same argument order as before:  ./scripts/setup.sh <env> [env-file] [settings-file]
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/secrets-pull.sh" "$@"
