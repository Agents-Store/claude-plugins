---
description: Optimize a specific OpenClaw workspace file or all files at once, with security checks and optional openclaw.json editing
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
argument-hint: <soul|agents|user|tools|heartbeat|identity|memory|bootstrap|boot|config|all>
---

# Workspace Optimize

Optimize a specific OpenClaw workspace file following best practices. CWD is the instance root (standard: `~/.openclaw/`, Docker multi-instance: `~/.openclaw-{name}/`). Files are read from and written to `./workspace/`.

**All generated content MUST be in English.** The interview/conversation with the user can be in any language, but workspace file content is always English.

## Arguments
- file-type: `soul`, `agents`, `user`, `tools`, `heartbeat`, `identity`, `memory`, `bootstrap`, `boot`, `config`, or `all` (required)

Parse from "$ARGUMENTS".

## Process

### 1. Parse arguments
Extract file type from arguments.

### 2. Read current file
Map file type to filename:
- `soul` → `./workspace/SOUL.md` (auto-injected every session)
- `agents` → `./workspace/AGENTS.md` (auto-injected every session)
- `user` → `./workspace/USER.md` (auto-injected every session)
- `tools` → `./workspace/TOOLS.md` (auto-injected every session)
- `heartbeat` → `./workspace/HEARTBEAT.md` (auto-injected in heartbeat runs)
- `identity` → `./workspace/IDENTITY.md` (auto-injected every session)
- `memory` → `./workspace/MEMORY.md` (auto-injected in main sessions only)
- `bootstrap` → `./workspace/BOOTSTRAP.md` (auto-injected when present — one-time first-run ritual, deleted after bootstrap completes)
- `boot` → `./workspace/BOOT.md` (NOT auto-injected — optional, executed via hook on gateway restart)
- `config` → `./openclaw.json` (editable with user permission)
- `all` → process all files sequentially

Read the current file. If it doesn't exist, note that we'll create it from scratch.

### 3. Load relevant skill
Load the corresponding skill for the file type:
- `soul` → soul-md skill
- `agents` → agents-md skill
- `user` → user-md skill
- `tools` → tools-md skill
- `heartbeat` → heartbeat-md skill
- `identity` → identity-md skill
- `memory` → memory-system skill
- `bootstrap` or `boot` → bootstrap-boot skill
- `config` → openclaw-config + config-validation skills

### 4. Gather context
Before optimizing, read related files for context:
- Other workspace files in `./workspace/`
- `./openclaw.json` (for channels, model, tools config)
- Session logs in `./agents/main/sessions/` if available
- Docs subfolders: `./workspace/docs/`, `./workspace/workflows/`
- Canvas: `./workspace/canvas/`

### 5. Security check
Before generating optimized content, run security checks:
- Scan current file for hardcoded secrets
- Check for PII that shouldn't be there
- Verify safety rules are present (red lines in AGENTS.md, boundaries in SOUL.md)
- For `config`: check SecretRef pattern usage

Use the **security-audit** skill for the full checklist.

### 6. Ask clarifying questions
If the current file is empty or being created:
- What is the purpose of this OpenClaw instance?
- Who are the primary users?
- What domain/industry?
- Any specific requirements?

### 7. Generate optimized version
Following the skill's best practices:
- Apply the correct template structure
- Include all recommended sections
- Ensure word count is within limits (SOUL.md < 2,000 words)
- Ensure character count is within limits (< 20,000 chars for auto-injected files)
- For large auto-injected files: recommend extracting infrequently-used content to `docs/` subfolders
- Maintain consistency with other workspace files
- **All content in English**
- Include security best practices (red lines, boundaries, memory isolation)

### 8. Show diff and apply
- Display the proposed new content
- If updating existing file: show what changed
- Ask for approval before writing
- Write the file to `./workspace/` with user's confirmation
- For `config`:
  1. Show proposed `./openclaw.json` changes as diff
  2. Ask for **explicit user confirmation**
  3. Back up: `cp ./openclaw.json ./openclaw.json.bak`
  4. Validate JSON syntax before writing
  5. Apply changes
  6. Run: `openclaw doctor --fix` (Docker multi-instance: `openclaw-{name} doctor --fix`)

### 9. Fix permissions (Docker deployments only)
After writing files in Docker deployments, fix permissions:
```bash
# Derive instance name from OPENCLAW_PROJECT_DIR (if set) or CWD (e.g., /root/.openclaw-team → team)
INSTANCE_DIR="${OPENCLAW_PROJECT_DIR:-$(pwd)}"
INSTANCE=$(basename "$INSTANCE_DIR" | sed 's/^\.openclaw-//')
cd "${OPENCLAW_PROJECT_DIR:-/docker/openclaw-$INSTANCE}"
docker compose exec -u root openclaw-gateway chown -R node:node /home/node/.openclaw/
```
For non-Docker deployments, skip this step.

### 10. Verify
After writing:
- Check file size against limits
- Verify consistency with other workspace files
- Suggest next steps (e.g., "Now optimize your AGENTS.md to match")

## For `all` mode
Process files in this order:
1. IDENTITY.md (foundational)
2. SOUL.md (persona)
3. USER.md (users)
4. AGENTS.md (rules)
5. TOOLS.md (tools)
6. HEARTBEAT.md (background tasks)
7. MEMORY.md (memory structure)
8. openclaw.json (configuration — with user permission)

Ask for approval after each file before proceeding to the next.
Run security check across all files at the end.
Fix permissions once after all edits are complete.
