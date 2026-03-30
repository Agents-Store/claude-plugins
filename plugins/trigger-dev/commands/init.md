---
description: Initialize Trigger.dev in the current project
argument-hint: [--self-hosted <url>]
allowed-tools: [Read, Write, Edit, Bash]
---

# Initialize Trigger.dev

1. Check if `trigger.config.ts` already exists in the project root
2. If `--self-hosted` argument is provided, run:
   ```bash
   npx trigger.dev@latest init -a <url>
   ```
   Otherwise run:
   ```bash
   npx trigger.dev@latest init
   ```
3. Verify `trigger.config.ts` was created
4. Verify `src/trigger/` directory exists with an example task
5. Check that `@trigger.dev/sdk` is in `package.json` dependencies
6. If self-hosted, ensure `.env` has `TRIGGER_API_URL` and `TRIGGER_SECRET_KEY`
7. Display next steps: "Run `npx trigger.dev@latest dev` to start the dev server"
