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

0. **Bootstrap connector** — consult the `connector-bootstrap` skill. Probe `ToolSearch` for the action names referenced below (`list_projects`, `list_cycles`, etc.). Match tools by action suffix — never assume a specific MCP prefix. If multiple Plane instances are connected, ask the user which one to use. All formulas and rules come from the `agile-fundamentals` skill.

1. **Find active sprint:**
   ```
   list_cycles({ project_id })
   ```
   Find cycle where today is between start_date and end_date.

2. **Get sprint details:**
   ```
   retrieve_cycle({ project_id, cycle_id })
   list_cycle_work_items({ project_id, cycle_id })
   ```

3. **Calculate burndown:**
   - Total points, completed points, remaining points
   - Sprint days total, days elapsed, days remaining
   - Ideal remaining = total × (remaining_days / total_days)
   - Status: ON TRACK / AT RISK / BEHIND

4. **Check WIP:**
   ```
   get_project_members({ project_id })
   ```
   WIP limit = team_size × 1.5
   Current WIP = items in "started" state

5. **Identify at-risk items:**
   - Items in "started" state for > 2 days
   - Items not started past mid-sprint
   - Items with "blocked_by" relations

6. **Display dashboard:**
   Sprint name, dates, progress bar, burndown status, WIP, at-risk items, per-person summary.

## Example Usage
```
/sprint-status "TaskFlow"
/sprint-status "My Project"
```
