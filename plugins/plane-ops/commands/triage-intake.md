---
description: Triage the Plane intake inbox — accept, defer, or reject incoming items
argument-hint: <project> [--limit <n>]
---

# Triage Intake

Run a triage session over the Plane intake queue for a project.

## Arguments

Format: `<project> [--limit <n>]`

Parse from `"$ARGUMENTS"`. Default limit is 20 items.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for the Plane resource tools `intake`, `project` and `workitem` (the project needs the `intakes` feature).
2. **Resolve project** — `project(action=list)` → `project_id`.
3. **Load intake queue** — `intake(action=list, project_id)` (follow `next_cursor`). Sort by age (oldest first).
4. **Triage each item** — follow the `intake-triage` skill. For each item ask the user (or classify automatically using the routing rules):
   - **Accept** → `intake(action=update, project_id, workitem_id=<the item's issue id>, status=1)`; per Plane's triage model the item becomes a regular backlog work item (the tool description does not say so — confirm on your instance), then complete it with `workitem(action=update, ...)`
   - **Accept + escalate** → `status=1`, then `workitem(action=update, ..., priority="urgent"|"high", assignees=[<on-call>])`
   - **Defer** → `intake(action=update, ..., status=0, snoozed_till=<revisit date as an ISO 8601 timestamp>)` (the tool description gives no format — confirm on your instance) plus a rationale comment (`workitem_comment(action=create)`)
   - **Reject** → `intake(action=update, ..., status=-1)` with a comment explaining why; a duplicate uses `status=2, duplicate_to=<existing work item id>` (id format per the tool description's wording — confirm on your instance). Use `intake(action=delete)` only for spam, after confirmation.
5. **Present session summary** — table of decisions made.
6. **Suggest follow-ups** — items needing more info from the reporter, duplicates to close, deferred items to revisit next grooming.

## Example

```
/triage-intake "TaskFlow"
/triage-intake "TaskFlow" --limit 10
```

## Output Format

```
| # | Item | Age | Decision | Result |
|---|------|-----|----------|--------|
| 1 | "Login 500 Safari" | 2d | Accept+escalate | PROJ-148, urgent, @alice |
| 2 | "Dark mode request" | 5d | Defer | Revisit in 2 sprints |
| 3 | "Same login bug" | 1d | Reject | Duplicate of PROJ-148 |
```

See the `intake-triage` skill for routing rules and cadence recommendations.
