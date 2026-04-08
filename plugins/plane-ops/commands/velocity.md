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

0. **Bootstrap connector** — consult the `connector-bootstrap` skill. Probe `ToolSearch` for the action names referenced below (`list_projects`, `list_cycles`, etc.). Match tools by action suffix — never assume a specific MCP prefix. If multiple Plane instances are connected, ask the user which one to use. All formulas and rules come from the `agile-fundamentals` skill.

1. **Resolve project:**
   ```
   list_projects()
   ```

2. **Get completed sprints:**
   ```
   list_archived_cycles({ project_id })
   ```
   Take last N archived cycles (sorted by end_date descending).

3. **Calculate velocity per sprint:**
   For each cycle:
   ```
   list_cycle_work_items({ project_id, cycle_id })
   ```
   Sum points of items in "completed" state group.
   Also sum total planned points.

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
