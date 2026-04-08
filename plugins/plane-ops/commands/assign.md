---
description: Assign or unassign a Plane work item to one or more users
argument-hint: <project> <item> <assignee> [more...]
---

# Assign

Assign a work item in Plane to one or more users. Replaces or appends depending on flags.

## Arguments

Format: `<project> <item> <assignee> [more...]`

- `project`: project name or identifier
- `item`: work item identifier (`PROJ-42`) or UUID
- `assignee`: username, email, display name, or `me`
- Additional assignees space-separated for multi-assign
- Flags: `--replace` (default: append), `--unassign <user>`, `--clear` (remove all)

Parse from `"$ARGUMENTS"`.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for `update_work_item`, `get_workspace_members`, `get_project_members`, `get_me`.
2. **Resolve project** → `project_id`. **Resolve work item** → `work_item_id` (and current `assignee_ids`).
3. **Resolve users**:
   - `me` → `get_me` → user_id
   - else → `get_project_members({ project_id })` and match by `display_name`, `email`, or `username` (case-insensitive). If no project member matches, fall back to `get_workspace_members`. If still ambiguous, ask the user to choose.
4. **Compute new `assignee_ids`**:
   - default → union(current, new)
   - `--replace` → just the new set
   - `--unassign <user>` → current minus that user
   - `--clear` → empty array
5. **Update** — `update_work_item({ project_id, work_item_id, assignee_ids })`. Note: some Plane builds use `assignees` instead — check schema.
6. **Confirm** — print final assignee list and item identifier.

## Examples

```
/assign "TaskFlow" PROJ-148 alice
/assign "TaskFlow" PROJ-148 me
/assign "TaskFlow" PROJ-148 alice bob --replace
/assign "TaskFlow" PROJ-148 --unassign bob
/assign "TaskFlow" PROJ-148 --clear
```

## Best Practices

- Prefer **single assignee** for accountability. Multi-assign blurs ownership — use it only for pairing or review handoff.
- Don't assign before the item meets Definition of Ready (see `agile-fundamentals` skill).
- When unassigning yourself, leave a comment with handoff context (`/comment add ...`).
