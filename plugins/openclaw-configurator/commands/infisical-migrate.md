---
description: Migrate an OpenClaw instance's secrets from plaintext .env into self-hosted Infisical and wire the Docker stack to inject them at runtime. Prompts for the Infisical project id; pushes sensitive keys; patches Dockerfile/compose/wrapper; rebuilds; strips plaintext; audits.
argument-hint: "[infisical-project-id]"
allowed-tools: ["Read", "Edit", "Bash", "Glob", "Grep", "Skill", "WebFetch"]
---

# Infisical Migrate

Migrate an OpenClaw instance's secrets from plaintext `.env` into self-hosted Infisical and wire the Docker stack to inject them at runtime. This is **destructive** (rebuilds containers, strips plaintext) — every step that changes state requires explicit confirmation, and backups are taken first.

Load the **infisical-migration** skill for the full playbook, troubleshooting matrix, and maintenance commands. Verify Infisical CLI syntax via **docs-research** (`https://infisical.com/docs/cli/overview`).

> **Rollback (state up-front):** restore `.env`, `docker-compose.yml`, and `Dockerfile` from their `.pre-infisical.bak` copies, then `cd "$PROJECT_DIR" && docker compose down && docker compose up -d --build`.

## Path resolution — uses BOTH dirs

```bash
INSTANCE_DIR="${OPENCLAW_INSTANCE_DIR:-${OPENCLAW_PROJECT_DIR:-$(pwd)}}"   # secrets live here
INSTANCE=$(basename "$INSTANCE_DIR" | sed 's/^\.openclaw-//')             # e.g. team
PROJECT_DIR="${OPENCLAW_PROJECT_DIR:-/docker/openclaw-$INSTANCE}"          # docker files live here
```

- **Instance dir** → `openclaw.json` (SecretRef ids), `agents/main/agent/auth-profiles.json`, instance `.env`.
- **Project dir** → `docker-compose.yml`/`docker-compose.yaml`, `Dockerfile`, `scripts/`, `.infisical.conf`.

## Process

### Step 1 — Inputs

- Parse the Infisical **project id** from `$ARGUMENTS`. If absent, ask the user for it.
- Ask for the environment slug (default `prod`) and domain (default `https://k.macstack.ai`).
- Read machine-identity creds from `/etc/openclaw/infisical.env`. If missing, instruct the user to create it (mode 600, `INFISICAL_CLIENT_ID` + `INFISICAL_CLIENT_SECRET`) and stop — never hardcode creds.

### Step 2 — Preconditions & backups

```bash
command -v infisical >/dev/null || { echo "Install Infisical CLI first: npm install -g @infisical/cli"; exit 1; }
COMPOSE_FILE=$([ -f "$PROJECT_DIR/docker-compose.yaml" ] && echo docker-compose.yaml || echo docker-compose.yml)
[ -f "$PROJECT_DIR/$COMPOSE_FILE" ] || { echo "ERROR: no $COMPOSE_FILE in $PROJECT_DIR"; exit 1; }

cp "$INSTANCE_DIR/.env" "$INSTANCE_DIR/.env.pre-infisical.bak" 2>/dev/null
cp "$PROJECT_DIR/$COMPOSE_FILE" "$PROJECT_DIR/$COMPOSE_FILE.pre-infisical.bak"
cp "$PROJECT_DIR/Dockerfile" "$PROJECT_DIR/Dockerfile.pre-infisical.bak" 2>/dev/null
```

### Step 3 — Enumerate keys & confirm

Run **infisical-migration** Step 1 to build the key set (openclaw.json SecretRef ids ∪ `.env` keys ∪ security-audit inline findings). Show the user the list of **key names** (never values) and ask for explicit confirmation before any push. Exclude OAuth/CLI credentials (`openai-codex:default`, Claude CLI tokens) — those stay in OpenClaw's encrypted store.

### Step 4 — Authenticate & push

Run **infisical-migration** Step 2: universal-auth login, `infisical secrets set` for the confirmed keys, then list them back to verify. Read each value from `.env`; never echo values.

### Step 5 — Patch the Docker stack

Run **infisical-migration** Steps 3–5 via Edit: create `.infisical.conf`, copy the `openclaw-with-infisical` wrapper, patch the `Dockerfile` (install CLI + ENTRYPOINT) and `docker-compose` (`env_file` for both services, CLI-service entrypoint). Show each diff and confirm before writing.

### Step 6 — Build & start

Only after a final confirmation, run **infisical-migration** Step 6 (`docker compose build` + `down`/`up -d`) and tail logs. Verify success indicators (`Injecting N Infisical secrets`, `[gateway] ready`). On `SecretRefResolutionError`, follow the skill's troubleshooting matrix (add the missing key, or disable the skill in `openclaw.json`) before continuing.

### Step 7 — Strip plaintext & migrate auth-profiles

Confirm, then run **infisical-migration** Step 7: reduce `.env` to infrastructure-only vars and migrate the `auth-profiles.json` API key to a `keyRef` SecretRef. Validate JSON before writing each file. Restart the stack.

### Step 8 — Audit & finish

```bash
cd "$PROJECT_DIR"
docker compose exec openclaw-gateway-$INSTANCE openclaw secrets audit --check
```

Expected `plaintext=1, unresolved=0, shadowed=0, legacy=0` (the `plaintext=1` codex sentinel is a known false positive — do not touch). Prompt for a Telegram/bot smoke test. When verified, offer to remove the `*.pre-infisical.bak` backups.

## Notes

- This command needs `$OPENCLAW_PROJECT_DIR` set (or to be run from the project dir) because it edits Docker files there; `$OPENCLAW_INSTANCE_DIR` locates the secrets.
- Never commit `.infisical.conf` or `/etc/openclaw/infisical.env`.
- After future OpenClaw upgrades, re-run `openclaw secrets audit --check` (see **release-migration**).
