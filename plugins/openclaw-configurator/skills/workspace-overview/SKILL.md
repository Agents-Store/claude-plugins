---
name: workspace-overview
description: OpenClaw workspace architecture and file system overview. Use when the user asks about OpenClaw workspace structure, how workspace files are loaded, character limits, subfolder patterns, or what goes in each file. Triggers on questions like "how does OpenClaw workspace work", "what files does OpenClaw load", "workspace file limits", "how to organize OpenClaw workspace".
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
│   ├── docs/                   # Read on demand
│   │   ├── clients/
│   │   ├── procedures/
│   │   ├── contracts/
│   │   └── standing-orders/
│   ├── workflows/              # .prose files
│   ├── memory/                 # Daily logs (auto-created)
│   └── skills/                 # Instance-specific skills
├── agents/
│   └── main/
│       └── sessions/
│           ├── sessions.json   # Session index
│           └── *.jsonl         # Session transcripts
├── cron/                       # Cron job configurations
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
├── canvas/                     # DO NOT SCAN
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

## Scan Targets for Evaluation (11 total)

| # | Target | Path | Mode |
|---|--------|------|------|
| 1 | Workspace files | `./workspace/*.md` | Read + Write |
| 2 | Workspace docs | `./workspace/docs/**/*.md` | Read + Write |
| 3 | Instance skills | `./workspace/skills/*/SKILL.md` | Read only |
| 4 | Sessions | `./agents/main/sessions/` | Read only |
| 5 | Config | `./openclaw.json` | Read only |
| 6 | Memory logs | `./workspace/memory/*.md` | Read only |
| 7 | Cron jobs | `./cron/` | Read only |
| 8 | Logs | `./logs/openclaw.log` | Read only |
| 9 | Shared public skills | `/root/openclaw-skills/*/SKILL.md` | Read only |
| 10 | Shared private skills | `/root/openclaw-private-skills/*/SKILL.md` | Read only |
| 11 | Shared plugins | `/root/openclaw-plugins/packages/*/` + private | Read only |

**Write scope**: The plugin only creates/edits files inside `./workspace/`. Everything else is read-only for analysis.

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

## Files NOT Auto-Loaded

These must be read manually by the agent when referenced from AGENTS.md:

- `memory/YYYY-MM-DD.md` — daily memory logs
- `docs/**/*.md` — documentation subfolders
- `workflows/*.prose` — workflow files
- `skills/` — instance-specific skills (separate loading system)

## Referencing Subfolders from AGENTS.md

Since subfolders are NOT auto-loaded, reference them explicitly:

```markdown
## Documentation
When needed, read files from docs/:
- docs/clients/ — client profiles (read before working on a client matter)
- docs/procedures/ — methodologies and templates
- docs/standing-orders/ — recurring autonomous task programs
```

## DO NOT SCAN — Excluded Directories

These directories contain sensitive/internal data and must NEVER be read or scanned:

- `./credentials/` — OAuth tokens, API keys
- `./telegram/` — Telegram session state
- `./devices/` — device pairing data
- `./subagents/` — internal subagent state
- `./completions/` — LLM completion cache
- `./delivery-queue/` — message delivery queue
- `./media/` — media file cache
- `./canvas/` — canvas state
- `./identity/` — certificates and identity data
- `./config.yaml` — internal gateway config
- `./*.bak*` — backup files

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
4. **Optimize** — generate improved files following best practices
5. **Apply** — show diffs, get approval, write changes to `./workspace/`
6. **Iterate** — start short, add rules when problems are observed

## SOUL.md Size Rule

Keep SOUL.md under **2,000 words**. Every word costs tokens on EVERY interaction since it's injected into every prompt. Be concise — personality doesn't need a novel.

## Memory Security

MEMORY.md is loaded **only in main private sessions**, never in group chats. This prevents data leakage across shared contexts. Design AGENTS.md group chat rules accordingly.
