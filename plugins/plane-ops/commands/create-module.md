---
description: Create a Plane module (feature/workstream grouping across sprints)
argument-hint: <project> <module name> [--lead <user>] [--target <YYYY-MM-DD>]
---

# Create Module

Create a new module in Plane to group work items by feature or workstream across multiple sprints.

## Arguments

Format: `<project> <module name> [--lead <user>] [--target <YYYY-MM-DD>] [--description <text>]`

Parse from `"$ARGUMENTS"`.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for the Plane resource tools `project`, `member` and `module`.
2. **Resolve project** — `project(action=list)` → `project_id`.
3. **Resolve lead** — `member(action=list_project, project_id)` → lead UUID.
4. **Create the module** — follow the `modules` skill. Call `module(action=create, project_id, name, description, lead, start_date, target_date, status="planned")`.
5. **Offer to populate** — ask the user whether to add any existing backlog items to the module now (`module(action=manage_workitems, project_id, module_id, add_ids=[...])`, read back with `module(action=list_workitems)`).
6. **Confirm** — print module name, lead, target date, and item count.

## Example

```
/create-module "TaskFlow" "Billing v2" --lead alice --target 2026-06-30
/create-module "TaskFlow" "Onboarding revamp" --lead bob --target 2026-05-15 --description "Cut signup drop-off by 30%"
```

See the `modules` skill for when to use a module vs a cycle.
