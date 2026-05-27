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

## 2026-05-27 — codemap-explain: Content quality overhaul

**Feature:** Rewrote codemap-explain skill and architect-explainer agent with clarification step, reading strategy, output template, verification, next steps, and reference file
**Implementation:**
- Added Step 1: Clarify Scope and Depth — asks user about depth (overview/moderate/deep dive), aspect, and experience level before explaining
- Added Step 2: Read and Analyze Code — structured reading strategy per scope (function/file/module/project)
- Added Step 4: Verify Your Explanation — cross-check claims against actual code before presenting
- Added Step 5: Suggest Next Steps — 2-3 actionable follow-ups tailored to user's interest
- Added Output Format template with consistent headers and depth-based section rules
- Created references/explanation-patterns.md — analogies for 20+ patterns, framework-specific tips (React, Express, Flask, Django, Spring, Go), explanation anti-patterns
- Updated architect-explainer agent to reinforce new methodology: clarify → analyze → explain → verify → next steps
- Expanded description frontmatter with additional trigger phrases
- Expanded Scope Adjustments with full-project scope and Format guidance
- Expanded Tone Rules with "Do NOT" anti-patterns
- Expanded Error Handling (minified code, binary files)
- Updated evals: 4 → 6 test cases, all expectations updated for new structure
**Rationale:** Skill produced inconsistent output — no format template, no clarification of user intent, no reading strategy for code analysis, no verification step. Users couldn't control depth or focus of explanations. Agent didn't reinforce the new methodology from its own system prompt.

## 2026-05-27 — frontend-test: Add Playwright MCP frontend testing

**Feature:** Added frontend testing capability via Playwright MCP — navigate a running app, explore UI, test forms and interactions, collect console/network errors, and generate a structured health report
**Implementation:**
- Added `playwright` stdio MCP server to `.mcp.json` (`npx @playwright/mcp@latest --headless`)
- Created `skills/frontend-test/SKILL.md` — 5-phase testing methodology (URL detection → Discovery → Interaction → Error Analysis → Report generation)
- Created `agents/frontend-tester.md` — Sonnet model, green color, dedicated browser automation agent with full Playwright MCP tool list
- Created `commands/test-frontend.md` — `/codemap:test-frontend [url]` entry point that delegates to the frontend-tester agent
- Report output at `docs/codemap/FRONTEND.md` with sections: Summary metrics, Pages Discovered, Console Errors, Network Failures, Forms, UI Issues, Recommendations
- Skill includes Step 0 Execution Mode (agent vs inline choice) matching existing skill pattern
- Skill includes Error Handling for: app not reachable, authentication required, Playwright MCP not connected, SPA dynamic content
- Updated plugin.json v1.2.0 → v1.3.0, added `playwright` and `frontend-testing` keywords
- Updated README.md with new command, skill, agent, and requirements
**Rationale:** Plugin provided code-level understanding (review, explain, diagram) but lacked runtime/UI perspective. Frontend testing via Playwright MCP completes the picture — users can now get a comprehensive report covering both code quality and actual UI behavior of their application.
