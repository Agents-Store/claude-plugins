---
description: Initialize Trigger.dev in your project
allowed-tools: mcp__trigger_dev__tds-list_orgs, mcp__trigger_dev__tds-initialize_project, mcp__trigger_dev__tds-get_current_worker
argument-hint: [project-name]
---

# Initialize Project

Set up Trigger.dev in the current project directory.

## Arguments
- project-name: Name for the new Trigger.dev project (optional, will prompt)

## Process

1. **List organizations:**
   ```
   tds-list_orgs()
   ```
   If multiple orgs, ask the user which one to use.

2. **Initialize project:**
   ```
   tds-initialize_project(
     orgParam=<selected_org>,
     projectName="$ARGUMENTS" or ask user,
     cwd=<current_working_directory>
   )
   ```

3. **Verify setup:**
   ```
   tds-get_current_worker(environment="dev")
   ```

4. **Report result:**
   - Show created files (trigger.config.ts, example task)
   - Show project ref
   - Remind to run `npx trigger.dev@latest dev` to start dev server

## Example Usage
```
/init-project my-background-jobs
/init-project
```

## Notes
- Only run if no trigger.config.ts exists yet
- Requires authenticated Trigger.dev account
- Creates src/trigger/ directory with example task
