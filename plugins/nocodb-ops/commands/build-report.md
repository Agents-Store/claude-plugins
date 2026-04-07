---
description: Build an aggregation report from NocoDB table data
allowed-tools: ["mcp__nocodb__aggregate", "mcp__nocodb__queryRecords", "mcp__nocodb__getTablesList", "mcp__nocodb__getTableSchema", "mcp__nocodb__countRecords"]
argument-hint: <table-name> [aggregation-type] [field]
---

# Build Report

Build an aggregation report from a NocoDB table.

## Arguments

Parse from "$ARGUMENTS":
- `table-name` (required): Name or ID of the table
- `aggregation-type` (optional): sum, count, avg, min, max, median (default: count)
- `field` (optional): Field to aggregate on

## Process

1. Run `getTablesList` to resolve the table name to an ID.
2. Run `getTableSchema` to discover numeric and countable fields.
3. Run `aggregate` with appropriate aggregation type and field.
4. If no field specified, run count aggregation on the whole table.
5. Present results in a clear summary format.
6. Suggest additional aggregations or filters for deeper analysis.

## Example Usage

```
/build-report Orders sum Amount
/build-report Contacts count
/build-report Products avg Price
/build-report Deals max Value
```
