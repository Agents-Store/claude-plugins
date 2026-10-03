---
description: Run a backlog grooming session — refine, estimate, and prioritize
argument-hint: <project> [--limit <n>]
---

# Groom Backlog

Run a structured backlog grooming session: review top items, fill missing details, estimate unestimated ones, and reprioritize.

## Arguments

Format: `<project> [--limit <n>]`

Parse from `"$ARGUMENTS"`. Default limit: top 20 items by priority.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for the Plane resource tools `project`, `workitem` and `workitem_relation`.
2. **Resolve project** — `project(action=list)` → `project_id`.
3. **Load candidate items** — `workitem(action=list, project_id, pql='stateGroup IN ("backlog","unstarted")', per_page=<limit>)`, then sort by priority client-side (follow `next_cursor` only if more are needed).
4. **For each item, check Definition of Ready** (see `agile-fundamentals`):
   - Title and description with acceptance criteria
   - Estimated (points 1–8)
   - No unresolved `blocked_by`
   - Assignable
5. **Fix gaps**:
   - Missing AC → ask user or draft and confirm
   - Unestimated → run `estimation` skill flow
   - Too large (> 8 points) → run `task-decomposition` skill
   - Stale (not updated > 30 days; `workitem(action=list, project_id, pql='stateGroup IN ("backlog","unstarted") AND updatedAt < daysAgo(30)')`) → flag for cancel-then-archive or re-confirm relevance
6. **Reprioritize** — use `backlog-management` (MoSCoW) or run `/wsjf-prioritize` if numeric scoring is needed.
7. **Present grooming summary** — what was refined, estimated, decomposed, archived.

## Example

```
/groom-backlog "TaskFlow"
/groom-backlog "TaskFlow" --limit 30
```

## Cadence

- Weekly: 30–60 min session
- Before every sprint planning: quick pass over top capacity × 1.5 worth of items
