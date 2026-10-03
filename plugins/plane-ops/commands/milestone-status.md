---
description: Show status and risk for a Plane milestone (release/launch tracking)
argument-hint: <project> [milestone name or id]
---

# Milestone Status

Report the health of a milestone: remaining work, velocity-based ETA, and Red/Yellow/Green risk.

## Arguments

Format: `<project> [milestone name or id]`

Parse from `"$ARGUMENTS"`. If no milestone is specified, list all active milestones with their status.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for the Plane resource tools `project`, `milestone`, `cycle` and `workitem`.
2. **Resolve project and milestone** — `project(action=list)`, then `milestone(action=list, project_id)`.
3. **Load milestone items** — `milestone(action=list_workitems, project_id, milestone_id)` (follow `next_cursor`); state totals in one call: `workitem(action=count, project_id, pql='milestone = "<milestone_id>"', group_by=state__group)`. Points come from the listed items (counts are of items).
4. **Compute metrics** — follow the reporting section of `epics-initiatives-milestones`:
   - `total_points`, `completed_points`, `remaining_points`
   - Weekly velocity from recent cycles (see `velocity-metrics` skill)
   - ETA: `remaining_points / weekly_velocity`
   - Days to `target_date`
5. **Classify risk** per `agile-fundamentals`:
   - Green: ETA + 20% buffer < target_date
   - Yellow: ETA ≤ target_date, buffer < 20%
   - Red: ETA > target_date
6. **Present** — table with milestone name, target, completion, ETA, risk. Highlight red items first.

## Example

```
/milestone-status "TaskFlow"
/milestone-status "TaskFlow" "v2.0 Public Beta"
```

## Output Format

```
| Milestone | Target | Completion | ETA | Risk |
|-----------|--------|-----------|-----|------|
| v2.0 Beta | Apr 30 | 34/52 (65%) | Apr 28 | 🟢 |
| v2.1      | May 15 | 10/48 (21%) | May 22 | 🔴 |
```
