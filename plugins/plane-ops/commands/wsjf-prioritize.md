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

0. **Bootstrap connector** — consult the `connector-bootstrap` skill. Probe `ToolSearch` for the action names referenced below (`list_projects`, `list_cycles`, etc.). Match tools by action suffix — never assume a specific MCP prefix. If multiple Plane instances are connected, ask the user which one to use. All formulas and rules come from the `agile-fundamentals` skill.

1. **Resolve project:**
   ```
   list_projects()
   ```

2. **Get estimated backlog items:**
   ```
   list_work_items({ project_id })
   ```
   Filter: items in backlog/unstarted states WITH story points set.
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
   update_work_item({ project_id, work_item_id, priority: "<new>" })
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
