---
description: Manage Plane milestones — create, list, add items, update, delete
argument-hint: <action> <project> [args...]
---

# Milestone

Create and manage milestones (release markers) on a Plane project. For status/risk reporting on an existing milestone use `/milestone-status`.

## Arguments

Format: `<action> <project> [args...]`

- `action`: `create` | `list` | `get` | `update` | `delete` | `add-items` | `remove-items`
- `project`: project name or identifier
- For `create`: `--name`, `--target <date>`, `--description`
- For `add-items`/`remove-items`: `--milestone <name>`, item IDs as remaining args

Parse from `"$ARGUMENTS"`.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for `create_milestone`, `list_milestones`, `retrieve_milestone`, `update_milestone`, `delete_milestone`, `add_work_items_to_milestone`, `remove_work_items_from_milestone`, `list_milestone_work_items`.
2. **Resolve project** → `project_id`.
3. **Route**:
   - `create` → gather name + target date (required) + description. Call `create_milestone`. Reject milestones >6 months out — split into two.
   - `list` → `list_milestones({ project_id })`, render with item count and target date.
   - `get` → `retrieve_milestone` + `list_milestone_work_items`. Render scope and aggregate state buckets.
   - `update` → resolve by name → `update_milestone`. Moving the target date is a **trade-off conversation** — reduce scope first, slip date last (see `epics-initiatives-milestones` skill).
   - `delete` → confirm. Items are unlinked, not deleted.
   - `add-items` / `remove-items` → resolve item IDs → `add_work_items_to_milestone({ milestone_id, work_item_ids: [...] })`.
4. **Confirm** — print milestone ID, target date, and item count.

## Examples

```
/milestone create "TaskFlow" --name "v2.0 Public Beta" --target 2026-06-15
/milestone list "TaskFlow"
/milestone get "TaskFlow" "v2.0 Public Beta"
/milestone add-items "TaskFlow" --milestone "v2.0 Public Beta" PROJ-148 PROJ-150 PROJ-151
/milestone update "TaskFlow" "v2.0 Public Beta" --target 2026-06-22
/milestone remove-items "TaskFlow" --milestone "v2.0 Public Beta" PROJ-160
```

## Best Practices

- Every milestone needs a **single owner** (the release manager).
- Lock the milestone scope at T-2 weeks. Add-items after lock requires removing equivalent points.
- Pair `/milestone create` with a Plane page (`/page create project ... --from-template milestone-update`) and link them in the milestone description.
- Use `/milestone-status` weekly during the run-up to track risk.
