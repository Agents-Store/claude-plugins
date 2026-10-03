---
description: Create a Plane epic for a large feature spanning multiple sprints
argument-hint: <project> <epic name> [--lead <user>] [--target <YYYY-MM-DD>]
---

# Create Epic

Create a new epic in Plane for a large feature or theme containing many work items.

## Arguments

Format: `<project> <epic name> [--lead <user>] [--target <YYYY-MM-DD>] [--priority <urgent|high|medium|low>]`

Parse from `"$ARGUMENTS"`.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for the Plane resource tools `project`, `member`, `workitem_type` and `workitem`. There are no epic tools: an epic is a work item whose type is named "Epic".
2. **Resolve project** — `project(action=list)` → `project_id`.
3. **Resolve lead** — `member(action=list_project, project_id)` → lead UUID.
4. **Create the epic** — follow the `epics-initiatives-milestones` skill. Resolve the type: `workitem_type(action=resolve, project_id, name="Epic")` → its `id` is the `type_id`. Then `workitem(action=create, project_id, name, type_id, description_html (goal + success metrics + out-of-scope), assignees=[<lead uuid>], start_date, target_date, priority)`. If the project refuses the type (the `epics` / `workitem_types` features are off), check `project(action=get_features, project_id)` and ask before enabling them with `project(action=update_features, project_id, epics=true, workitem_types=true)`.
5. **Offer to decompose** — ask if the user wants to run `/decompose` against the epic to create child work items now.
6. **Confirm** — print epic name, lead, target date, and identifier.

## When to Use an Epic

- Scope is 1–3 months of work
- Owned by a single tech lead
- Will be decomposed into many sprint-sized work items
- Not tied to a fixed release date (use a milestone for that)

## Example

```
/create-epic "TaskFlow" "Multi-tenant support" --lead alice --target 2026-07-01
/create-epic "TaskFlow" "Enterprise SSO" --lead bob --priority high
```
