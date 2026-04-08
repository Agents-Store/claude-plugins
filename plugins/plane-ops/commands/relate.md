---
description: Create a relation between two Plane work items (block, duplicate, relates-to)
argument-hint: <relation> <project> <from-item> <to-item>
---

# Relate

Create or remove a typed relation between two work items.

## Arguments

Format: `<relation> <project> <from-item> <to-item>`

- `relation`: `blocks` | `blocked-by` | `duplicate` | `duplicate-of` | `relates-to` | `remove`
- `project`: project name or identifier
- `from-item`: source work item identifier (`PROJ-42`)
- `to-item`: target work item identifier (`PROJ-43`)

Parse from `"$ARGUMENTS"`.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for `create_work_item_relation`, `list_work_item_relations`, `remove_work_item_relation`.
2. **Resolve project** → `project_id`. **Resolve both work items** → UUIDs.
3. **Map relation type** to API value. Plane typically uses: `blocking` / `blocked_by` / `duplicate` / `relates_to`. Check schema and adapt. Note the API field is usually `issues: [uuid]` (plural array), not `related_issue`.
4. **Route**:
   - `blocks` → from `from-item` create `blocking` to `to-item` (API may auto-create the inverse `blocked_by` on the target)
   - `blocked-by` → from `from-item` create `blocked_by` to `to-item`
   - `duplicate` / `duplicate-of` → `duplicate` relation
   - `relates-to` → `relates_to`
   - `remove` → `list_work_item_relations`, find the matching one, call `remove_work_item_relation`
5. **Confirm** — print both items and the relation direction.

## Examples

```
/relate blocks "TaskFlow" PROJ-148 PROJ-150
/relate blocked-by "TaskFlow" PROJ-150 PROJ-148
/relate duplicate "TaskFlow" PROJ-160 PROJ-148
/relate relates-to "TaskFlow" PROJ-148 PROJ-200
/relate remove "TaskFlow" PROJ-148 PROJ-150
```

## Best Practices

- Set blockers **as soon as you discover them**, not in retro. Blockers visible early let the team unblock themselves.
- Mark duplicates with `duplicate-of`, then close the duplicate with a comment linking to the canonical item.
- Use `/dependencies` after blocking to see the full graph and detect chains/cycles.
