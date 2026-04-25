# LEARNINGS.md — codemap-dev

Accumulated fixes and discoveries from plugin usage.

## 2026-04-25 — commands + agents + diagram: Agent delegation, MCP tool fix, anti-Mermaid

**Feature:** Rewrote all 6 commands to delegate work to agents; fixed wrong MCP tool name; added anti-Mermaid guardrails; added onboarding verification step
**Implementation:**
- Commands now reference 1 primary skill + launch the appropriate agent (code-reviewer, architect-explainer, diagrammer)
- Added `allowed-tools` to all commands (was missing)
- Fixed `open_drawio_xml` → `create_diagram` (correct drawio-mcp tool name) in SKILL.md, diagrammer agent, evals
- Added CRITICAL RULES block in codemap-diagram skill: hard NO MERMAID requirement
- Reinforced NO MERMAID in diagrammer agent
- Added mandatory verification phase in onboard command (check all 3 diagrams exist and are .drawio)
- Fixed XML comment in mxgraph-templates.md base template
- Changed diagrammer agent model from opus to sonnet
- Added "Step 0: Execution Mode (MANDATORY)" to all 3 skills — when auto-triggered, asks user to choose agent or inline before doing any work
- Updated README.md with Usage Modes table (command = auto agent, chat trigger = user choice)
- Added Error Handling sections to all 3 skills (drawio unavailable, file not found, ORM not detected, etc.)
- Added failure-case evals (nonexistent paths, empty projects) to all 3 skill evals
- Fixed README model mismatch: diagrammer listed as Opus but actually Sonnet
- Added explicit `docs/codemap/diagrams/` directory creation step to onboard, db, flows commands
**Rationale:** Agents existed but were never called. Wrong MCP tool name caused diagram generation failures and Mermaid fallbacks. Missing verification meant onboarding sometimes produced incomplete output. Skills didn't offer agent delegation when auto-triggered — user had no way to use agents outside of commands. Missing error handling led to confusing failures. Missing directory creation step caused file write errors.
