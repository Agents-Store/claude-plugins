---
description: Break down a work item into smaller stories/tasks using INVEST criteria
argument-hint: <work-item-identifier>
---

# Decompose

Break down a work item into smaller, sprint-ready stories or tasks using INVEST criteria and vertical slicing.

## Arguments
Format: `<work-item-identifier>`
- work-item-identifier: Item identifier like "MP-42" (required)

Parse from "$ARGUMENTS". Extract project_identifier and issue_identifier number.

## Process

0. **Bootstrap connector** — consult the `connector-bootstrap` skill. Probe `ToolSearch` for the action names referenced below (`list_projects`, `list_cycles`, etc.). Match tools by action suffix — never assume a specific MCP prefix. If multiple Plane instances are connected, ask the user which one to use. All formulas and rules come from the `agile-fundamentals` skill.

1. **Retrieve the item:**
   ```
   retrieve_work_item_by_identifier({
     project_identifier: "<prefix>",
     issue_identifier: <number>
   })
   ```

2. **Analyze against INVEST criteria:**
   - Independent: check relations for hard dependencies
   - Negotiable: check description format
   - Valuable: check epic/business context
   - Estimable: check description detail
   - Small: check if points > 8
   - Testable: check acceptance criteria

3. **Propose decomposition:**
   Choose splitting pattern based on item type:
   - Workflow steps (most common)
   - Business rules
   - CRUD operations
   - Happy path vs edge cases
   - Data variations
   - Platform/interface

4. **Present proposed children:**
   | # | Child Item | Points | Rationale |
   |---|-----------|--------|-----------|

5. **On confirmation — create children:**
   ```
   For each child:
     create_work_item({
       project_id, name, parent: <parent_id>,
       point, priority, description_html
     })
   ```

6. **Set relations between children if needed:**
   ```
   create_work_item_relation({ relation_type: "blocked_by", ... })
   ```

## Example Usage
```
/decompose MP-42
/decompose TF-15
```
