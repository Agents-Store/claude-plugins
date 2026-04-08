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

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for `list_modules`, `create_module`, `add_work_items_to_module`.
2. **Resolve project** — `list_projects` → `project_id`.
3. **Resolve lead** — `get_project_members({ project_id })` → lead UUID.
4. **Create the module** — follow the `modules` skill. Call `create_module` with `name`, `description`, `lead`, `start_date`, `target_date`, `status: "planned"`.
5. **Offer to populate** — ask the user whether to add any existing backlog items to the module now (`add_work_items_to_module`).
6. **Confirm** — print module name, lead, target date, and item count.

## Example

```
/create-module "TaskFlow" "Billing v2" --lead alice --target 2026-06-30
/create-module "TaskFlow" "Onboarding revamp" --lead bob --target 2026-05-15 --description "Cut signup drop-off by 30%"
```

See the `modules` skill for when to use a module vs a cycle.
