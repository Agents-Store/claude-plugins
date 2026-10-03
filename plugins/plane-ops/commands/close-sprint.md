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

0. **Bootstrap connector** — consult the `connector-bootstrap` skill. Probe `ToolSearch` for the Plane tools (on Plane MCP 0.3+ the `cycle`, `workitem` and `project` resource tools; on legacy connectors the action names referenced below, `list_projects`, `list_cycles`, etc.). Never assume a specific MCP prefix. If multiple Plane instances are connected, ask the user which one to use. All formulas and rules come from the `agile-fundamentals` skill. Calls below are written as resource calls; the legacy action name is in parentheses.

1. **Find active sprint:**
   ```
   cycle(action="list", project_id)                       // legacy: list_cycles
   ```
   Find cycle where today is between start_date and end_date.

2. **Get sprint items:**
   ```
   cycle(action="list_workitems", project_id, cycle_id)   // legacy: list_cycle_work_items
   ```
   Categorize by state group: completed, started, unstarted.

3. **Calculate metrics:**
   - Total points planned
   - Points completed
   - Completion rate (%)
   - Items completed vs total

4. **Present sprint summary:**
   Show completed items, incomplete items, and metrics.

5. **Complete (end) the sprint** — this MUST come before transferring items:
   ```
   cycle(action="complete", project_id, cycle_id)         // legacy: update_cycle({ end_date: today })
   ```
   `complete` sets `end_date` to today. Skip it if the sprint's `end_date` is already today or in the past — keep the recorded end date. The server refuses to transfer work items out of a cycle that has not ended yet.

6. **Handle incomplete items:**
   If --transfer-to specified:
   ```
   cycle(action="list", project_id)                       // find the target cycle by name; create it if missing
   cycle(action="transfer_workitems", project_id, cycle_id, new_cycle_id)   // legacy: transfer_cycle_work_items
   ```
   `transfer_workitems` moves only the unfinished work items; completed ones stay in the closed sprint.

   If --transfer-to is not specified, ask the user what to do with incomplete items.

7. **Archive the sprint:**
   ```
   cycle(action="archive", project_id, cycle_id)          // legacy: archive_cycle
   ```
   Archive comes last. On Plane MCP 0.3+ `archive` ends a still-running cycle by itself, so skipping steps 5-6 would archive the sprint with its unfinished items still inside it; on legacy connectors archiving an active cycle may be rejected with HTTP 400.

8. **Display final summary:**
   Velocity recorded, items transferred (if any), sprint archived.

## Example Usage
```
/close-sprint "TaskFlow"
/close-sprint "My Project" --transfer-to "Sprint 13"
```
