---
description: Manage Plane cycles beyond planning — list, archive, transfer, delete
argument-hint: <action> <project> [args...]
---

# Cycles

Operate on cycles (sprints) beyond create/plan/close. For sprint planning use `/plan-sprint` and `/create-sprint`; for status use `/sprint-status`; for closing use `/close-sprint`.

## Arguments

Format: `<action> <project> [args...]`

- `action`: `list` | `list-archived` | `get` | `archive` | `unarchive` | `transfer` | `delete` | `update`
- `project`: project name or identifier
- For `get`/`archive`/`unarchive`/`delete`: cycle name or ID
- For `transfer`: `--from <cycle>` `--to <cycle>` (incomplete items only by default; `--all` for everything)
- For `update`: `--name`, `--description`, `--start <date>`, `--end <date>`

Parse from `"$ARGUMENTS"`.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for `list_cycles`, `list_archived_cycles`, `retrieve_cycle`, `update_cycle`, `delete_cycle`, `archive_cycle`, `unarchive_cycle`, `transfer_cycle_work_items`, `list_cycle_work_items`.
2. **Resolve project** → `project_id`.
3. **Route**:
   - `list` → `list_cycles`. Render with: name | state (upcoming/current/completed) | dates | items | progress.
   - `list-archived` → `list_archived_cycles`.
   - `get` → `retrieve_cycle` + `list_cycle_work_items`. Show metrics.
   - `archive` → confirm. Archived cycles disappear from default views but remain queryable.
   - `unarchive` → restore.
   - `transfer` → resolve both cycles. By default, transfer only items NOT in a `completed` group state. Call `transfer_cycle_work_items({ from_cycle_id, to_cycle_id, work_item_ids })`. Print count moved.
   - `delete` → **destructive**, confirm twice. Items lose cycle assignment but are not deleted. Prefer `archive` over `delete`.
   - `update` → resolve cycle → `update_cycle`. Changing dates of an active cycle distorts velocity history — warn the user.
4. **Confirm** — re-list after mutation.

## Examples

```
/cycles list "TaskFlow"
/cycles list-archived "TaskFlow"
/cycles get "TaskFlow" "Sprint 14"
/cycles transfer "TaskFlow" --from "Sprint 14" --to "Sprint 15"
/cycles archive "TaskFlow" "Sprint 10"
/cycles update "TaskFlow" "Sprint 15" --end 2026-04-25
/cycles delete "TaskFlow" "Sprint 09"
```

## Best Practices

- **Archive completed cycles after retro** — keeps the active list clean while preserving velocity data.
- Don't use `delete` to "redo" a sprint — historical data is gold for velocity. Archive instead.
- `transfer` should be the LAST step of a sprint close, after retro, not the first.
