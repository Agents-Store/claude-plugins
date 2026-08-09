#!/usr/bin/env bash
# scripts/secrets-pull.sh — Infisical -> .env + .claude/settings.local.json
#
# Both targets are written from the same fetch, so the shell tooling (.env) and
# Claude Code (the `env` block that resolves ${VAR} in .mcp.json) can never drift
# apart. Values are rendered single-quoted, which keeps $ # & = spaces, base64
# padding, JWT dots and multiline PEM keys intact for `source .env` and dotenv
# loaders alike.
#
# Safety:
#   • a failed or empty fetch never touches the destination files
#   • a pull that would replace a REAL local value with a placeholder stops with
#     exit 3 and tells you to push first (override with --force)
#   • the previous .env is kept as .env.bak
#
# Usage:
#   ./scripts/secrets-pull.sh                                   # dev -> .env + settings
#   ./scripts/secrets-pull.sh prod                              # another environment
#   ./scripts/secrets-pull.sh dev .env ""                       # skip settings
#   ./scripts/secrets-pull.sh dev "" .claude/settings.local.json # skip .env
#   ./scripts/secrets-pull.sh --dry-run                         # show the plan only
#   ./scripts/secrets-pull.sh --force                           # allow downgrades
#
# Override the instance for one run:  INFISICAL_DOMAIN=https://... ./scripts/secrets-pull.sh
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=lib/infisical.sh
source "$ROOT/scripts/lib/infisical.sh"
PY="$ROOT/scripts/lib/envsync.py"

FORCE=0
DRY_RUN=0
POSITIONAL=()
while [ $# -gt 0 ]; do
  case "$1" in
    --force)   FORCE=1 ;;
    --dry-run) DRY_RUN=1 ;;
    -h|--help)
      sed -n '2,26p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    --*) echo "Unknown flag: $1" >&2; exit 1 ;;
    *) POSITIONAL+=("$1") ;;
  esac
  shift
done

ENV_NAME="${POSITIONAL[0]:-$(inf_default_env)}"
ENV_FILE="${POSITIONAL[1]-.env}"
SETTINGS="${POSITIONAL[2]-.claude/settings.local.json}"

cd "$ROOT" || exit 1

echo "Secrets pull"
inf_banner
echo "Environment: $ENV_NAME"
echo "Env file:    ${ENV_FILE:-skipped}"
echo "Settings:    ${SETTINGS:-skipped}"
echo ""

inf_require_cli || exit 1
inf_ensure_login "$(inf_domain)" || exit 1

JSON=$(mktemp "${TMPDIR:-/tmp}/infisical_json_XXXXXX")
trap 'rm -f "$JSON" "$JSON.push"' EXIT

echo "Fetching secrets from Infisical ($ENV_NAME)..."
inf_fetch "$ENV_NAME" "$JSON" || { echo "Aborted — no files were changed."; exit 1; }
echo ""

# -- Plan + downgrade guard (only meaningful when we are writing a .env) -------
if [ -n "$ENV_FILE" ]; then
  PLAN_ARGS=(pull-plan --json "$JSON" --env-file "$ENV_FILE")
  [ "$FORCE" = 1 ] && PLAN_ARGS+=(--force)
  python3 "$PY" "${PLAN_ARGS[@]}"
  rc=$?
  if [ "$rc" = 3 ]; then
    echo ""
    echo "Aborted — no files were changed."
    exit 3
  elif [ "$rc" != 0 ]; then
    exit "$rc"
  fi
  echo ""
fi

if [ "$DRY_RUN" = 1 ]; then
  echo "Dry run — nothing written."
  exit 0
fi

# -- Write ---------------------------------------------------------------------
[ -n "$ENV_FILE" ] && [ -f "$ENV_FILE" ] && cp -p "$ENV_FILE" "$ENV_FILE.bak"
python3 "$PY" render --json "$JSON" --env-file "$ENV_FILE" --settings "$SETTINGS" || exit 1

echo ""
echo "Done. Restart Claude Code so the new env block is picked up."
