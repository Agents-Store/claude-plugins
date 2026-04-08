---
description: Create a new sprint cycle in Plane
argument-hint: <project> <name> --start <YYYY-MM-DD> --end <YYYY-MM-DD>
---

# Create Sprint

Quickly create a new sprint cycle with specified dates.

## Arguments
Format: `<project> <name> --start <YYYY-MM-DD> --end <YYYY-MM-DD>`
- project: Project name or identifier (required)
- name: Sprint name (required)
- --start: Start date in ISO format (required)
- --end: End date in ISO format (required)

Parse from "$ARGUMENTS".

## Process

0. **Bootstrap connector** — consult the `connector-bootstrap` skill. Probe `ToolSearch` for the action names referenced below (`list_projects`, `list_cycles`, etc.). Match tools by action suffix — never assume a specific MCP prefix. If multiple Plane instances are connected, ask the user which one to use. All formulas and rules come from the `agile-fundamentals` skill.

1. **Resolve project:**
   ```
   list_projects()
   ```
   Find project by name or identifier.

2. **Get current user:**
   ```
   get_me()
   ```
   Get user UUID for owned_by field.

3. **Create the cycle:**
   ```
   create_cycle({
     project_id, name, owned_by,
     start_date, end_date
   })
   ```

4. **Display result:**
   Show created sprint name, dates, and ID.
   Suggest next step: "Add items with /plan-sprint or manually."

## Example Usage
```
/create-sprint "TaskFlow" "Sprint 12" --start 2025-03-17 --end 2025-03-21
/create-sprint "My Project" "Sprint 5 — Auth" --start 2025-03-10 --end 2025-03-14
```
