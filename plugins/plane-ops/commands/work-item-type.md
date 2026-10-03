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
- For `create`/`update`: `--name`, `--description`, `--enabled` (the `is_active` flag). Icon, color and default are not parameters of the Plane MCP tool: set them in the Plane UI.

Parse from `"$ARGUMENTS"`.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for the Plane resource tools `project`, `workitem_type` and `workitem_property`. Note: this feature requires a plan and workspace with custom work item types; a plan without it refuses the calls with a message naming the feature.
2. **Resolve project** → `project_id`.
3. **Route**:
   - `list` → `workitem_type(action=list, project_id)` (omit `project_id` for the workspace catalogue; follow `next_cursor`). Render: name | active? | usage count (`workitem(action=count, project_id, group_by=type_id)`)
   - `create` → `workitem_type(action=resolve, project_id, name)` finds or creates a usable type and never duplicates it; use `workitem_type(action=create, name, description?, project_id?, project_ids?, is_active?)` when you need the description. Where the workspace owns the type vocabulary, creating on a project is rejected and `resolve` (or `import_to_project`) is the valid path. Suggest pairing with custom properties (`/property`).
   - `update` → resolve by name → `workitem_type(action=update, workitem_type_id, project_id?, name?, description?, is_active?)`.
   - `delete` → confirm. Items of this type need migration first; warn if any exist (`workitem(action=count, project_id, pql='type = "<type-id>"')`). Then `workitem_type(action=delete, workitem_type_id, project_id?)`.
   - `get` → `workitem_type(action=retrieve, workitem_type_id, project_id?)` + the property schema attached to the type: `workitem_property(action=list, project_id, workitem_type_id)`.
4. **Confirm** — re-list after mutation.

## Recommended type sets

**Standard product team:** Story, Bug, Task, Spike, Tech Debt
**Platform team:** Feature, Bug, Incident, Runbook, RFC
**Support team:** Ticket, Bug, Question, Escalation

Don't go beyond 6 types — taxonomy fatigue is real. See `labels-states-properties` skill for guidance on type vs label vs property.

## Examples

```
/work-item-type list "TaskFlow"
/work-item-type create "TaskFlow" --name Spike --description "Time-boxed research"
/work-item-type update "TaskFlow" Story --enabled
/work-item-type delete "TaskFlow" "Old Type"
```
