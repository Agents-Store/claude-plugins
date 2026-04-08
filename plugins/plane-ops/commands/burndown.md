---
description: Show sprint burndown and projected completion for the active cycle
argument-hint: <project> [--cycle <current|name>]
---

# Burndown

Compute a burndown view for a sprint: ideal line, actual points remaining, and projected end state.

## Arguments

Format: `<project> [--cycle <current|name>]`

Parse from `"$ARGUMENTS"`. Default: current cycle.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for `list_cycles`, `list_cycle_work_items`, `list_work_item_activities`.
2. **Resolve project and cycle** — `list_projects` → `list_cycles({ project_id })` → active cycle (or named).
3. **Load cycle items** — `list_cycle_work_items({ project_id, cycle_id })`.
4. **Reconstruct daily points remaining** — for each day from `start_date` to today, sum points of items not in a completed state group as of that day. Use `list_work_item_activities` to find state transitions, or fall back to current snapshot if activity data is unavailable.
5. **Compute**:
   - `total_points` = sum of all cycle item points
   - `completed_points` = sum of items in completed state group
   - `remaining_points` = `total_points − completed_points`
   - `ideal_remaining(day)` = `total_points × (1 − day / total_days)`
   - `projected_end_points` = linear extrapolation from the last 3 days of actual burn
   - `on_track` = `projected_end_points ≤ 0`
6. **Present** — ASCII or markdown table with day, ideal, actual, delta. Highlight if the team is ahead/behind and by how much.
7. **Recommend** — if off track by > 20%, suggest scope reduction (see `sprint-planning` on transferring items).

## Example

```
/burndown "TaskFlow"
/burndown "TaskFlow" --cycle "Sprint 15"
```

## Output Format

```
Sprint 14 — Billing v2 (day 6 of 10)
Total: 40 pts · Completed: 22 · Remaining: 18 · Ideal: 16
Status: 🟡 2 pts behind ideal · Projected end: 30/40 (75%)

Day | Ideal | Actual | Delta
  0 |   40  |   40   |   0
  1 |   36  |   38   |  +2
  …
```
