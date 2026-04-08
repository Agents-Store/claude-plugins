---
description: Create, update, or inspect a work item (issue/task/ticket) in Plane
argument-hint: <action> <project> [args...]
---

# Work Item

Create, update, or inspect a single work item in Plane. Delegates all tool resolution to the `connector-bootstrap` skill and all field rules to the `work-items` skill.

## Arguments

Format: `<action> <project> [args...]`

- `action`: one of `create`, `update`, `get`, `search`, `comment`, `link`, `log-time`, `block`
- `project`: project name or identifier
- Remaining args depend on action (see examples)

Parse from `"$ARGUMENTS"`.

## Process

1. **Bootstrap connector** — consult the `connector-bootstrap` skill. Probe `ToolSearch` for work item actions (`create_work_item`, `update_work_item`, `search_work_items`, `retrieve_work_item_by_identifier`) before assuming anything. If multiple Plane instances are connected, ask the user which one.

2. **Resolve project** — `list_projects` → pick `project_id` by name or identifier.

3. **Route by action** — follow the matching section of the `work-items` skill:
   - `create` → gather title, description with AC, priority, points, assignees, labels; call `create_work_item` (check schema for `state`/`state_id` and `labels`/`label_ids` field names)
   - `update` → resolve work item ID, apply field changes via `update_work_item`
   - `get` → when the user passes a human identifier like `PROJ-42`, split into project slug `PROJ` and integer `42`, then call `retrieve_work_item_by_identifier({ project_identifier, issue_identifier })`. For UUIDs, use `retrieve_work_item({ project_id, work_item_id })`.
   - `search` → `search_work_items({ query })` — typically workspace-scoped, filter by project client-side if needed
   - `comment` → `create_work_item_comment`
   - `link` → `create_work_item_link` (PRs, docs, designs)
   - `log-time` → `create_work_log` with duration as **integer minutes** (convert "2h 30m" → 150); project must have `is_time_tracking_enabled`
   - `block` → `create_work_item_relation` with `relation_type: "blocked_by"` and `issues: [uuid]` (array, plural — not `related_issue`)

4. **Validate** — before creating or committing to a sprint, verify the Definition of Ready from the `agile-fundamentals` skill.

5. **Confirm** — print a short summary of what was created/changed and the item identifier.

## Examples

```
/work-item create "TaskFlow" "Fix login 500 on Safari" --priority high --points 3 --labels bug
/work-item update "TaskFlow" PROJ-148 --state "In Progress" --assignee alice
/work-item get "TaskFlow" PROJ-148
/work-item search "TaskFlow" "login bug"
/work-item comment "TaskFlow" PROJ-148 "Reproduced on Safari 17, investigating"
/work-item link "TaskFlow" PROJ-148 https://github.com/org/repo/pull/420 "PR #420"
/work-item log-time "TaskFlow" PROJ-148 PT2H30M "Debug + fix"
/work-item block "TaskFlow" PROJ-148 PROJ-140
```
