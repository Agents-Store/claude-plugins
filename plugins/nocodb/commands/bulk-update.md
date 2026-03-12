---
description: Bulk update records in a NocoDB table
allowed-tools: ["mcp__nocodb__bulk_update_records", "mcp__nocodb__list_records", "mcp__nocodb__list_tables"]
argument-hint: <table-name> --where <filter> --set <field=value>
---

# Bulk Update

Update multiple records in a NocoDB table that match a filter.

## Arguments
Format: `<table-name> --where <filter> --set <field=value>`
- table-name: Name or ID of the table (required)
- --where: Filter to find records (required)
- --set: Field and value to update (required)

Parse from "$ARGUMENTS".

## Process

1. **Find table:**
   Use `list_tables` to resolve table name to ID.

2. **Find matching records:**
   Use `list_records` with the filter to preview what will be updated.

3. **Confirm and update:**
   Use `bulk_update_records` to update all matching records.

4. **Verify:**
   Use `list_records` to confirm updates.

## Example Usage
```
/bulk-update contacts --where "(Status,eq,Lead)" --set Status=Active
/bulk-update orders --where "(DueDate,lt,2024-01-01)~and(Status,eq,Pending)" --set Status=Overdue
```
