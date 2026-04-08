---
description: Generate daily standup summary for current sprint
argument-hint: <project>
---

# Standup

Generate a daily standup summary — per-person status, sprint progress, and blockers.

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

2. **Get sprint items and team:**
   ```
   list_cycle_work_items({ project_id, cycle_id })
   get_project_members({ project_id })
   ```

3. **Group items by assignee and state:**
   For each team member:
   - Completed: items in "completed" state group
   - In Progress: items in "started" state group
   - Not Started: items in "unstarted" state group

4. **Detect blockers:**
   For in-progress items, check:
   ```
   list_work_item_relations({ project_id, work_item_id })
   ```
   Flag items with "blocked_by" relations.

5. **Calculate sprint progress:**
   - Total/completed/remaining points
   - Days elapsed and remaining
   - Pace vs needed pace
   - WIP count vs limit

6. **Display standup report:**
   Per-person summary (done, doing, blocked) + team-level sprint progress.

## Example Usage
```
/standup "TaskFlow"
/standup "My Project"
```
