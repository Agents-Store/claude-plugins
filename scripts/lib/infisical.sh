#!/usr/bin/env bash
# scripts/lib/infisical.sh — shared helpers for the secrets pull/push/audit scripts.
#
# Sourced, never executed. Provides:
#   inf_domain          resolve the Infisical instance URL
#   inf_project         resolve the Infisical project (workspace) id
#   inf_default_env     resolve the default environment slug
#   inf_require_cli     abort unless the Infisical CLI is installed
#   inf_identity_file   resolve the machine-identity credentials file (may be empty)
#   inf_ensure_login    authenticate: machine identity if available, else user login
#   inf_fetch           fetch one environment as JSON into a file (fails loudly)
#
# Auth order:
#   1. A machine identity at $INFISICAL_IDENTITY_FILE (default: one file per
#      project under /etc/infisical/, the server-wide convention, holding
#      INFISICAL_UNIVERSAL_AUTH_CLIENT_ID / _CLIENT_SECRET). We
#      exchange those for a short-lived token and pass it explicitly on every call.
#      This is non-interactive and immune to the active-instance problem below.
#   2. Otherwise the interactive user session, which needs the dance described next.
#
# Why the active-instance dance: the Infisical CLI keeps a separate login per
# self-hosted instance but only ONE is "active" at a time, and `infisical secrets`
# always reads the active one — `--domain` does not switch it for authenticated
# reads. So we compare and, if needed, `infisical login --domain=...`.

# The instance URL is deployment data and is deliberately NOT committed. It is
# resolved at run time: INFISICAL_DOMAIN in the environment, then the machine-
# identity file, then the gitignored .env, and finally the vendor's hosted
# service. Set it once in whichever of those you already keep out of git.
INFISICAL_DEFAULT_DOMAIN="https://app.infisical.com"
INFISICAL_CONFIG_FILE="$HOME/.infisical/infisical-config.json"
INFISICAL_DEFAULT_IDENTITY="/etc/infisical/${INFISICAL_PROJECT_SLUG:-claude-plugins}.env"

# Repo root = parent of the directory holding this library's parent (scripts/lib -> repo).
inf_repo_root() {
  cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd
}

# Instance URL. Override with INFISICAL_DOMAIN=https://... for a one-off run.
# Ladder: environment > machine-identity file > gitignored .env > vendor default.
inf_read_domain_from() {
  [ -r "$1" ] || return 0
  sed -n 's/^[[:space:]]*INFISICAL_DOMAIN[[:space:]]*=[[:space:]]*//p' "$1" \
    | tail -n1 | tr -d '"' | tr -d "'" | tr -d '\r'
}

inf_domain() {
  local d="${INFISICAL_DOMAIN:-}"
  local id_file
  if [ -z "$d" ]; then
    id_file="$(inf_identity_file)"
    [ -n "$id_file" ] && d="$(inf_read_domain_from "$id_file")"
  fi
  [ -z "$d" ] && d="$(inf_read_domain_from "$(inf_repo_root)/.env")"
  d="${d:-$INFISICAL_DEFAULT_DOMAIN}"
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

# Machine-identity credentials file. Override with INFISICAL_IDENTITY_FILE=...
# (set it to "" to force the interactive user path). Empty output = none usable.
inf_identity_file() {
  local f="${INFISICAL_IDENTITY_FILE-$INFISICAL_DEFAULT_IDENTITY}"
  [ -n "$f" ] && [ -r "$f" ] && printf '%s' "$f"
}

# Exchange the universal-auth credentials for a short-lived token, into
# INFISICAL_TOKEN. Returns non-zero (quietly) so callers can fall back.
#
# The credentials are sourced into the environment rather than passed as flags:
# the CLI reads INFISICAL_UNIVERSAL_AUTH_CLIENT_ID / _CLIENT_SECRET itself, which
# keeps the secret out of argv and therefore out of `ps`. The secret is unset
# again as soon as the token is in hand so it is not inherited by child processes.
#
# NOTE: capture stdout ONLY. The CLI writes its update-check banner to stderr, so
# a `2>&1` here silently concatenates that banner onto the JWT and every later
# call fails with an unhelpful "denied".
inf_login_machine() {
  local domain="$1" file token
  file="$(inf_identity_file)" || return 1
  [ -n "$file" ] || return 1

  set -a
  # shellcheck disable=SC1090
  . "$file" || { set +a; return 1; }
  set +a

  if [ -z "${INFISICAL_UNIVERSAL_AUTH_CLIENT_ID:-}" ] || \
     [ -z "${INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET:-}" ]; then
    unset INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET
    echo "Identity file '$file' has no CLIENT_ID/CLIENT_SECRET — ignoring it." >&2
    return 1
  fi

  token=$(infisical login --method=universal-auth --domain="$domain" --plain --silent 2>/dev/null)
  unset INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET

  if [ -z "$token" ]; then
    echo "Machine-identity login failed against '$domain' (file: $file)." >&2
    return 1
  fi

  export INFISICAL_TOKEN="$token"
}

# Authenticate. Prefers the machine identity; falls back to the interactive user
# session, switching the active instance to our domain when needed.
inf_ensure_login() {
  local domain="$1" active

  if [ -n "$(inf_identity_file)" ]; then
    if inf_login_machine "$domain"; then
      return 0
    fi
    echo "Falling back to the interactive user session." >&2
    echo "" >&2
  fi

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
  [ -n "${INFISICAL_TOKEN:-}" ] && args+=(--token="$INFISICAL_TOKEN")

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
  local ident; ident="$(inf_identity_file)"
  if [ -n "$ident" ]; then
    echo "Auth:     machine identity ($ident)"
  else
    echo "Auth:     interactive user session"
  fi
}
