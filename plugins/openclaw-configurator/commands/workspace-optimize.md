---
description: Optimize a specific OpenClaw workspace file or all files at once
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
argument-hint: <soul|agents|user|tools|heartbeat|identity|memory|bootstrap|boot|config|all>
---

# Workspace Optimize

Optimize a specific OpenClaw workspace file following best practices. CWD is the instance root (`~/.openclaw-{name}/`). Files are read from and written to `./workspace/`.

## Arguments
- file-type: `soul`, `agents`, `user`, `tools`, `heartbeat`, `identity`, `memory`, `bootstrap`, `boot`, `config`, or `all` (required)

Parse from "$ARGUMENTS".

## Process

### 1. Parse arguments
Extract file type from arguments.

### 2. Read current file
Map file type to filename:
- `soul` → `./workspace/SOUL.md`
- `agents` → `./workspace/AGENTS.md`
- `user` → `./workspace/USER.md`
- `tools` → `./workspace/TOOLS.md`
- `heartbeat` → `./workspace/HEARTBEAT.md`
- `identity` → `./workspace/IDENTITY.md`
- `memory` → `./workspace/MEMORY.md`
- `bootstrap` → `./workspace/BOOTSTRAP.md`
- `boot` → `./workspace/BOOT.md`
- `config` → `./openclaw.json` (read-only analysis, recommend changes)
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
- `config` → openclaw-config skill

### 4. Gather context
Before optimizing, read related files for context:
- Other workspace files in `./workspace/`
- `./openclaw.json` (for channels, model, tools config)
- Session logs in `./agents/main/sessions/` if available

### 5. Ask clarifying questions
If the current file is empty or being created:
- What is the purpose of this OpenClaw instance?
- Who are the primary users?
- What domain/industry?
- Any specific requirements?

### 6. Generate optimized version
Following the skill's best practices:
- Apply the correct template structure
- Include all recommended sections
- Ensure word count is within limits (SOUL.md < 2,000 words)
- Ensure character count is within limits (< 20,000 chars)
- Maintain consistency with other workspace files

### 7. Show diff and apply
- Display the proposed new content
- If updating existing file: show what changed
- Ask for approval before writing
- Write the file to `./workspace/` with user's confirmation
- For `config`: show recommended `./openclaw.json` changes but ask user to apply manually

### 8. Verify
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
8. openclaw.json (configuration — recommend only)

Ask for approval after each file before proceeding to the next.
