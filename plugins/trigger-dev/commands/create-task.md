---
description: Create a new Trigger.dev task file
argument-hint: <task-name> [--type basic|schema|cron|agent]
allowed-tools: [Read, Write, Edit]
---

# Create Task

1. Parse arguments:
   - `task-name` (required): kebab-case task identifier
   - `--type` (optional, default: basic): basic, schema, cron, agent
2. Determine the task directory from `trigger.config.ts` `dirs` field (default: `src/trigger/`)
3. Create the task file at `<dirs>/<task-name>.ts` using the appropriate template:

**basic**: Simple task with retry config
**schema**: Task with Zod schema validation
**cron**: Scheduled task with cron expression
**agent**: AI agent task with LLM integration

4. Ensure the task is exported
5. Display: "Task created. Run `npx trigger.dev@latest dev` to register it."
