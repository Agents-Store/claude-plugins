---
description: Calculate team velocity from historical sprint data
argument-hint: <project> [--sprints <count>]
---

# Velocity

Calculate team velocity from completed sprints and show trend analysis.

## Arguments
Format: `<project> [--sprints <count>]`
- project: Project name or identifier (required)
- --sprints: Number of past sprints to analyze (default: 5)

Parse from "$ARGUMENTS".

## Process

0. **Bootstrap connector** — consult the `connector-bootstrap` skill. Probe `ToolSearch` for the Plane resource tools referenced below (`project`, `cycle`, `workitem`); their names are `mcp__<server>__<resource>`, never assume a specific MCP prefix. If multiple Plane instances are connected, ask the user which one to use. All formulas and rules come from the `agile-fundamentals` skill. Calls are written `resource(action=..., ...)`.

1. **Resolve project:**
   ```
   project(action=list)
   ```

2. **Get completed sprints:**
   ```
   cycle(action=list, project_id, status=completed)
   ```
   Take last N completed cycles (sorted by end_date descending). Sprints that are already archived: `cycle(action=list, project_id, archived=true)` (`status` is ignored then).

3. **Calculate velocity per sprint:**
   For each cycle:
   ```
   cycle(action=list_workitems, project_id, cycle_id, pql='stateGroup = "completed"', fields="id,point")
   cycle(action=list_workitems, project_id, cycle_id, fields="id,point")
   ```
   Sum `point` of the completed items (first call) and of all items (second call, total planned). Items finished per sprint for all completed cycles in one call: `workitem(action=count, project_id, pql='cycle IN completedCycles() AND stateGroup = "completed"', group_by=cycle_id)`.

4. **Calculate aggregates:**
   - Average velocity
   - Min/max range
   - Average completion rate
   - Trend (improving/stable/declining)

5. **Display velocity report:**
   ```
   | Sprint | Planned | Completed | Rate |
   |--------|---------|-----------|------|
   | Sprint 11 | 40 | 36 | 90% |
   | Sprint 10 | 38 | 32 | 84% |
   | ...

   Average velocity: 33 pts/sprint
   Range: 28-36 pts
   Completion rate: 86%
   Trend: Stable
   Recommended next sprint: ~28 pts (velocity × 0.85 buffer)
   ```

## Example Usage
```
/velocity "TaskFlow"
/velocity "My Project" --sprints 10
```
