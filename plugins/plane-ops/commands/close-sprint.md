---
description: Close current sprint — review completion, transfer incomplete items, archive
argument-hint: <project> [--transfer-to <next-cycle-name>]
---

# Close Sprint

Close the active sprint — review completion metrics, handle incomplete items, and archive.

## Arguments
Format: `<project> [--transfer-to <next-cycle-name>]`
- project: Project name or identifier (required)
- --transfer-to: Name of next sprint to transfer incomplete items (optional)

Parse from "$ARGUMENTS".

## Process

0. **Bootstrap connector** — consult the `connector-bootstrap` skill. Probe `ToolSearch` for the action names referenced below (`list_projects`, `list_cycles`, etc.). Match tools by action suffix — never assume a specific MCP prefix. If multiple Plane instances are connected, ask the user which one to use. All formulas and rules come from the `agile-fundamentals` skill.

1. **Find active sprint:**
   ```
   list_cycles({ project_id })
   ```
   Find cycle where today is between start_date and end_date.

2. **Get sprint items:**
   ```
   list_cycle_work_items({ project_id, cycle_id })
   ```
   Categorize by state group: completed, started, unstarted.

3. **Calculate metrics:**
   - Total points planned
   - Points completed
   - Completion rate (%)
   - Items completed vs total

4. **Present sprint summary:**
   Show completed items, incomplete items, and metrics.

5. **Handle incomplete items:**
   If --transfer-to specified:
   ```
   list_cycles({ project_id })  // find or create target cycle
   transfer_cycle_work_items({ project_id, cycle_id, new_cycle_id })
   ```
   Otherwise, ask user what to do with incomplete items.

6. **Archive the sprint:**
   ```
   archive_cycle({ project_id, cycle_id })
   ```

7. **Display final summary:**
   Velocity recorded, items transferred (if any), sprint archived.

## Example Usage
```
/close-sprint "TaskFlow"
/close-sprint "My Project" --transfer-to "Sprint 13"
```
