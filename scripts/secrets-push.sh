#!/usr/bin/env bash
# scripts/secrets-push.sh — .env -> Infisical (the reverse of secrets-pull.sh)
#
# DRY-RUN by default: it prints the plan and writes nothing. Pass --yes to apply.
# `infisical secrets set` is an UPSERT — it creates and updates, never deletes, so
# keys that exist only in Infisical are left alone.
#
# Safety:
#   • a key whose remote value is REAL and whose local value is a placeholder is
#     SKIPPED (a stale local template must not wipe a live credential). --force
#     pushes those too.
#   • secrets are handed to the CLI through a mode-600 temp file, never as argv,
#     so they do not show up in `ps`.
#
# Usage:
#   ./scripts/secrets-push.sh                       # dry-run against the default env
#   ./scripts/secrets-push.sh --yes                 # apply
#   ./scripts/secrets-push.sh prod --yes            # a specific environment
#   ./scripts/secrets-push.sh --all-envs --yes      # dev + staging + prod (they are
#                                                   # kept identical in this project)
#   ./scripts/secrets-push.sh --only DOKPLOY_URL,DOKPLOY_API_KEY --yes
#   ./scripts/secrets-push.sh --env-file .env.local --yes
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=lib/infisical.sh
source "$ROOT/scripts/lib/infisical.sh"
PY="$ROOT/scripts/lib/envsync.py"

APPLY=0
FORCE=0
ALL_ENVS=0
ONLY=""
ENV_FILE=".env"
POSITIONAL=()
while [ $# -gt 0 ]; do
  case "$1" in
    --yes|--apply) APPLY=1 ;;
    --force)       FORCE=1 ;;
    --all-envs)    ALL_ENVS=1 ;;
    --only)        ONLY="$2"; shift ;;
    --only=*)      ONLY="${1#--only=}" ;;
    --env-file)    ENV_FILE="$2"; shift ;;
    --env-file=*)  ENV_FILE="${1#--env-file=}" ;;
    -h|--help)
      sed -n '2,26p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    --*) echo "Unknown flag: $1" >&2; exit 1 ;;
    *) POSITIONAL+=("$1") ;;
  esac
  shift
done

cd "$ROOT" || exit 1

if [ "$ALL_ENVS" = 1 ]; then
  ENVS=(dev staging prod)
else
  ENVS=("${POSITIONAL[0]:-$(inf_default_env)}")
fi

[ -f "$ENV_FILE" ] || { echo "No $ENV_FILE — run ./scripts/secrets-pull.sh first." >&2; exit 1; }

echo "Secrets push"
inf_banner
echo "Source:      $ENV_FILE"
echo "Environment: ${ENVS[*]}"
if [ "$APPLY" = 1 ]; then
  echo "Mode:        APPLY (writing to Infisical)"
else
  echo "Mode:        DRY-RUN (nothing written — pass --yes to apply)"
fi
echo ""

inf_require_cli || exit 1
inf_ensure_login "$(inf_domain)" || exit 1

PROJECT_ID="$(inf_project)"
DOMAIN="$(inf_domain)"
JSON=$(mktemp "${TMPDIR:-/tmp}/infisical_json_XXXXXX")
UPLOAD=$(mktemp "${TMPDIR:-/tmp}/infisical_push_XXXXXX")
chmod 600 "$UPLOAD"
trap 'rm -f "$JSON" "$UPLOAD"' EXIT

status=0
for ENV_NAME in "${ENVS[@]}"; do
  echo "──────── $ENV_NAME ────────"
  if ! inf_fetch "$ENV_NAME" "$JSON"; then
    echo "Skipping '$ENV_NAME' — could not read its current state."
    status=1
    continue
  fi

  PLAN_ARGS=(push-plan --json "$JSON" --env-file "$ENV_FILE" --out "$UPLOAD")
  [ "$FORCE" = 1 ] && PLAN_ARGS+=(--force)
  [ -n "$ONLY" ] && PLAN_ARGS+=(--only "$ONLY")
  python3 "$PY" "${PLAN_ARGS[@]}"
  rc=$?
  if [ "$rc" = 4 ]; then
    echo "   nothing to do"
    echo ""
    continue
  elif [ "$rc" != 0 ]; then
    status=$rc
    echo ""
    continue
  fi

  if [ "$APPLY" = 1 ]; then
    SET_ARGS=(secrets set --file "$UPLOAD" --env="$ENV_NAME" --domain="$DOMAIN" --silent)
    [ -n "$PROJECT_ID" ] && SET_ARGS+=(--projectId="$PROJECT_ID")
    if infisical "${SET_ARGS[@]}" >/dev/null; then
      echo "   ✓ written to Infisical ($ENV_NAME)"
    else
      echo "   ✗ write FAILED for $ENV_NAME" >&2
      status=1
    fi
  else
    echo "   (dry-run — pass --yes to write)"
  fi
  echo ""
done

if [ "$APPLY" = 1 ] && [ "$status" = 0 ]; then
  echo "Done. Re-run ./scripts/secrets-pull.sh to bring .env back in lockstep."
fi
exit "$status"
