---
description: Manage custom work item types in a Plane project (Story, Bug, Spike, ...)
argument-hint: <action> <project> [args...]
---

# Work Item Type

Define and manage custom work item types — beyond the default Issue/Task. Examples: Story, Bug, Spike, Tech Debt, Incident.

## Arguments

Format: `<action> <project> [args...]`

- `action`: `list` | `create` | `update` | `delete` | `get`
- `project`: project name or identifier
- For `create`/`update`: `--name`, `--description`, `--icon`, `--color`, `--default`, `--enabled`

Parse from `"$ARGUMENTS"`.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for `list_work_item_types`, `create_work_item_type`, `update_work_item_type`, `delete_work_item_type`, `retrieve_work_item_type`. Note: this feature requires a Plane build with custom work item types enabled in workspace features.
2. **Resolve project** → `project_id`.
3. **Route**:
   - `list` → render: name | icon | default? | usage count
   - `create` → call `create_work_item_type`. Suggest pairing with custom properties (`/property`).
   - `update` → resolve by name → patch.
   - `delete` → confirm. Items of this type need migration first; warn if any exist.
   - `get` → details + property schema attached to the type.
4. **Confirm** — re-list after mutation.

## Recommended type sets

**Standard product team:** Story, Bug, Task, Spike, Tech Debt
**Platform team:** Feature, Bug, Incident, Runbook, RFC
**Support team:** Ticket, Bug, Question, Escalation

Don't go beyond 6 types — taxonomy fatigue is real. See `labels-states-properties` skill for guidance on type vs label vs property.

## Examples

```
/work-item-type list "TaskFlow"
/work-item-type create "TaskFlow" --name Spike --icon flask --color #8b5cf6 --description "Time-boxed research"
/work-item-type update "TaskFlow" Story --default
/work-item-type delete "TaskFlow" "Old Type"
```
