---
description: Manage Plane modules — list, get, update, add items, archive (complement to /create-module)
argument-hint: <action> <project> [args...]
---

# Module

Operate on modules (feature workstreams) beyond creation. For initial creation use `/create-module`.

## Arguments

Format: `<action> <project> [args...]`

- `action`: `list` | `list-archived` | `get` | `update` | `add-items` | `remove-items` | `archive` | `unarchive` | `delete`
- `project`: project name or identifier
- For `get`/`update`/`add-items`/etc: module name or ID
- For `update`: `--name`, `--description`, `--lead <user>`, `--target <date>`, `--status <planned|in-progress|paused|completed|cancelled>`
- For `add-items`/`remove-items`: item identifiers as remaining args

Parse from `"$ARGUMENTS"`.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for `list_modules`, `list_archived_modules`, `retrieve_module`, `update_module`, `delete_module`, `archive_module`, `unarchive_module`, `add_work_items_to_module`, `remove_work_item_from_module`, `list_module_work_items`.
2. **Resolve project** → `project_id`. Resolve module by name when given.
3. **Route**:
   - `list` → render: name | lead | items | state buckets | target | progress
   - `get` → details + items list grouped by state
   - `update` → patch
   - `add-items` / `remove-items` → resolve item UUIDs, call the corresponding tool. Note: `add` typically takes an array; `remove` is often single-item — may need a loop.
   - `archive` / `unarchive` / `delete` → confirm before delete; prefer archive
4. **Confirm** — re-render the module after mutation.

## Modules vs Cycles

| Cycles | Modules |
|---|---|
| time-boxed (sprints) | scope-boxed (features) |
| 1–2 weeks | weeks–months |
| velocity unit | progress unit |
| every item belongs to one cycle | items can belong to multiple modules |

A single feature usually spans 2–4 cycles. Use both: items live in a cycle for *when* and a module for *what*.

## Examples

```
/module list "TaskFlow"
/module get "TaskFlow" "Checkout v2"
/module update "TaskFlow" "Checkout v2" --status in-progress --target 2026-05-30
/module add-items "TaskFlow" "Checkout v2" PROJ-148 PROJ-149 PROJ-150
/module remove-items "TaskFlow" "Checkout v2" PROJ-148
/module archive "TaskFlow" "Old Workstream"
```
