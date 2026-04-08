---
description: Plan a new sprint — calculate capacity, select items from backlog, set sprint goal
argument-hint: <project> [--duration <days>] [--goal <sprint goal>]
---

# Plan Sprint

Run a complete sprint planning ceremony — capacity calculation, backlog selection, and sprint creation.

## Arguments
Format: `<project> [--duration <days>] [--goal <sprint goal>]`
- project: Project name or identifier (required)
- --duration: Sprint length in days (default: 5)
- --goal: Sprint goal description (optional, will be suggested)

Parse from "$ARGUMENTS".

## Process

0. **Bootstrap connector** — consult the `connector-bootstrap` skill. Probe `ToolSearch` for the action names referenced below (`list_projects`, `list_cycles`, etc.). Match tools by action suffix — never assume a specific MCP prefix. If multiple Plane instances are connected, ask the user which one to use. All formulas and rules come from the `agile-fundamentals` skill.

1. **Resolve project:**
   ```
   list_projects()
   ```
   Find project by name or identifier. Get project_id.

2. **Get team and context:**
   ```
   get_project_members({ project_id })
   get_me()
   list_states({ project_id })
   ```
   Count team members. Get current user ID. Map state names to UUIDs.

3. **Calculate velocity:**
   ```
   list_archived_cycles({ project_id })
   ```
   For last 3-5 archived cycles, get work items and sum completed points.
   Calculate average velocity.

4. **Calculate capacity:**
   ```
   With history: capacity = avg_velocity × 0.85
   Without history: capacity = team_size × duration × 0.7 × 0.85
   ```

5. **Select backlog items:**
   ```
   list_work_items({ project_id, order_by: "-priority" })
   ```
   Filter: state group = backlog/unstarted, point is set.
   Select items by priority until capacity reached.

6. **Present proposed sprint:**
   Show table with items, points, assignees, total vs capacity.
   Suggest sprint goal based on selected items.

7. **On confirmation — create sprint:**
   ```
   create_cycle({ project_id, name, owned_by, start_date, end_date, description })
   add_work_items_to_cycle({ project_id, cycle_id, issue_ids })
   ```

8. **Verify:**
   ```
   list_cycle_work_items({ project_id, cycle_id })
   ```
   Confirm all items are in the sprint.

## Example Usage
```
/plan-sprint "My Project"
/plan-sprint "TaskFlow" --duration 5 --goal "Launch user authentication"
```
