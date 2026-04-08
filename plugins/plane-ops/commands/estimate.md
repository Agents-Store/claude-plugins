---
description: Estimate unestimated work items using Fibonacci story points
argument-hint: <project> [--cycle <cycle-name>] [--scale fibonacci|tshirt]
---

# Estimate

Batch estimate unestimated work items in the backlog or a specific sprint.

## Arguments
Format: `<project> [--cycle <cycle-name>] [--scale fibonacci|tshirt]`
- project: Project name or identifier (required)
- --cycle: Specific sprint to estimate items in (optional, defaults to full backlog)
- --scale: Estimation scale — fibonacci (default) or tshirt

Parse from "$ARGUMENTS".

## Process

0. **Bootstrap connector** — consult the `connector-bootstrap` skill. Probe `ToolSearch` for the action names referenced below (`list_projects`, `list_cycles`, etc.). Match tools by action suffix — never assume a specific MCP prefix. If multiple Plane instances are connected, ask the user which one to use. All formulas and rules come from the `agile-fundamentals` skill.

1. **Resolve project:**
   ```
   list_projects()
   ```

2. **Get items to estimate:**
   If --cycle specified:
   ```
   list_cycles({ project_id }) → find cycle
   list_cycle_work_items({ project_id, cycle_id })
   ```
   Otherwise:
   ```
   list_work_items({ project_id })
   ```
   Filter: items where point is null or 0.

3. **Find reference stories (for calibration):**
   Look for completed items with known point values to anchor estimates.

4. **Estimate each item:**
   For each unestimated item:
   - Present: name, description, priority
   - Analyze: components touched, unknowns, dependencies
   - Suggest estimate with reasoning
   - If scale is tshirt: show XS/S/M/L/XL then map to Fibonacci

5. **On confirmation per item:**
   ```
   update_work_item({ project_id, work_item_id, point: <value> })
   ```

6. **Flag oversized items:**
   Items > 8 points → suggest decomposition with /decompose.

7. **Summary:**
   Total items estimated, total points, items flagged for splitting.

## Example Usage
```
/estimate "TaskFlow"
/estimate "My Project" --cycle "Sprint 12"
/estimate "ShopFlow" --scale tshirt
```
