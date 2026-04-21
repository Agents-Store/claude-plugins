---
description: Generate a specific diagram — architecture, flow, db, sequence, deps
argument-hint: <type> [scope] — types: architecture, flow <feature>, db, sequence <endpoint>, deps <module>
---

# Generate Diagram

Create a visual diagram for the specified aspect of the codebase. Request: $ARGUMENTS

## Instructions

1. Read all three codemap skills:
   - `${CLAUDE_PLUGIN_ROOT}/skills/codemap-diagram/SKILL.md` — primary skill for diagram generation
   - `${CLAUDE_PLUGIN_ROOT}/skills/codemap-explain/SKILL.md` — for understanding code before diagramming
   - `${CLAUDE_PLUGIN_ROOT}/skills/codemap-review/SKILL.md` — for identifying architectural issues to highlight in diagrams
2. Read diagram references at `${CLAUDE_PLUGIN_ROOT}/skills/codemap-diagram/references/`

### Parse Arguments

3. Parse `$ARGUMENTS` for diagram type and optional scope:
   - `architecture` → C4 container diagram of the entire system
   - `flow <feature>` → flowchart of a specific feature (e.g., `flow login`, `flow deal-creation`)
   - `db` → ERD of all database tables (delegates to same logic as `/codemap:db`)
   - `sequence <endpoint>` → sequence diagram for a request to specific endpoint (e.g., `sequence POST /deals/add`)
   - `deps <module>` → dependency graph for a module (e.g., `deps routes`, `deps models`)
   - If no argument or unrecognized → ask user which type they want

### Analyze Code

4. Use codemap-explain methodology to understand the code before diagramming:
   - **architecture**: root config files, entry point, all top-level directories
   - **flow**: route handler for the feature, related templates, models
   - **db**: all model definitions, migrations
   - **sequence**: specific route handler, all functions it calls, database queries
   - **deps**: all files in the module, their import statements

### Generate Diagram

5. Follow the codemap-diagram skill's generation process:
   - Choose the right mxGraph XML template from references
   - Apply color coding from color-legend.md
   - Use real names from the code
   - Keep to max 15 nodes (split if needed)
   - Add title and labels
   - If codemap-review identifies architectural issues, highlight them in the diagram (e.g., red border on problematic components)

6. Save to `docs/codemap/diagrams/{type}-{scope}.drawio`
   - Create directory if it doesn't exist
   - Naming: `architecture.drawio`, `flow-login.drawio`, `erd.drawio`, `sequence-post-deals.drawio`, `deps-routes.drawio`

7. Call `open_drawio_xml` MCP tool with the generated XML

### Output

8. Show the saved file path
9. Show the interactive preview URL from drawio-mcp
10. Brief description of what the diagram shows and key relationships