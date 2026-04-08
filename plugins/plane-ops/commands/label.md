---
description: Manage Plane labels — list, create, update, delete, or apply to a work item
argument-hint: <action> <project> [args...]
---

# Label

Manage labels in a Plane project. Labels drive triage, grooming, and reporting filters.

## Arguments

Format: `<action> <project> [args...]`

- `action`: `list` | `create` | `update` | `delete` | `apply` | `remove`
- `project`: project name or identifier
- Remaining: label name, `--color #hex`, `--description`, `--item PROJ-42`

Parse from `"$ARGUMENTS"`.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for `list_labels`, `create_label`, `update_label`, `delete_label`, `retrieve_label`, plus `update_work_item` (for `apply`/`remove`).
2. **Resolve project** — `list_projects` → `project_id`.
3. **Route**:
   - `list` → `list_labels({ project_id })`. Group by prefix (`type/`, `area/`, `priority/`) for readability.
   - `create` → `create_label({ project_id, name, color, description })`. If color omitted, pick from a stable palette by hashing the name.
   - `update` → resolve label by name → `update_label`.
   - `delete` → confirm with the user before destructive call (labels in use are unlinked from items).
   - `apply` → resolve work item via `retrieve_work_item_by_identifier`, fetch current `label_ids`, append the new one, `update_work_item({ label_ids })`. Check schema field name — some Plane builds use `labels`.
   - `remove` → same but remove from the list.
4. **Confirm** — print resulting label set or item label list.

## Conventions

Recommend a **prefixed taxonomy** so labels stay searchable:

- `type/bug`, `type/feature`, `type/chore`, `type/spike`, `type/tech-debt`
- `area/api`, `area/web`, `area/mobile`, `area/infra`
- `priority/p0`, `priority/p1`, `priority/p2`
- `status/needs-info`, `status/blocked`, `status/ready-for-review`
- `customer/acme`, `customer/contoso` (only if you track per-customer work)

Avoid creating one-off labels — they become noise. Audit with `/label list` quarterly.

## Examples

```
/label list "TaskFlow"
/label create "TaskFlow" "type/bug" --color #e11d48
/label update "TaskFlow" "type/bug" --description "Defect in shipped behavior"
/label apply "TaskFlow" --item PROJ-148 "type/bug"
/label remove "TaskFlow" --item PROJ-148 "status/needs-info"
/label delete "TaskFlow" "old-label"
```
