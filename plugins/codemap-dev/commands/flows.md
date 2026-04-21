---
description: Find main user flows (entry points → services → DB) and visualize them
argument-hint: (no arguments — auto-discovers flows)
---

# Discover and Visualize User Flows

Find the main user flows in the project and generate visual diagrams for each.

## Instructions

1. Read all three codemap skills:
   - `${CLAUDE_PLUGIN_ROOT}/skills/codemap-explain/SKILL.md` — for understanding and describing flows
   - `${CLAUDE_PLUGIN_ROOT}/skills/codemap-diagram/SKILL.md` — for generating flow diagrams
   - `${CLAUDE_PLUGIN_ROOT}/skills/codemap-review/SKILL.md` — for noting flow-level issues (missing validation, unprotected routes, missing error handling)

### Discover Entry Points

2. Find all route definitions / API endpoints / CLI commands:
   - Flask: Grep for `@.*\.route` or `@.*_bp\.route` in routes/ directory
   - Django: Read urls.py files
   - Express: Grep for `router.get`, `router.post`, etc.
   - Next.js: Read app/ or pages/ directory structure
   - Generic: Grep for HTTP method decorators or handler registrations

### Identify Major Flows

3. Group entry points into logical user flows:
   - **Authentication flow** — login, register, logout, password reset
   - **Main CRUD flows** — create, read, update, delete for primary entities
   - **Key feature flows** — the 2-3 most important features of the application
   - **Navigation flow** — how users move between sections

4. For each major flow (max 5-6 flows):
   - Use codemap-explain methodology to trace the call chain: route handler → service/logic → model/DB → response
   - Identify decision points and branches
   - Note external service calls
   - Identify the database operations involved
   - Apply codemap-review to spot issues in the flow (unprotected routes, missing validation, error handling gaps)

### Generate Flow Diagrams

5. For each major flow, generate a flowchart:
   - Use the flowchart template from mxgraph-templates.md
   - Apply color coding: green for logic, blue for data, yellow for interface
   - Include decision diamonds for conditional logic
   - Label edges with data being passed
   - Highlight any issues found during review (red border on problematic steps)
   - Save to `docs/codemap/diagrams/flow-{name}.drawio`
   - Call `open_drawio_xml` for preview

### Generate Flows Documentation

6. Write `docs/codemap/FLOWS.md` with:
   - **Flow Summary** — list of all discovered flows with one-line descriptions
   - **Flow Details** — for each flow:
     - Entry point (URL, method)
     - Steps in the flow (using codemap-explain 4-layer model for complex steps)
     - Database operations
     - External service calls
     - Issues found (from codemap-review)
     - Link to the flow diagram
   - **Common Patterns** — shared patterns across flows (e.g., all routes use @login_required)

### Output

7. Show all generated diagram file paths and preview URLs
8. Show the FLOWS.md file path
9. Summary: total flows discovered, total diagrams generated, any cross-cutting issues found
10. Suggest: "Use `/codemap:diagram sequence <endpoint>` for a detailed sequence diagram of any specific endpoint"