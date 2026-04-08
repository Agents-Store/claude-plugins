---
description: Manage Plane workflow states — list, create, update, delete, reorder
argument-hint: <action> <project> [args...]
---

# State

Manage workflow states (the columns on a board) for a Plane project.

## Arguments

Format: `<action> <project> [args...]`

- `action`: `list` | `create` | `update` | `delete`
- `project`: project name or identifier
- For `create`/`update`: `--name`, `--group <backlog|unstarted|started|completed|cancelled>`, `--color #hex`, `--sequence <int>`, `--default`

Parse from `"$ARGUMENTS"`.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for `list_states`, `create_state`, `update_state`, `delete_state`, `retrieve_state`.
2. **Resolve project** → `project_id`.
3. **Route**:
   - `list` → `list_states({ project_id })`. Render grouped by `group`, sorted by `sequence`. Mark the default state.
   - `create` → require `--name` and `--group`. Color defaults from a stable palette per group. Call `create_state`.
   - `update` → resolve state by name → `update_state`. Renaming a state does NOT migrate items — they keep the same `state_id`.
   - `delete` → confirm. **Block deletion** if any items currently sit in this state — instruct the user to migrate them first via `/bulk-update --state <new>`.
4. **Confirm** — re-list states after mutation.

## State group semantics

Plane groups are fixed: `backlog`, `unstarted`, `started`, `completed`, `cancelled`. Velocity counts only items moved into a `completed` group state during the cycle. Reports separate `cancelled` from `completed`. **Don't put "Done" in the `started` group** — it breaks burndown.

## Recommended state set (Scrum)

| Group | States |
|---|---|
| backlog | Backlog |
| unstarted | Ready, To Do |
| started | In Progress, In Review |
| completed | Done |
| cancelled | Cancelled, Won't Fix |

See `labels-states-properties` skill for variant sets (Kanban, support, research).

## Examples

```
/state list "TaskFlow"
/state create "TaskFlow" --name "In Review" --group started --color #f59e0b
/state update "TaskFlow" "In Review" --sequence 35
/state delete "TaskFlow" "Old Column"
```
