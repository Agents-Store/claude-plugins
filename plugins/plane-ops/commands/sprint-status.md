---
description: Show current sprint status — progress, burndown, at-risk items
argument-hint: <project>
---

# Sprint Status

Display a dashboard of the current sprint — progress, burndown, WIP, and at-risk items.

## Arguments
Format: `<project>`
- project: Project name or identifier (required)

Parse from "$ARGUMENTS".

## Process

0. **Bootstrap connector** — consult the `connector-bootstrap` skill. Probe `ToolSearch` for the Plane resource tools referenced below (`project`, `member`, `cycle`, `workitem`); their names are `mcp__<server>__<resource>`, never assume a specific MCP prefix. If multiple Plane instances are connected, ask the user which one to use. All formulas and rules come from the `agile-fundamentals` skill. Calls are written `resource(action=..., ...)`.

1. **Find active sprint:**
   ```
   cycle(action=list, project_id, status=current)
   ```
   The cycle where today is between start_date and end_date.

2. **Get sprint details:**
   ```
   cycle(action=retrieve, project_id, cycle_id)
   cycle(action=list_workitems, project_id, cycle_id)
   workitem(action=count, project_id, pql='cycle = "<cycle_id>"', group_by=state__group)
   ```
   The count gives the item totals per state group in one call; the list gives the points.

3. **Calculate burndown:**
   - Total points, completed points, remaining points
   - Sprint days total, days elapsed, days remaining
   - Ideal remaining = total × (remaining_days / total_days)
   - Status: ON TRACK / AT RISK / BEHIND

4. **Check WIP:**
   ```
   member(action=list_project, project_id)
   workitem(action=count, project_id, pql='stateGroup = "started"')
   ```
   WIP limit = team_size × 1.5
   Current WIP = `total_count` of the started items

5. **Identify at-risk items:**
   - Items in "started" state for > 2 days: `cycle(action=list_workitems, project_id, cycle_id, pql='stateGroup = "started" AND updatedAt < daysAgo(2)')`
   - Items not started past mid-sprint: `pql='stateGroup IN ("backlog","unstarted")'`
   - Items past their due date: `pql='isOverdue()'`
   - Items with "blocked_by" relations: `workitem_relation(action=list, project_id, workitem_id)` per open item

6. **Display dashboard:**
   Sprint name, dates, progress bar, burndown status, WIP, at-risk items, per-person summary.

## Example Usage
```
/sprint-status "TaskFlow"
/sprint-status "My Project"
```
