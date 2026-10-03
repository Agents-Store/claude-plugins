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

0. **Bootstrap connector** — consult the `connector-bootstrap` skill. Probe `ToolSearch` for the Plane resource tools referenced below (`project`, `member`, `state`, `cycle`, `workitem`); their names are `mcp__<server>__<resource>`, never assume a specific MCP prefix. If multiple Plane instances are connected, ask the user which one to use. All formulas and rules come from the `agile-fundamentals` skill. Calls are written `resource(action=..., ...)`.

1. **Resolve project:**
   ```
   project(action=list)
   ```
   Find project by name or identifier (follow `next_cursor` if needed). Get project_id.

2. **Get team and context:**
   ```
   member(action=list_project, project_id)
   member(action=me)
   state(action=list, project_id)
   ```
   Count team members. Get current user ID. Map state names to UUIDs.

3. **Calculate velocity:**
   ```
   cycle(action=list, project_id, status=completed)
   ```
   For the last 3-5 completed cycles, sum the completed points:
   ```
   cycle(action=list_workitems, project_id, cycle_id, pql='stateGroup = "completed"', fields="id,point")
   ```
   Calculate average velocity.

4. **Calculate capacity:**
   ```
   With history: capacity = avg_velocity × 0.85
   Without history: capacity = team_size × duration × 0.7 × 0.85
   ```

5. **Select backlog items:**
   ```
   workitem(action=list, project_id, pql='stateGroup IN ("backlog","unstarted")', fields="id,name,point,priority,assignees")
   ```
   Keep items where `point` is set (PQL has no estimate field). Select items by priority until capacity reached.

6. **Present proposed sprint:**
   Show table with items, points, assignees, total vs capacity.
   Suggest sprint goal based on selected items.

7. **On confirmation — create sprint:**
   ```
   cycle(action=create, project_id, name, owned_by, start_date, end_date, description)
   cycle(action=manage_workitems, project_id, cycle_id, add_ids=[...])
   ```

8. **Verify:**
   ```
   cycle(action=list_workitems, project_id, cycle_id)
   ```
   Confirm all items are in the sprint.

## Example Usage
```
/plan-sprint "My Project"
/plan-sprint "TaskFlow" --duration 5 --goal "Launch user authentication"
```
