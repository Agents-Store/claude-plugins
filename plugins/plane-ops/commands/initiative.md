---
description: Manage Plane initiatives — strategic groupings above epics
argument-hint: <action> [args...]
---

# Initiative

Initiatives are the highest-level planning unit in Plane — they group multiple epics across multiple projects under a single strategic theme. See the `epics-initiatives-milestones` skill for the conceptual model.

## Arguments

Format: `<action> [args...]`

- `action`: `list` | `create` | `update` | `get` | `delete` | `link-epic`
- For `create`: `--name`, `--description`, `--lead <user>`, `--start <date>`, `--target <date>`
- For `link-epic`: `--initiative <name|id>`, `--epic <project>:<id>`

Parse from `"$ARGUMENTS"`.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for `list_initiatives`, `create_initiative`, `update_initiative`, `retrieve_initiative`, `delete_initiative`. Initiatives are workspace-scoped (no `project_id`).
2. **Route**:
   - `list` → `list_initiatives`. Render: name | lead | epics count | start–target | status.
   - `create` → gather name, description, dates. Initiatives without an explicit lead and target date drift — warn the user if either is missing.
   - `update` → resolve by name or ID → `update_initiative`.
   - `get` → `retrieve_initiative` + render its epics list (cross-project) and aggregate progress.
   - `delete` → confirm. Linked epics are NOT deleted, just unlinked.
   - `link-epic` → many Plane builds use the epic's `initiative_id` field via `update_epic`. If a dedicated `add_epic_to_initiative` tool exists, use it; otherwise patch the epic.
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
