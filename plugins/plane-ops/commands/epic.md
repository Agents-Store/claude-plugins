---
description: Manage Plane epics — list, get, update, delete (complement to /create-epic)
argument-hint: <action> <project> [args...]
---

# Epic

Operate on epics beyond creation. For creation use `/create-epic`. For breaking an epic into stories use `/decompose`.

## Arguments

Format: `<action> <project> [args...]`

- `action`: `list` | `get` | `update` | `delete` | `status`
- `project`: project name or identifier
- For `get`/`update`/`status`/`delete`: epic name or ID
- For `update`: `--name`, `--description`, `--lead <user>`, `--target <date>`, `--initiative <name>`

Parse from `"$ARGUMENTS"`.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for `list_epics`, `retrieve_epic`, `update_epic`, `delete_epic`. Note: child items of an epic are work items with `parent_id = epic_id`.
2. **Resolve project** → `project_id`.
3. **Route**:
   - `list` → render: name | lead | child count | state buckets | target | progress %.
   - `get` → details + child items grouped by state. Show progress as `(completed_points / total_points)` and as `(completed_count / total_count)`.
   - `status` → same as get but compact and emphasizes RAG (Red/Amber/Green) based on points completed vs time elapsed (see `epics-initiatives-milestones` skill).
   - `update` → patch. Linking to an initiative goes through this (`--initiative` → resolve initiative ID → set `initiative_id`).
   - `delete` → confirm. Children are unlinked, not deleted.
4. **Confirm** — re-render after mutation.

## Examples

```
/epic list "TaskFlow"
/epic get "TaskFlow" "Checkout Rewrite"
/epic status "TaskFlow" "Checkout Rewrite"
/epic update "TaskFlow" "Checkout Rewrite" --target 2026-06-30 --lead alice
/epic delete "TaskFlow" "Cancelled Idea"
```

## Best Practices

- Every epic needs an **outcome statement** in its description (not just a feature list). E.g. "Customers can complete checkout in <30s on mobile" — this is the success criterion.
- Epic health check: if an epic has been "in progress" for >3 cycles with <50% completion, rescope or split.
- Pair epics with a tracking page (`/page create project ... --from-template spec`) and link from the epic description.
