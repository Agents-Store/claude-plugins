---
name: workspace-overview
description: OpenClaw workspace architecture and file system overview — directory structure, file loading mechanics, character limits, scan categories (A-J), and subfolder organization patterns. Use this skill whenever the user asks about how the workspace is structured, what files get loaded automatically, character limits, what goes where, or how to organize their workspace. This is the foundational skill — use it first when the user is new to OpenClaw or asks broad questions about workspace organization, even before more specific skills like agents-md or soul-md.
---

# OpenClaw Workspace Architecture

This skill covers the structure, loading mechanics, and organization of an OpenClaw agent workspace.

## Instance Directory Structure

Each OpenClaw instance lives at `~/.openclaw-{name}/` (e.g. `~/.openclaw-nova/`). The plugin runs from this directory as CWD. All paths below are relative to CWD.

```
./                              # Instance root (~/.openclaw-{name}/)
├── workspace/                  # Workspace files (auto-injected)
│   ├── AGENTS.md               # Operating rules, procedures
│   ├── SOUL.md                 # Persona, tone, boundaries
│   ├── USER.md                 # User profiles, preferences
│   ├── IDENTITY.md             # Agent name, emoji, avatar
│   ├── TOOLS.md                # Tool notes, priorities
│   ├── HEARTBEAT.md            # Background task checklist
│   ├── MEMORY.md               # Curated long-term memory
│   ├── BOOT.md                 # Gateway restart instructions
│   ├── BOOTSTRAP.md            # First-run ritual (deleted after)
│   ├── docs/                   # On-demand reference files
│   │   ├── rules/              # Extended rules
│   │   ├── procedures/         # Task-specific guides
│   │   ├── clients/            # Client profiles
│   │   └── standing-orders/    # Recurring autonomous tasks
│   ├── workflows/              # .prose workflow files
│   ├── canvas/                 # Canvas UI files (optional)
│   ├── memory/                 # Daily logs (auto-created)
│   └── skills/                 # Instance-specific skills
├── agents/
│   └── main/
│       └── sessions/
│           ├── sessions.json   # Session index
│           └── *.jsonl         # Session transcripts
├── memory/
│   └── main.sqlite             # Vector search index (auto-built)
├── cron/
│   └── jobs.json               # Scheduled jobs
├── logs/
│   └── openclaw.log            # Gateway log
├── openclaw.json               # Central gateway configuration
├── credentials/                # DO NOT SCAN
├── telegram/                   # DO NOT SCAN
├── devices/                    # DO NOT SCAN
├── subagents/                  # DO NOT SCAN
├── completions/                # DO NOT SCAN
├── delivery-queue/             # DO NOT SCAN
├── media/                      # DO NOT SCAN
├── identity/                   # DO NOT SCAN
├── config.yaml                 # DO NOT SCAN
└── *.bak*                      # DO NOT SCAN
```

### Shared Resources (absolute paths — one set for all instances)

```
/root/openclaw-skills/*/SKILL.md            # Shared public skills
/root/openclaw-private-skills/*/SKILL.md    # Shared private skills
/root/openclaw-plugins/packages/*/          # Shared public plugins
/root/openclaw-plugins-private/packages/*/  # Shared private plugins
```

## Scan Categories (A–J + Shared)

| Cat | Target | Path | Mode |
|-----|--------|------|------|
| A | Auto-injected workspace files | `./workspace/AGENTS.md`, `SOUL.md`, `USER.md`, `IDENTITY.md`, `TOOLS.md`, `HEARTBEAT.md`, `MEMORY.md`, `BOOT.md`, `BOOTSTRAP.md` | Read + Write |
| B | Memory files | `./workspace/memory/*.md` + `./workspace/MEMORY.md` | Read + Write |
| C | Instance skills | `./workspace/skills/*/SKILL.md` | Read only |
| D | Subfolders (on-demand) | `./workspace/docs/**/*.md` + `./workspace/workflows/**/*.prose` | Read + Write |
| E | Config | `./openclaw.json` | Read + Write (with permission) |
| F | Sessions | `./agents/main/sessions/sessions.json` + `*.jsonl` | Read only |
| G | Memory index | `./memory/main.sqlite` | Read only (vector search index) |
| H | Cron | `./cron/jobs.json` | Read only |
| I | Logs | `./logs/openclaw.log` | Read only |
| J | Canvas | `./workspace/canvas/` | Read + Write |
| — | Shared public skills | `/root/openclaw-skills/*/SKILL.md` | Read only |
| — | Shared private skills | `/root/openclaw-private-skills/*/SKILL.md` | Read only |
| — | Shared plugins | `/root/openclaw-plugins/packages/*/` + private | Read only |

**Write scope**: The plugin creates/edits files in `./workspace/` and `./openclaw.json` (with explicit user permission). Everything else is read-only for analysis.

## DO NOT SCAN — Excluded Directories

