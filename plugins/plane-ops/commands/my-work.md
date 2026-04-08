---
description: List Plane work items assigned to the current user
argument-hint: [--project name] [--state name] [--cycle current|next|all] [--limit n]
---

# My Work

Show open work items assigned to the current user across all projects, or filtered.

## Arguments

Format: `[flags...]`

- `--project <name>`: scope to one project (default: all projects in the workspace)
- `--state <group|name>`: filter (default: anything not in `completed` or `cancelled` group)
- `--cycle current|next|all`: filter by cycle membership (default: all)
- `--priority <p0|p1|p2|...>`
- `--limit <n>`: max items (default 25)
- `--all`: include completed and cancelled

Parse from `"$ARGUMENTS"`.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for `get_me`, `list_projects`, `list_work_items`, `list_cycle_work_items`, `list_states`.
2. **Resolve current user** — `get_me` → `user_id`.
3. **Resolve scope**:
   - if `--project` → that one `project_id`
   - else → `list_projects` → loop over each
4. **Fetch items** — `list_work_items({ project_id, assignees: [user_id], ... })`. If the API does not accept assignee filter, fetch and filter client-side.
5. **Apply filters** — drop completed/cancelled (unless `--all`), apply state/priority/cycle filters. For `--cycle current`, look up the active cycle via `list_cycles({ project_id })` and filter against `list_cycle_work_items`.
6. **Render** — group by project, sort by priority then state. Columns: `ID | Title | State | Priority | Cycle | Updated`.
7. **Show summary** — total items, total story points, breakdown by state, count of overdue.
8. **Suggest** — `/log-time` for items in progress, `/comment add` for items idle >3 days.

## Examples

```
/my-work
/my-work --cycle current
/my-work --project "TaskFlow" --priority p0
/my-work --state "In Review"
/my-work --all --limit 50
```

## Best Practices

- Run this every morning before standup.
- WIP > 3 in-progress items is a red flag (see `agile-fundamentals` WIP limits).
- If the same item shows up day after day with no movement, it's stuck — comment why or ask for help.
