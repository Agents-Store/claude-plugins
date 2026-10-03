---
description: Apply the same change to many Plane work items at once
argument-hint: <project> <items...> <changes...>
---

# Bulk Update

Apply identical field changes to a list of work items. Plane has no bulk-edit action for arbitrary fields — this command loops `workitem(action=update)` (and the merge actions `manage_assignee` / `manage_label`) and reports per-item success/failure; cycle, module and milestone moves go through one `manage_workitems` call each.

## Arguments

Format: `<project> <items...> <changes...>`

- `project`: project name or identifier
- `items`: space-separated identifiers (`PROJ-148 PROJ-149 PROJ-150`), or `--from-search "query"`, or `--from-cycle "Sprint 14"`, or `--from-state "In Review"`
- Changes (any combination):
  - `--state <name>`
  - `--priority <p0|p1|p2|...>`
  - `--assignee <user>` (replaces) or `--add-assignee <user>` (appends)
  - `--label add:<name>` / `--label remove:<name>`
  - `--cycle <name>` (move to cycle) or `--cycle none` (remove from cycle)
  - `--module <name>` / `--module remove:<name>`
  - `--milestone <name>`

Parse from `"$ARGUMENTS"`.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for the Plane resource tools `workitem`, plus `cycle`, `module` and `milestone` for the cycle/module/milestone moves.
2. **Resolve project** → `project_id`.
3. **Resolve item set**:
   - explicit list → resolve each identifier to UUID
   - `--from-search` → `workitem(action=search, query)` (workspace-wide; keep the project's items) or `workitem(action=list, project_id, pql='text ~ "query"')`
   - `--from-cycle` → `cycle(action=list_workitems, project_id, cycle_id)`
   - `--from-state` → `workitem(action=list, project_id, pql='state = "<state-uuid>"')`
   Print the resolved set with title preview and **ask for confirmation** before mutating.
4. **Resolve targets** — state name → state UUID (`state(action=list, project_id)`); label name → label UUID (`label(action=list, project_id)`); assignee → user UUID (`member(action=list_project, project_id)`); cycle/module/milestone name → IDs (`cycle` / `module` / `milestone` `action=list`).
5. **Apply** — loop items:
   - For field changes (state/priority/assignee replace) → `workitem(action=update, project_id, workitem_id, state=…, priority=…, assignees=[…])`.
   - For adding or removing one assignee or label → `workitem(action=manage_assignee, ..., add_user_id|remove_user_id)` / `workitem(action=manage_label, ..., add_label_id|remove_label_id)`: the list is merged server-side, no read-first needed.
   - For cycle/module/milestone moves → one call with the full list: `cycle(action=manage_workitems, project_id, cycle_id, add_ids=[…])`, `module(action=manage_workitems, …)`, `milestone(action=manage_workitems, …)`. `--cycle none` / `--module remove:<name>` use `remove_ids=[…]` on the cycle/module the items are in (a removal: the permission dialog asks first); find that cycle with `--from-cycle` or by asking.
6. **Report** — table: `ID | Field | Old → New | Result`. Sum success/failure counts.

## Safety

- **Always show the resolved set and ask "apply to N items? (y/n)"** before any write.
- Refuse to bulk-update >50 items in a single call without `--force`.
- Bulk updates do NOT trigger Plane notifications the same way single updates do — warn the user.
- Operations are NOT atomic. Partial failure is possible. Print failed IDs at the end.

## Examples

```
/bulk-update "TaskFlow" PROJ-148 PROJ-149 PROJ-150 --state "Done"
/bulk-update "TaskFlow" --from-state "In Review" --priority p1
/bulk-update "TaskFlow" --from-cycle "Sprint 14" --label add:carryover --cycle "Sprint 15"
/bulk-update "TaskFlow" --from-search "login bug" --assignee alice
/bulk-update "TaskFlow" PROJ-160 PROJ-161 --milestone "v2.0 Public Beta"
```

## Best Practices

- Run `/find` or `/my-work` first to verify the selection set, then pipe the IDs into `/bulk-update`.
- For sprint carryover, the canonical pattern is: `/cycles transfer` (handles incomplete-only) — only use bulk-update for cross-cutting field edits.
- After bulk-update, run `/history` on a sample to verify the change landed.
