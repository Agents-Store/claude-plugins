---
description: Generate a full onboarding report — README summary, stack, folder structure, entry points, how to run locally, and 3 main diagrams (architecture, main flow, DB)
argument-hint: (no arguments — analyzes current project)
---

# Onboard to Current Project

Generate a comprehensive onboarding package for a developer joining this project.

## Instructions

1. Read all three codemap skills:
   - `${CLAUDE_PLUGIN_ROOT}/skills/codemap-review/SKILL.md` — for code quality assessment
   - `${CLAUDE_PLUGIN_ROOT}/skills/codemap-explain/SKILL.md` — for explanation methodology
   - `${CLAUDE_PLUGIN_ROOT}/skills/codemap-diagram/SKILL.md` — for diagram generation rules

### Phase 1: Project Analysis

2. Read root files: README.md, CLAUDE.md, package.json or requirements.txt, docker-compose*.yml, Dockerfile*, .env.example
3. Scan directory structure using Glob — identify all top-level directories and their roles
4. Identify the tech stack: framework, database, deployment, key libraries
5. Find entry points: main app file, route definitions, CLI commands, startup scripts
6. Read the main app file and key configuration
7. Read model definitions (models.py, schema files, migrations)
8. Identify how to run locally (Docker, dev server, scripts)

### Phase 2: Generate ONBOARDING.md

9. Create `docs/codemap/` directory if it doesn't exist
10. Write `docs/codemap/ONBOARDING.md` with these sections:
    - **Project Overview** — what this project does, in 2-3 sentences
    - **Tech Stack** — framework, database, key libraries with versions
    - **Directory Structure** — tree with one-line description per directory
    - **Entry Points** — where to start reading the code
    - **How to Run Locally** — step-by-step instructions
    - **Key Concepts** — 3-5 important patterns or conventions used in the project
    - **Code Quality Notes** — apply codemap-review skill to identify top 3-5 patterns (good and bad) across the codebase
    - **Links to Diagrams** — references to the 3 generated diagrams

### Phase 3: Generate Architecture Description

11. Write `docs/codemap/ARCHITECTURE.md` with:
    - System overview (what components exist and how they communicate)
    - Data flow description (request lifecycle)
    - Layer descriptions (data, logic, interface)
    - External dependencies
    - Links to architecture diagram

### Phase 4: Generate 3 Diagrams

Follow the codemap-diagram skill process for each:

12. **Architecture diagram** — C4 container diagram showing all system components
    - Save to `docs/codemap/diagrams/architecture.drawio`
    - Call `open_drawio_xml` for preview

13. **Main user flow** — flowchart of the primary user action
    - Save to `docs/codemap/diagrams/main-flow.drawio`
    - Call `open_drawio_xml` for preview

14. **Database ERD** — all tables with relationships
    - Save to `docs/codemap/diagrams/erd.drawio`
    - Call `open_drawio_xml` for preview

### Phase 5: Summary

15. Output a summary listing all generated files with brief descriptions
16. Show the 3 diagram preview URLs
17. Suggest next steps: "Try `/codemap:explain <file>` to dive deeper into any component"