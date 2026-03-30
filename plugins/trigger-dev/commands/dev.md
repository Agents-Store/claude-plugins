---
description: Start the Trigger.dev dev server
argument-hint: [--profile <name>]
allowed-tools: [Bash]
---

# Start Dev Server

1. Verify `trigger.config.ts` exists in the project
2. Build the dev command:
   - Base: `npx trigger.dev@latest dev`
   - If `--profile` argument: add `--profile <name>`
   - If monorepo detected: add `--config <path-to-trigger.config.ts>`
3. Run the command
4. The dev server will watch for file changes and register tasks with the dev environment
