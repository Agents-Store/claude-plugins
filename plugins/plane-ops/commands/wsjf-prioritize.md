---
description: Prioritize backlog items using Weighted Shortest Job First (WSJF) scoring
argument-hint: <project>
---

# WSJF Prioritize

Prioritize backlog items using Weighted Shortest Job First scoring — balancing value, urgency, risk, and effort.

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

2. **Get estimated backlog items:**
   ```
   workitem(action=list, project_id, pql='stateGroup IN ("backlog","unstarted")', fields="id,name,point,estimate_point,priority", per_page=100)
   ```
   Follow `next_cursor`; keep items WITH story points set (PQL has no estimate field, so `point` is checked on the listed items).
   (Items without estimates cannot be scored — suggest /estimate first.)

3. **Score each item interactively:**
   For each item, present and ask:
   - **Business Value** (1-10): How much user/business value does this deliver?
   - **Time Criticality** (1-10): How urgent is this? Is there a deadline?
   - **Risk Reduction** (1-10): Does this reduce technical or business risk?
   - **Job Size**: Use existing story points

4. **Calculate WSJF:**
   ```
   WSJF = (Business Value + Time Criticality + Risk Reduction) / Story Points
   ```
   Higher WSJF = higher priority.

5. **Sort and assign priorities:**
   ```
   Top 25%    → priority: "urgent"
   25-50%     → priority: "high"
   50-75%     → priority: "medium"
   Bottom 25% → priority: "low"
   ```

6. **Update items:**
   ```
   workitem(action=update, project_id, workitem_id, priority="<new>")
   ```

7. **Display ranked list:**
   ```
   | Rank | Item | BV | TC | RR | Size | WSJF | Priority |
   |------|------|----|----|-----|------|------|----------|
   | 1 | Quick fix | 8 | 9 | 5 | 2 | 11.0 | urgent |
   | 2 | Key feature | 9 | 7 | 6 | 5 | 4.4 | high |
   | ... |
   ```

## Example Usage
```
/wsjf-prioritize "TaskFlow"
/wsjf-prioritize "My Project"
```
