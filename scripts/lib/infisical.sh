#!/usr/bin/env bash
# scripts/lib/infisical.sh — shared helpers for the secrets pull/push/audit scripts.
#
# Sourced, never executed. Provides:
#   inf_domain          resolve the Infisical instance URL
#   inf_project         resolve the Infisical project (workspace) id
#   inf_default_env     resolve the default environment slug
#   inf_require_cli     abort unless the Infisical CLI is installed
#   inf_ensure_login    make sure the ACTIVE CLI session points at our instance
#   inf_fetch           fetch one environment as JSON into a file (fails loudly)
#
# Why the active-instance dance: the Infisical CLI keeps a separate login per
# self-hosted instance but only ONE is "active" at a time, and `infisical secrets`
# always reads the active one — `--domain` does not switch it for authenticated
# reads. So we compare and, if needed, `infisical login --domain=...`.

INFISICAL_DEFAULT_DOMAIN="https://k.macstack.ai"
INFISICAL_CONFIG_FILE="$HOME/.infisical/infisical-config.json"

# Repo root = parent of the directory holding this library's parent (scripts/lib -> repo).
inf_repo_root() {
  cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd
}

# Instance URL. Override with INFISICAL_DOMAIN=https://... for a one-off run.
inf_domain() {
  local d="${INFISICAL_DOMAIN:-$INFISICAL_DEFAULT_DOMAIN}"
  printf '%s' "${d%/}"
}

# Project (workspace) id: env override > .infisical.json > empty.
# An empty id makes the CLI fall back to .infisical.json in the CWD, which is the
# same value — we pass it explicitly so the scripts work from any directory.
inf_project() {
  if [ -n "${INFISICAL_PROJECT_ID:-}" ]; then
    printf '%s' "$INFISICAL_PROJECT_ID"; return
  fi
  local f; f="$(inf_repo_root)/.infisical.json"
  [ -f "$f" ] || { printf ''; return; }
  sed -n 's/.*"workspaceId"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$f" | head -1
}

# Default environment slug from .infisical.json (falls back to dev).
inf_default_env() {
  local f; f="$(inf_repo_root)/.infisical.json"
  local e=""
  [ -f "$f" ] && e=$(sed -n 's/.*"defaultEnvironment"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$f" | head -1)
  printf '%s' "${e:-dev}"
}

inf_require_cli() {
  command -v infisical >/dev/null 2>&1 && return 0
  echo "Infisical CLI not installed." >&2
  echo "  macOS: brew install infisical/get-cli/infisical" >&2
  return 1
}

# Currently-active instance, normalised (the config stores it with a /api suffix).
inf_active_instance() {
  [ -f "$INFISICAL_CONFIG_FILE" ] || { printf ''; return; }
  local d
  d=$(sed -n 's/.*"LoggedInUserDomain"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$INFISICAL_CONFIG_FILE" 2>/dev/null | head -1)
  d="${d%/}"; d="${d%/api}"; d="${d%/}"
  printf '%s' "$d"
}

# Switch/authenticate so that the active instance is our domain. Interactive when
# no session exists yet.
inf_ensure_login() {
  local domain="$1" active
  active="$(inf_active_instance)"
  [ "$active" = "$domain" ] && return 0

  if [ -n "$active" ]; then
    echo "Active Infisical instance is '$active', this repo uses '$domain'."
    echo "Switching by logging into '$domain'..."
  else
    echo "No active Infisical session. Logging into '$domain'..."
  fi
  echo ""
  if ! infisical login --domain="$domain"; then
    echo ""
    echo "Login failed or cancelled. Run it manually, then retry:" >&2
    echo "  infisical login --domain=$domain" >&2
    return 1
  fi
  echo ""
}

# inf_fetch <env> <out.json> — writes raw JSON. Non-zero exit means nothing usable
# was written, so callers must never touch destination files on failure.
inf_fetch() {
  local env="$1" out="$2" err
  err=$(mktemp "${TMPDIR:-/tmp}/infisical_err_XXXXXX")
  local args=(secrets --env="$env" --domain="$(inf_domain)" -o json --silent)
  local pid; pid="$(inf_project)"
  [ -n "$pid" ] && args+=(--projectId="$pid")

  if ! infisical "${args[@]}" > "$out" 2> "$err"; then
    echo "Failed to fetch secrets for env '$env':" >&2
    grep -vi "new release\|brew\|upgrade\|To update, run" "$err" | sed 's/^/   /' >&2
    rm -f "$err"
    return 1
  fi
  rm -f "$err"
  # A zero exit with an empty body still means "do not overwrite anything".
  [ -s "$out" ] || { echo "Empty response from Infisical for env '$env'." >&2; return 1; }
}

inf_banner() {
  echo "Instance: $(inf_domain)"
  local pid; pid="$(inf_project)"
  echo "Project:  ${pid:-<from .infisical.json in CWD>}"
}
