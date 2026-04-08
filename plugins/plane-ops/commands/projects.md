---
description: List, inspect, update, or delete Plane projects (complement to /setup-project)
argument-hint: <action> [args...]
---

# Projects

Operate on Plane projects. For initial creation with Agile defaults use `/setup-project`.

## Arguments

Format: `<action> [args...]`

- `action`: `list` | `get` | `update` | `delete` | `features`
- For `get`/`update`/`delete`/`features`: project name or identifier
- For `update`: `--name`, `--identifier <SLUG>`, `--description`, `--icon`, `--lead <user>`, `--default-assignee <user>`
- For `features`: `--enable cycles,modules,issues,inbox,pages,views` or `--disable ...`

Parse from `"$ARGUMENTS"`.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for `list_projects`, `retrieve_project`, `update_project`, `delete_project`, `get_project_features`, `update_project_features`, `get_project_members`.
2. **Route**:
   - `list` → render: identifier | name | lead | members | cycles? | modules? | last activity. Highlight archived.
   - `get` → details + member count + active cycle/module count.
   - `update` → patch. Changing `identifier` rewrites all work item IDs (`OLD-42` → `NEW-42`) — warn loudly before doing this.
   - `delete` → **destructive**. Confirm with project name typed back. Suggest archive in UI as the safer alternative.
   - `features` → `get_project_features` first, show current state, then `update_project_features`. Common flags: cycles, modules, issues, inbox (intake), pages, views, time-tracking.
3. **Confirm** — print result.

## Examples

```
/projects list
/projects get "TaskFlow"
/projects update "TaskFlow" --lead alice --description "Customer-facing checkout app"
/projects features "TaskFlow" --enable inbox,pages,modules
/projects delete "Old Sandbox"
```

## Best Practices

- Don't rename project `identifier` after launch — every existing reference (commits, PR titles, Slack threads) breaks.
- Disable unused features — clutter in the sidebar slows everyone down. Most teams need: cycles, modules, pages, views.
- Use `/projects features` to enable `inbox` (intake) before running `/triage-intake`.
