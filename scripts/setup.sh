#!/bin/bash
# scripts/setup.sh
# Pulls secrets from Infisical and writes .env + .claude/settings.local.json
#
# Usage:
#   ./scripts/setup.sh dev .env .claude/settings.local.json
#   ./scripts/setup.sh staging .env
#   ./scripts/setup.sh prod "" .claude/settings.local.json

DOMAIN="https://k.macstack.ai"
ENV="${1:-dev}"
ENV_FILE="$2"
SETTINGS="$3"

echo "Setup"
echo "Environment: $ENV"
echo "Env file:    ${ENV_FILE:-skipped}"
echo "Settings:    ${SETTINGS:-skipped}"
echo ""

# -- Check Infisical CLI -------------------------------------------------
if ! command -v infisical &> /dev/null; then
  echo "Infisical CLI not installed"
  echo "  macOS: brew install infisical/get-cli/infisical"
  exit 1
fi

# -- Fetch secrets -> temp file -------------------------------------------
echo "Fetching secrets from Infisical..."

TEMP_ENV=$(mktemp /tmp/infisical_env_XXXXXX)

infisical secrets \
  --domain="$DOMAIN" \
  --env="$ENV" \
  -o dotenv > "$TEMP_ENV"

echo "Secrets fetched: $(wc -l < "$TEMP_ENV") variables"
echo ""

# -- Write .env -----------------------------------------------------------
if [ -n "$ENV_FILE" ]; then
  cp "$TEMP_ENV" "$ENV_FILE"
  echo "$ENV_FILE written"
fi

# -- Write settings.local.json -------------------------------------------
if [ -n "$SETTINGS" ]; then
  mkdir -p "$(dirname "$SETTINGS")"

  TEMP_PY=$(mktemp /tmp/infisical_py_XXXXXX.py)

  cat > "$TEMP_PY" << 'PYEOF'
import json, os, sys

env_file      = sys.argv[1]
settings_path = sys.argv[2]

# Parse .env file
secrets = {}
with open(env_file, 'r') as f:
  for line in f:
    line = line.strip()
    if not line or line.startswith('#'):
      continue
    if '=' not in line:
      continue
    k, v = line.split('=', 1)
    secrets[k.strip()] = v.strip()

print(f"   Parsed {len(secrets)} secrets")

# Read existing settings.local.json
existing = {}
if os.path.exists(settings_path):
  with open(settings_path, 'r') as f:
    content = f.read().strip()
    if content:
      existing = json.loads(content)

# Update ONLY env section
existing['env'] = {**existing.get('env', {}), **secrets}

# Write back
with open(settings_path, 'w') as f:
  json.dump(existing, f, indent=2)
  f.write('\n')

print(f"{settings_path} updated with {len(secrets)} variables")
PYEOF

  python3 "$TEMP_PY" "$TEMP_ENV" "$SETTINGS"
  rm -f "$TEMP_PY"
fi

rm -f "$TEMP_ENV"

echo ""
echo "Done!"
