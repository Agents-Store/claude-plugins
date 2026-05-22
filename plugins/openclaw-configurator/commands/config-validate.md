---
description: Validate openclaw.json against official documentation, check for latest features, detect inline secrets, verify cross-references with workspace files, and optionally reconcile config against a newer release
allowed-tools: ["Read", "Edit", "Bash", "Glob", "Grep", "Skill", "WebFetch", "WebSearch"]
argument-hint: "[--secrets] [--docs] [--all] [--upgrade] [--upgrade-from <tag>]"
---

# Config Validate

Validate the current OpenClaw instance's `openclaw.json` against official documentation and best practices.

**Path resolution (in priority order):**
1. `$OPENCLAW_INSTANCE_DIR` — runtime workspace dir holding `openclaw.json` (standard: `~/.openclaw/`, Docker multi-instance: `~/.openclaw-{name}/`).
2. `$OPENCLAW_PROJECT_DIR` — git/docker-compose project dir; fallback only.
3. `$(pwd)` — current directory.

Workspace commands always target the **instance** dir, which usually differs from the project dir.

## Process

### 1. Resolve and read openclaw.json

```bash
INSTANCE_DIR="${OPENCLAW_INSTANCE_DIR:-${OPENCLAW_PROJECT_DIR:-$(pwd)}}"
cd "$INSTANCE_DIR" || { echo "ERROR: cannot access $INSTANCE_DIR"; exit 1; }
cat ./openclaw.json
```

If not found, report error and stop.

### 2. Structure Validation

Check that all expected top-level sections exist:
- `agents` (required)
- `channels` (at least one channel recommended)
- `tools` (recommended)
- `plugins` (optional)
- `session` (optional)

### 3. Secret Detection

```bash
# Check for potential inline secrets (tokens, API keys)
grep -n -E '"[A-Za-z0-9_:.-]{20,}"' ./openclaw.json | grep -vi '"source"\|"provider"\|"id"\|"model"\|"profile"\|"mode"\|"workspace"\|"description"\|"name"'
```

If inline secrets found:
- Flag as CRITICAL security issue
- Show the correct SecretRef pattern:
  ```json
  {
    "source": "env",
    "provider": "default",
    "id": "ENV_VAR_NAME"
  }
  ```
- Remind user that `.env` file should contain the actual values

**Known false positive**: `openclaw doctor` may report `unresolved SecretRef "env:default:..."` when running outside gateway runtime. This is safe to ignore.

### 4. Field-Level Validation

Check each field against expected values. Use the **config-validation** skill for the complete checklist. Key checks:

- `agents.defaults.model` — is it set and valid?
- `agents.defaults.heartbeat.model` — using a cheap model?
- `channels.*.dmPolicy` — not `"open"` in production?
- `tools.loopDetection.enabled` — true for production?
- `agents.defaults.userTimezone` — valid IANA timezone?

### 5. Cross-Validation with Workspace Files

Read workspace files and cross-check:

```bash
# Check which workspace files exist
for f in AGENTS.md SOUL.md USER.md IDENTITY.md TOOLS.md HEARTBEAT.md MEMORY.md; do
  [ -f "./workspace/$f" ] && echo "OK $f" || echo "MISSING $f"
done
```

Cross-checks:
- Every user ID in `channels.*.allowFrom` should have a profile in `./workspace/USER.md`
- If heartbeat is configured, `./workspace/HEARTBEAT.md` should exist and have content
- If groups are configured, `./workspace/AGENTS.md` should have group chat rules
- `userTimezone` should match timezone in `./workspace/USER.md`

### 6. Fetch Latest Documentation

To check official OpenClaw docs for latest features, follow the **docs-research** skill — it holds the tool-priority ladder (Firecrawl → Exa → Perplexity → Jina → context7 → WebFetch) and the OpenClaw documentation URL map.

Compare current config with latest available features. Flag:
- New fields available but not configured
- Deprecated fields still in use
- Newer model versions available

### 7. Generate Validation Report

```markdown
# openclaw.json Validation Report

## Instance
- Path: [CWD]
- Config size: [bytes]

## Security
- Inline secrets: [NONE / FOUND (list)]
- SecretRef usage: [correct / needs migration]
- dmPolicy: [secure / needs review]

## Configuration Quality
| Section | Status | Issues |
|---------|--------|--------|
| agents.defaults | OK/WARN | [details] |
| heartbeat | OK/WARN/MISSING | [details] |
| channels | OK/WARN | [details] |
| tools | OK/WARN | [details] |
| plugins | OK/WARN/NONE | [details] |
| session | OK/WARN/NONE | [details] |

## Cross-Validation
| Check | Result |
|-------|--------|
| allowFrom ↔ USER.md | [match/mismatch] |
| heartbeat ↔ HEARTBEAT.md | [aligned/misaligned] |
| groups ↔ AGENTS.md | [covered/missing] |
| timezone ↔ USER.md | [match/mismatch] |

## Feature Freshness
- [New features available / all current]

## Recommendations
1. [Most important fix]
2. [Second priority]
3. [Third priority]
```

### 8. Offer to Fix

If issues found, offer to fix them:
- For openclaw.json changes: show proposed diff, ask for explicit confirmation
- Always back up before editing: `cp ./openclaw.json ./openclaw.json.bak`
- After editing: run `openclaw doctor --fix` to verify (Docker multi-instance: `openclaw-{name} doctor --fix`)
- For workspace file issues: suggest using `/workspace-optimize <file>`

### 9. Upgrade Reconciliation Mode (`--upgrade` / `--upgrade-from <tag>`)

For an instance whose **code** was already updated but whose **config** was never reconciled against the new release (e.g. updated manually, outside `/instance-update`), run this mode after the normal validation above.

Determine the tag range, then hand off to the **release-migration** skill:

```bash
PROJECT_DIR="${OPENCLAW_PROJECT_DIR:-$(pwd)}"
NEW_TAG=$(git -C "$PROJECT_DIR" describe --tags --abbrev=0 2>/dev/null)

# --upgrade-from <tag>  → OLD_TAG is the provided tag
# --upgrade (no arg)    → OLD_TAG is the tag before NEW_TAG
OLD_TAG="${UPGRADE_FROM:-$(git -C "$PROJECT_DIR" describe --tags --abbrev=0 "$NEW_TAG^" 2>/dev/null)}"
echo "Reconciling config from $OLD_TAG → $NEW_TAG"
```

Invoke **release-migration** with `OLD_TAG` and `NEW_TAG`. It reads the changelog, recommends new features, migrates deprecated/legacy settings (with the safeguards above), and runs `openclaw doctor --fix`. This is the same reconciliation phase `/instance-update` runs automatically — use it standalone here.
