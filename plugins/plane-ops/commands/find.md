---
description: Search Plane work items by query, identifier, or filter
argument-hint: <query> [--project name] [--state name] [--assignee user] [--label name]
---

# Find

Quick search for Plane work items. Accepts a free-text query, an identifier (`PROJ-42`), or filter flags.

## Arguments

Format: `<query> [flags...]`

- `query`: free text, OR an identifier like `PROJ-42`, OR omit when using only filters
- `--project <name>`: scope to a project
- `--state <name>`: filter by state (e.g. "In Progress")
- `--assignee <user>`: filter by assignee (or `me`)
- `--label <name>`: filter by label
- `--limit <n>`: max results (default 20)

Parse from `"$ARGUMENTS"`.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for `search_work_items`, `retrieve_work_item_by_identifier`, `list_work_items`, `get_workspace_members`, `get_me`.
2. **Detect identifier shortcut** — if the query matches `^[A-Z][A-Z0-9]+-\d+$`, split into project slug + integer and call `retrieve_work_item_by_identifier` directly. Render the full item and stop.
3. **Free-text path** — call `search_work_items({ query })` (workspace-scoped on most builds). If a `--project` is given and the API doesn't support project filter, post-filter results client-side.
4. **Filter-only path** — if no query but flags are present, use `list_work_items` with filter parameters.
5. **Apply remaining filters** client-side (state, assignee, label) — these are not always supported by `search_work_items`.
6. **Render** — table with columns: `ID | Title | State | Assignee | Updated`. Truncate titles at 60 chars. Show top `--limit` results.
7. **Suggest next actions** — for any single result, hint at `/work-item get`, `/comment add`, `/assign`.

## Examples

```
/find "login bug"
/find PROJ-148
/find --assignee me --state "In Progress"
/find "checkout" --project "TaskFlow" --label type/bug
/find --label priority/p0 --limit 5
```

## Best Practices

- For frequently-used filters (e.g. "my open p0 bugs"), save them as a Plane view and reference the view name in `/find` instead.
- Search is full-text over title and description on most Plane builds — comments are usually NOT indexed.
- If results feel stale, the workspace search index may be lagging — fall back to `list_work_items` with explicit filters.
