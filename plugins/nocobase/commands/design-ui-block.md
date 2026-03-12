---
description: Design a NocoBase UI block layout
allowed-tools: ["mcp__nocobase__page_list", "mcp__nocobase__page_inspect", "mcp__nocobase__table_add", "mcp__nocobase__column_add", "mcp__nocobase__action_add"]
argument-hint: <collection> <block-type>
---

# Design UI Block

Design a NocoBase UI block for a collection — table, form, details, kanban, calendar, or chart.

## Arguments
Format: `<collection> <block-type>`
- collection: Target collection name (required)
- block-type: Block type — table, form, details, kanban, calendar, gantt, chart (required)

Parse from "$ARGUMENTS".

## Process

1. **Analyze collection:**
   Review collection fields and relations to determine best configuration.

2. **Design block:**
   - Select visible fields and their order
   - Configure filters and default sort
   - Set up actions (create, edit, delete, export)
   - Configure field components

3. **Provide implementation guidance.**

## Example Usage
```
/design-ui-block "contacts" table
/design-ui-block "deals" kanban
/design-ui-block "events" calendar
/design-ui-block "orders" form
```