These contain sensitive/internal data (OAuth tokens, session state, device pairing, certs) — reading them risks exposing secrets in LLM context. Do not scan:

- `./credentials/` — OAuth tokens, API keys
- `./telegram/` — Telegram session state
- `./devices/` — device pairing data
- `./subagents/` — internal subagent state
- `./completions/` — LLM completion cache
- `./delivery-queue/` — message delivery queue
- `./media/` — media file cache
- `./identity/` — certificates and identity data
- `./config.yaml` — internal gateway config
- `./*.bak*` — backup files
- `./memory/main.sqlite-wal` — sqlite WAL (do not touch)
- `./memory/main.sqlite-shm` — sqlite shared memory (do not touch)

## Auto-Injected Files (loaded every session)

| File | Purpose | When Loaded |
|------|---------|-------------|
| `AGENTS.md` | Operating rules, priorities, behavioral guidance | Every session |
| `SOUL.md` | Persona, tone, boundaries, values | Every session |
| `USER.md` | User identity, preferences, context | Every session |
| `IDENTITY.md` | Agent name, vibe, emoji, avatar | Every session |
| `TOOLS.md` | Local tool notes and environment-specific details | Every session |
| `HEARTBEAT.md` | Background task checklist | Heartbeat runs only |
| `BOOT.md` | Gateway restart instructions | On gateway restart |
| `MEMORY.md` | Curated long-term memory | Main session only (never in groups) |
| `BOOTSTRAP.md` | First-run ritual (deleted after completion) | First session only |

## Character Limits

- **Per file**: `bootstrapMaxChars` = 20,000 characters (default)
- **Total across all files**: `bootstrapTotalMaxChars` = 150,000 characters (default)
- Files exceeding limits are **truncated silently**
- Override in `./openclaw.json`:
  ```json
  {
    "agents": {
      "defaults": {
        "bootstrapMaxChars": 30000,
        "bootstrapTotalMaxChars": 200000
      }
    }
  }
  ```

## Key Rule: SOUL vs AGENTS Separation

- **SOUL.md** = WHO the agent IS (persona, values, tone, boundaries)
- **AGENTS.md** = HOW the agent OPERATES (procedures, rules, memory management, group chat behavior)
- Never mix personality into AGENTS.md or procedures into SOUL.md

## Workspace Subfolders — On-Demand Reference Files

Only auto-injected files are loaded every session. Everything in subfolders is read on demand by the agent via the `read` tool — saving tokens when content is not relevant.

**Key rules**:
- If content is needed in >= 50% of sessions → keep in auto-injected files
- If content is needed in < 50% of sessions → move to docs/
- If content is critical for safety → keep in AGENTS.md or SOUL.md regardless
- One topic per file, lowercase-hyphen naming

See `references/subfolder-patterns.md` for detailed subfolder structure, templates, and examples.

## Files NOT Auto-Loaded

These must be read manually by the agent when referenced from AGENTS.md:

- `memory/YYYY-MM-DD.md` — daily memory logs
- `docs/**/*.md` — documentation subfolders
- `workflows/*.prose` — workflow files
- `canvas/` — canvas UI files
- `skills/` — instance-specific skills (separate loading system)

## Content Language

Write all workspace file content in English. This ensures consistency across multi-user setups, better compatibility with LLM models (which process English instructions more reliably), and clearer prompt engineering. Users may communicate with the agent in any language, but the workspace files themselves are always English.

## Referencing Subfolders from AGENTS.md

Since subfolders are NOT auto-loaded, reference them explicitly:

```markdown
## Reference Documents
Before starting a task, check if a relevant doc exists.
Read it with: read docs/<folder>/<file>.md

Available docs:
- docs/rules/         — security rules, data classification
- docs/procedures/    — step-by-step guides for specific task types
- docs/clients/       — client profiles, contracts, key facts
- docs/standing-orders/ — recurring tasks and schedules
```

## Version Control

Initialize git tracking for workspace files in a **private** repository. Exclude secrets:
```gitignore
.env
*.key
*.pem
secrets*
```

## Customization Workflow

The recommended approach for workspace optimization:

1. **Scan** — read all current workspace files, check for gaps
2. **Interview** — understand goals, users, tasks, channels, success criteria
3. **Analyze** — identify missing rules, conflicts, unused tools, pain points
4. **Security audit** — check for secrets, prompt injection risks, missing safety rules
5. **Optimize** — generate improved files following best practices
6. **Apply** — show diffs, get approval, write changes to `./workspace/`
7. **Fix permissions** — run chown + doctor in Docker after edits
8. **Iterate** — start short, add rules when problems are observed

## SOUL.md Size Rule

Keep SOUL.md under **2,000 words**. Every word costs tokens on EVERY interaction since it's injected into every prompt. Be concise — personality doesn't need a novel.

## Memory Security

MEMORY.md is loaded **only in main private sessions**, never in group chats. This prevents data leakage across shared contexts. Design AGENTS.md group chat rules accordingly.
