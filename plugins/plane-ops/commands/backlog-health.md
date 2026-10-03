---
description: Analyze backlog health — unestimated items, stale items, missing details
argument-hint: <project>
---

# Backlog Health

Generate a health report for the project backlog — identifying gaps and recommending actions.

## Arguments
Format: `<project>`
- project: Project name or identifier (required)

Parse from "$ARGUMENTS".

## Process

0. **Bootstrap connector** — consult the `connector-bootstrap` skill. Probe `ToolSearch` for the Plane resource tools referenced below (`project`, `workitem`); their names are `mcp__<server>__<resource>`, never assume a specific MCP prefix. If multiple Plane instances are connected, ask the user which one to use. All formulas and rules come from the `agile-fundamentals` skill. Calls are written `resource(action=..., ...)`.

1. **Resolve project:**
   ```
   project(action=list)
   ```

2. **Get all backlog items:**
   ```
   workitem(action=count, project_id, pql='stateGroup IN ("backlog","unstarted")')
   workitem(action=count, project_id, pql='stateGroup IN ("backlog","unstarted") AND hasNoAssignee()')
   workitem(action=count, project_id, pql='stateGroup IN ("backlog","unstarted") AND priority = "none"')
   workitem(action=list, project_id, pql='stateGroup IN ("backlog","unstarted")', per_page=100, fields="id,name,point,description_stripped")
   ```
   The counts (read `total_count`) answer the PQL-filterable metrics without paging; the list (follow `next_cursor`) is needed only for the estimate and description checks, which PQL cannot filter. Stale candidates: add `AND updatedAt < daysAgo(42)` to the first query.

3. **Calculate health metrics:**
   - Total items in backlog
   - Unestimated (point is null)
   - No priority set (priority is "none" or null)
   - No assignee
   - No description (description_html is empty)
   - Oversized (point > 8)
   - Ready items (has estimate + priority + description)

4. **Calculate health score:**
   ```
   health_score = (ready_items / total_items) × 100
   ```

5. **Display health report:**
   ```
   ┌─────────────────────────────────────┐
   │ BACKLOG HEALTH REPORT               │
   ├─────────────────────────────────────┤
   │ Total items:      XX                │
   │ Ready for sprint: XX (XX%)          │
   │ Unestimated:      XX (XX%)          │
   │ No priority:      XX (XX%)          │
   │ Oversized (>8pt): XX (XX%)          │
   │ No description:   XX (XX%)          │
   ├─────────────────────────────────────┤
   │ Health Score: XX% — STATUS          │
   └─────────────────────────────────────┘
   ```

6. **Provide actionable recommendations:**
   Based on the biggest gaps, suggest:
   - /estimate for unestimated items
   - /decompose for oversized items
   - /wsjf-prioritize for unprioritized items

## Example Usage
```
/backlog-health "TaskFlow"
/backlog-health "My Project"
```
