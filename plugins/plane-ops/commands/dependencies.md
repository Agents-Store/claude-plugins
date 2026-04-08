---
description: Show dependency graph and active blockers for a project or sprint
argument-hint: <project> [--cycle <current|next|name>]
---

# Dependencies

Inspect work item relations to find active blockers, blocking chains, and risk items.

## Arguments

Format: `<project> [--cycle <current|next|name>] [--item <id>]`

Parse from `"$ARGUMENTS"`. Without `--cycle` or `--item`, scan the whole active backlog.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for `list_work_items`, `list_work_item_relations`, `retrieve_work_item`.
2. **Resolve project** — `list_projects` → `project_id`.
3. **Scope the scan**:
   - `--cycle current` → items in the active cycle (`list_cycle_work_items`)
   - `--cycle <name>` → items in that cycle
   - `--item <id>` → just that item and its transitive relations
   - default → in-progress + unstarted items in the project
4. **For each item, fetch relations** — `list_work_item_relations({ project_id, work_item_id })`.
5. **Build the graph** — direction matters: `blocked_by` (incoming), `blocking` (outgoing), `duplicate`, `relates_to`.
6. **Highlight risk**:
   - Items blocked by something not yet started
   - Items blocking 2+ other items (critical path candidates)
   - Cyclic dependencies (report explicitly)
7. **Present** as a table grouped by risk level (🔴 blocker chain, 🟡 single blocker, 🟢 no blockers).

## Example

```
/dependencies "TaskFlow"
/dependencies "TaskFlow" --cycle current
/dependencies "TaskFlow" --item PROJ-148
```

## Output Format

```
🔴 Blocker chains
  PROJ-148 (Stripe webhook) ← blocks PROJ-152, PROJ-153, PROJ-160
    blocked_by PROJ-140 (backlog, unestimated)

🟡 Single blockers
  PROJ-155 blocked_by PROJ-147 (in progress, @alice)

🟢 Clear
  PROJ-150, PROJ-151, …
```
