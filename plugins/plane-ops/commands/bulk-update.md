---
description: Apply the same change to many Plane work items at once
argument-hint: <project> <items...> <changes...>
---

# Bulk Update

Apply identical field changes to a list of work items. Plane has no native bulk endpoint — this command loops `update_work_item` and reports per-item success/failure.

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

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for `update_work_item`, `list_work_items`, `search_work_items`, plus `add_work_items_to_cycle` / `add_work_items_to_module` / `add_work_items_to_milestone` for the cycle/module/milestone moves.
2. **Resolve project** → `project_id`.
3. **Resolve item set**:
   - explicit list → resolve each identifier to UUID
   - `--from-search` → `search_work_items`
   - `--from-cycle` / `--from-state` → `list_work_items` with filter
   Print the resolved set with title preview and **ask for confirmation** before mutating.
4. **Resolve targets** — state name → state_id; label name → label_id; assignee → user_id; cycle/module/milestone name → IDs.
5. **Apply** — loop items:
   - For field changes (state/priority/assignee/labels) → `update_work_item`. Per-item, fetch current `label_ids`/`assignee_ids` first when adding/removing rather than replacing.
   - For cycle/module/milestone moves → use the corresponding `add_work_items_to_*` bulk tool with the full list (single API call).
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
