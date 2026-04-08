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

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for `list_intake_work_items`, `retrieve_intake_work_item`, `create_work_item`.
2. **Resolve project** — `list_projects` → `project_id`.
3. **Load intake queue** — `list_intake_work_items({ project_id })`. Sort by age (oldest first).
4. **Triage each item** — follow the `intake-triage` skill. For each item ask the user (or classify automatically using the routing rules):
   - **Accept** → convert to work item in the backlog
   - **Accept + escalate** → create work item, set urgent/high, assign on-call
   - **Defer** → mark with rationale and revisit date
   - **Reject** → delete with a comment
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
