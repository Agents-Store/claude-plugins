---
description: Configure OpenClaw model-provider authentication with an OAuth/CLI-backend-first, cost-saving bias (Claude CLI, Codex OAuth). Detects current auth, recommends the cheapest working path, runs non-interactive config steps, and prints interactive logins for you to run.
argument-hint: "[anthropic|codex|openai|google|status|all]"
allowed-tools: ["Read", "Bash", "Glob", "Grep", "Edit", "WebFetch", "WebSearch"]
---

# Provider Setup

Set up or change OpenClaw model-provider authentication. Biases toward the **cheapest working path**: reuse a local CLI subscription session (Claude CLI / Codex OAuth) for chat models so you don't pay metered API tokens, and reserve API keys for functions/skills that need the embedded API.

Load the **provider-auth** skill for the full method matrix and the **docs-research** skill for fetching current docs.

**Path resolution (in priority order):**
1. `$OPENCLAW_INSTANCE_DIR` — runtime workspace dir holding `openclaw.json` + `agents/main/agent/auth-profiles.json` (standard: `~/.openclaw/`, Docker multi-instance: `~/.openclaw-{name}/`).
2. `$OPENCLAW_PROJECT_DIR` — git/docker-compose project dir; fallback only.
3. `$(pwd)` — current directory.

## Arguments

- `$ARGUMENTS` — optional target: `anthropic`, `codex`, `openai`, `google`, `all`, or `status`.
  - `status` → run Steps 1–3 only (report current auth + recommendation, **no changes**).
  - A provider name → focus the setup on that provider.
  - empty / `all` → review every configured provider.

## Process

### 1. Detect current auth

```bash
INSTANCE_DIR="${OPENCLAW_INSTANCE_DIR:-${OPENCLAW_PROJECT_DIR:-$(pwd)}}"
cd "$INSTANCE_DIR" || { echo "ERROR: cannot access $INSTANCE_DIR"; exit 1; }

# Current default model + runtime
openclaw config get agents.defaults.model --json 2>/dev/null || grep -n '"model"' ./openclaw.json

# Which providers are authenticated and how (credential type + expiry)
openclaw models status 2>/dev/null

# Which auth profiles exist (NAMES + mode/managedBy only — never read token values aloud)
grep -oE '"[a-z0-9:-]+"[[:space:]]*:[[:space:]]*\{' ./agents/main/agent/auth-profiles.json 2>/dev/null | sed 's/[":{ ]//g'

# Is a local CLI login available on the host?
command -v claude && claude auth status --text 2>/dev/null
command -v codex
```

**Security:** read `auth-profiles.json` to learn which profiles/modes exist — do **not** print token values.

### 2. Verify current guidance (docs change)

Load **docs-research** and fetch the current recommended method for the target provider(s):
- Anthropic → `/providers/anthropic`, `/gateway/cli-backends`
- Codex/OpenAI → `/providers/openai`, `/concepts/oauth`
- General → `/gateway/authentication`, `/concepts/model-providers`

Auth methods (API key vs OAuth vs CLI backend) and recommended models change between releases — confirm before recommending.

### 3. Recommend (cost-first)

Load **provider-auth**. Decide the cheapest working path:

- **Claude:** if `claude` is installed and `claude auth status` shows logged-in → recommend the **Claude CLI backend** (no API key, auto token refresh, bills against the Claude subscription session). Otherwise recommend `claude auth login` first, falling back to an API key only if CLI auth can't work on this host.
- **Codex/OpenAI:** if a ChatGPT/Codex subscription is available → recommend **Codex OAuth** (`openai-codex`) with model `openai/gpt-5.5`.
- **Google/others:** API key via `openclaw models auth add`, or Gemini CLI backend if present.

State the savings explicitly (e.g. "this routes chat through your Claude subscription instead of metered API tokens"). Note that any skill/plugin needing the **embedded API** still requires an API key (kept in `.env`/SecretRef).

If `status` was requested, stop here with the report + recommendation.

### 4. Interactive logins — PRINT, do not run

OAuth/CLI logins open a browser and bind a local callback port; they cannot run in this command's context. Print the exact commands for the user to run via the `!` prefix (or their own shell on the gateway host):

```
! claude auth login
! claude auth status --text
! openclaw models auth login --provider anthropic --method cli --set-default
```

For Codex:
```
! openclaw models auth login --provider openai-codex
```

Wait for the user to confirm they completed the interactive step before continuing.

### 5. Non-interactive config (run, with safeguards)

Apply the canonical model ref + runtime and remove any precedence-blocking embedded-API token profile. Prefer `openclaw` CLI over hand-editing JSON when available:

```bash
# Set canonical model ref (example: Claude)
openclaw models set anthropic/claude-opus-4-7

# Remove a stale embedded-API token profile so the CLI backend takes effect
openclaw config unset auth.profiles.anthropic:claude 2>/dev/null
openclaw config unset agents.defaults.cliBackends.anthropic 2>/dev/null
```

If a field must be edited directly in `openclaw.json` (e.g. model-scoped `agentRuntime.id: "claude-cli"`), follow the **openclaw-config** safeguards:
1. Show the proposed diff and ask for explicit confirmation.
2. `cp ./openclaw.json ./openclaw.json.bak`
3. Validate JSON syntax before writing.
4. Never delete unrelated sections.

### 6. Verify

```bash
openclaw models status
openclaw models list --provider anthropic
openclaw doctor          # Docker multi-instance: openclaw-{name} doctor
```

Report the final auth state: provider, credential type (oauth/cli/api-key), default model + runtime, and whether chat now routes through a subscription session (cost win) vs. the metered API.

**Docker note:** if `openclaw.json` was edited from the host in a Docker deployment, fix permissions (chown + doctor) as in `/workspace-optimize` step 9 before finishing.
