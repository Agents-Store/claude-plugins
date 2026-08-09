#!/usr/bin/env bash
# scripts/secrets-audit.sh — read-only drift report across the four places a key
# has to exist for this monorepo to work:
#
#   .env                          shell tooling the plugins invoke (nb, docker, …)
#   .claude/settings.local.json   the env block Claude Code expands ${VAR} from
#   Infisical                     the source of truth
#   .env.example                  the documented catalogue (committed)
#
# …checked against what the repo actually needs: every ${VAR} in the root
# .mcp.json and in every plugins/*/.mcp.json.
#
# Compares KEY NAMES and value *kind* (real vs placeholder) — never prints a value.
#
# Usage:
#   ./scripts/secrets-audit.sh              # audit the default environment
#   ./scripts/secrets-audit.sh prod
#   ./scripts/secrets-audit.sh --offline    # skip Infisical, audit local files only
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=lib/infisical.sh
source "$ROOT/scripts/lib/infisical.sh"
PY="$ROOT/scripts/lib/envsync.py"

OFFLINE=0
ENV_FILE=".env"
POSITIONAL=()
while [ $# -gt 0 ]; do
  case "$1" in
    --offline)    OFFLINE=1 ;;
    --env-file)   ENV_FILE="$2"; shift ;;
    --env-file=*) ENV_FILE="${1#--env-file=}" ;;
    -h|--help)
      sed -n '2,21p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    --*) echo "Unknown flag: $1" >&2; exit 1 ;;
    *) POSITIONAL+=("$1") ;;
  esac
  shift
done

cd "$ROOT" || exit 1
ENV_NAME="${POSITIONAL[0]:-$(inf_default_env)}"

JSON=""
if [ "$OFFLINE" = 0 ]; then
  inf_require_cli || exit 1
  inf_ensure_login "$(inf_domain)" || exit 1
  JSON=$(mktemp "${TMPDIR:-/tmp}/infisical_json_XXXXXX")
  trap 'rm -f "$JSON"' EXIT
  if ! inf_fetch "$ENV_NAME" "$JSON"; then
    echo "Continuing offline (Infisical section will be empty)." >&2
    JSON=""
  fi
fi

ARGS=(audit --env-file "$ENV_FILE" --example .env.example
      --settings .claude/settings.local.json --root .)
[ -n "$JSON" ] && ARGS+=(--json "$JSON")

echo "Infisical instance: $(inf_domain)  |  project: $(inf_project)  |  env: $ENV_NAME"
echo ""
python3 "$PY" "${ARGS[@]}"
