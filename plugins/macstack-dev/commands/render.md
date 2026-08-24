---
description: Rebuild the generated macstack documents — ROLES.md, ARCHITECTURE.md, README.md
---

Use the `macstack-dev:render-docs` skill on the project at $ARGUMENTS (default: current
directory). Rebuild the documents whose source of truth is `macstack.json`, not themselves.
Run the renderer, report which files changed, and if anything changed remind the user that a
journal row was appended. Do not hand-edit the rendered files; if the output looks wrong, the
fix belongs in the spec or in the renderer.
