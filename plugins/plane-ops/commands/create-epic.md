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

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for `list_epics`, `create_epic`, `update_epic`.
2. **Resolve project** — `list_projects` → `project_id`.
3. **Resolve lead** — `get_project_members` → lead UUID.
4. **Create the epic** — follow the `epics-initiatives-milestones` skill. Call `create_epic` with `name`, `description_html` (goal + success metrics + out-of-scope), `lead`, `start_date`, `target_date`, `priority`.
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
