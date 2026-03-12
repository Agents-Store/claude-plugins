---
description: Create a NocoBase page with blocks
allowed-tools: ["mcp__nocobase__page_create", "mcp__nocobase__table_add", "mcp__nocobase__column_add", "mcp__nocobase__action_add", "mcp__nocobase__menu_create_group"]
argument-hint: <page-title> [--collection <name>] [--block <table|form|details|kanban>]
---

# Create Page

Create a NocoBase page with configured blocks, columns, and actions.

## Arguments
Format: `<page-title> [--collection <name>] [--block <table|form|details|kanban>]`
- page-title: Title of the page (required)
- --collection: Collection to bind to the block (optional)
- --block: Block type to add — table, form, details, kanban, calendar, gantt, chart (optional)

Parse from "$ARGUMENTS".

## Process

1. **Create the page:**
   Use `page_create` to create a new page with the given title.

2. **Add blocks (if collection specified):**
   Use `table_add` to add the requested block type bound to the collection.

3. **Configure columns:**
   Use `column_add` to add visible fields to the block.

4. **Add actions:**
   Use `action_add` to add standard actions (create, edit, delete, filter).

## Example Usage
```
/create-page "Contacts" --collection contacts --block table
/create-page "Dashboard"
/create-page "New Order" --collection orders --block form
```
