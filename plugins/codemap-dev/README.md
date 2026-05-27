# codemap-dev

Code understanding plugin for Claude Code. Helps developers (especially beginners) quickly onboard to unfamiliar projects through structured code review, step-by-step explanations, and visual diagrams via drawio-mcp.

## What It Does

- **Onboarding**: Generates a full onboarding package — project overview, architecture docs, and 3 key diagrams
- **Code Review**: Beginner-friendly review with "why" explanations, not just "fix this"
- **Code Explanation**: 4-layer model (Context → Data Flow → Details → Pitfalls)
- **Diagrams**: Architecture, ERD, user flows, sequence diagrams — all as native .drawio files via drawio-mcp

## Usage Modes

| How you invoke | What happens |
|---|---|
| `/codemap:review file.py` (command) | Agent launches **automatically** |
| `/codemap:explain app.py` (command) | Agent launches **automatically** |
| `/codemap:diagram architecture` (command) | Agent launches **automatically** |
| "review file.py" (chat trigger) | Skill triggers → **asks**: agent or inline? |
| "explain app.py" (chat trigger) | Skill triggers → **asks**: agent or inline? |

**Commands** always delegate to specialized agents. **Skills** (auto-triggered by chat) give you the choice.

## Requirements

- **drawio-mcp** — public HTTP MCP server (auto-configured by plugin, no API key needed)

## Commands

| Command | Description |
|---------|-------------|
| `/codemap:onboard` | Full onboarding report + 3 diagrams (architecture, main flow, ERD) |
| `/codemap:review <path\|PR#>` | Beginner-friendly code review |
| `/codemap:explain <path\|symbol>` | Step-by-step code explanation |
| `/codemap:diagram <type> [scope]` | Generate specific diagram (architecture, flow, db, sequence, deps) |
| `/codemap:db` | Parse models/migrations and generate ERD + DB documentation |
| `/codemap:flows` | Discover and visualize main user flows |

## Skills (auto-triggered in chat)

| Skill | Triggers when... |
|-------|-----------------|
| `codemap-review` | User asks to review code, check quality, find issues |
| `codemap-explain` | User asks to explain code, understand a file/function. Asks about depth (overview/moderate/deep dive) and aspect of interest before explaining. Ref: `explanation-patterns.md` |
| `codemap-diagram` | User asks for a diagram, visualization, ERD, flow chart |

## Agents

| Agent | Role | Model |
|-------|------|-------|
| `code-reviewer` | Focused code review with educational feedback | Opus |
| `architect-explainer` | Architecture analysis and guided project tours | Opus |
| `diagrammer` | Diagram generation via drawio-mcp | Sonnet |

## Output Artifacts

All generated files are saved to `docs/codemap/` in the project:

- `docs/codemap/ONBOARDING.md` — summary document for newcomers
- `docs/codemap/ARCHITECTURE.md` — textual architecture description with diagram links
- `docs/codemap/DB.md` — database schema description + ERD
- `docs/codemap/FLOWS.md` — main user flows with diagrams
- `docs/codemap/diagrams/*.drawio` — all generated diagrams (open with draw.io)

## Diagram Types

| Type | Command | Use for |
|------|---------|---------|
| C4 Container | `diagram architecture` | System overview — services, databases, external APIs |
| Flowchart | `diagram flow <feature>` | User action step-by-step progression |
| ERD | `diagram db` or `db` | Database tables and relationships |
| Sequence | `diagram sequence <endpoint>` | Request lifecycle between components |
| Dependency | `diagram deps <module>` | Module import/dependency graph |

## Principles

- All diagrams are native mxGraph XML rendered via drawio-mcp — no Mermaid
- Skills are reusable: work both in commands and when users ask questions in chat
- Review feedback explains "why", not just "what" to fix
- Explanations use real names from code, not generic labels