---
description: Manage Plane initiatives — strategic groupings above epics
argument-hint: <action> [args...]
---

# Initiative

Initiatives are the highest-level planning unit in Plane — they group multiple epics across multiple projects under a single strategic theme. See the `epics-initiatives-milestones` skill for the conceptual model.

## Arguments

Format: `<action> [args...]`

- `action`: `list` | `create` | `update` | `get` | `delete` | `link-epic` | `link-project`
- For `create`/`update`: `--name`, `--description`, `--lead <user>`, `--start <date>`, `--target <date>` (stored as `end_date`), `--state DRAFT|PLANNED|ACTIVE|COMPLETED|CLOSED`
- For `link-epic`: `--initiative <name|id>`, `--epic <project>:<id>`; for `link-project`: `--initiative <name|id>`, `--project <name>`

Parse from `"$ARGUMENTS"`.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for the Plane resource tools `initiative`, `workitem` and `workspace`. Initiatives are workspace-scoped (no `project_id`). The tool needs the workspace's native initiatives feature (`workspace(action=get_features)`; enabling it with `workspace(action=update_features, initiatives=true)` needs the user's consent).
2. **Route**:
   - `list` → `initiative(action=list)` (returns every initiative, unpaginated). Render: name | lead | epics count | start–end | state.
   - `create` → gather name, description, dates. `initiative(action=create, name, description_html, lead, start_date, end_date, state)`. Initiatives without an explicit lead and end date drift — warn the user if either is missing. Projects are linked afterwards (`link-project`).
   - `update` → resolve by name or ID → `initiative(action=update, initiative_id, ...)`.
   - `get` → `initiative(action=retrieve, initiative_id)` + `initiative(action=list_workitems, initiative_id)` (the linked epics, cross-project) + `initiative(action=list_projects, initiative_id)`, then aggregate progress with `workitem(action=count, pql='childOf("<epic identifier>")', group_by=state__group)` per epic.
   - `delete` → confirm, then `initiative(action=delete, initiative_id)`. Linked epics and projects are NOT deleted, just unlinked.
   - `link-epic` → there is no epic tool: the epic is a work item, and `initiative(action=manage_workitems, initiative_id, add_ids=[<epic workitem id>])` links it (`remove_ids` unlinks it). Resolve the epic with `workitem(action=retrieve_by_identifier, workitem_identifier="<PROJ-N>")`. Read the result back with `initiative(action=list_workitems, initiative_id)`.
   - `link-project` → `initiative(action=add_projects, initiative_id, project_ids=[<project uuid>])` (`remove_projects` unlinks), read back with `initiative(action=list_projects, initiative_id)`.
3. **Confirm** — print initiative ID and a summary of linked epics.

## When to use what

| Unit | Scope | Time horizon | Owner |
|---|---|---|---|
| Initiative | workspace, multi-project | quarter / multi-quarter | exec / PM lead |
| Epic | single project | weeks–months | tech lead |
| Module | single project, scope-boxed | flexible | feature owner |
| Cycle | single project, time-boxed | 1–2 weeks | scrum master |
| Milestone | release marker | event date | release manager |

If your work fits inside one project, use an **epic**, not an initiative. Initiatives are for cross-team strategic bets.

## Examples

```
/initiative list
/initiative create --name "Q2 Mobile Launch" --lead alice --target 2026-06-30
/initiative get "Q2 Mobile Launch"
/initiative link-epic --initiative "Q2 Mobile Launch" --epic "Mobile App":42
/initiative update "Q2 Mobile Launch" --target 2026-07-15
```
