---
description: Generate a full onboarding report — README summary, stack, folder structure, entry points, how to run locally, and 3 main diagrams (architecture, main flow, DB)
argument-hint: (no arguments — analyzes current project)
allowed-tools: [Read, Grep, Glob, Write, Bash, Agent, Skill]
---

# Onboard to Current Project

Generate a comprehensive onboarding package for a developer joining this project.

## Instructions

1. Read the primary skill:
   - `${CLAUDE_PLUGIN_ROOT}/skills/codemap-explain/SKILL.md` — explanation methodology

2. Ensure output directories exist: `docs/codemap/diagrams/` — create if missing.

3. Launch the **architect-explainer** agent with a prompt to perform the full onboarding:

   **Phase 1 — Project Analysis:**
   - Read root files (README.md, CLAUDE.md, package.json/requirements.txt, docker-compose, .env.example)
   - Scan directory structure, identify tech stack, find entry points
   - Read model definitions and key configuration

   **Phase 2 — Generate Documentation:**
   - Create `docs/codemap/ONBOARDING.md` (overview, stack, directory structure, entry points, how to run, key concepts)
   - Create `docs/codemap/ARCHITECTURE.md` (components, data flow, layers, external dependencies)

   **Phase 3 — Generate 3 Diagrams** (via codemap-diagram skill):
   - `docs/codemap/diagrams/architecture.drawio` — C4 container diagram
   - `docs/codemap/diagrams/main-flow.drawio` — primary user flow
   - `docs/codemap/diagrams/erd.drawio` — database ERD

   **Phase 4 — Verification (MANDATORY):**
   - Verify all 3 diagrams were created: architecture.drawio, main-flow.drawio, erd.drawio
   - If any diagram is missing, generate it before proceeding
   - Verify all files are `.drawio` (not `.mmd` or any other format)

   **Phase 5 — Summary:**
   - List all generated files with descriptions
   - Show diagram preview URLs
   - Suggest next steps
