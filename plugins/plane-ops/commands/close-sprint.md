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

0. **Bootstrap connector** — consult the `connector-bootstrap` skill. Probe `ToolSearch` for the Plane resource tools referenced below (`project`, `cycle`, `workitem`); their names are `mcp__<server>__<resource>`, never assume a specific MCP prefix. If multiple Plane instances are connected, ask the user which one to use. All formulas and rules come from the `agile-fundamentals` skill. Calls are written `resource(action=..., ...)`.

1. **Find active sprint:**
   ```
   cycle(action=list, project_id, status=current)
   ```
   The cycle where today is between start_date and end_date.

2. **Get sprint items:**
   ```
   cycle(action=list_workitems, project_id, cycle_id)
   workitem(action=count, project_id, pql='cycle = "<cycle_id>"', group_by=state__group)
   ```
   Categorize by state group: completed, started, unstarted (the count gives the totals in one call, the list gives the points).

3. **Calculate metrics:**
   - Total points planned
   - Points completed
   - Completion rate (%)
   - Items completed vs total

4. **Present sprint summary:**
   Show completed items, incomplete items, and metrics.

5. **Complete (end) the sprint** — this MUST come before transferring items:
   ```
   cycle(action=complete, project_id, cycle_id)
   ```
   `complete` sets `end_date` to today. Skip it if the sprint's `end_date` is already today or in the past — keep the recorded end date. The server refuses to transfer work items out of a cycle that has not ended yet.

6. **Handle incomplete items:**
   If --transfer-to specified:
   ```
   cycle(action=list, project_id)                       // find the target cycle by name; create it (cycle(action=create)) if missing
   cycle(action=transfer_workitems, project_id, cycle_id, new_cycle_id)
   ```
   `transfer_workitems` moves only the unfinished work items; completed ones stay in the closed sprint. To send some unfinished items back to the backlog instead, take them out first with `cycle(action=manage_workitems, project_id, cycle_id, remove_ids=[...])`.

   If --transfer-to is not specified, ask the user what to do with incomplete items.

7. **Archive the sprint:**
   ```
   cycle(action=archive, project_id, cycle_id)
   ```
   Archive comes last. `archive` ends a still-running cycle by itself, so skipping steps 5-6 would archive the sprint with its unfinished items still inside it.

8. **Display final summary:**
   Velocity recorded, items transferred (if any), sprint archived.

## Example Usage
```
/close-sprint "TaskFlow"
/close-sprint "My Project" --transfer-to "Sprint 13"
```
