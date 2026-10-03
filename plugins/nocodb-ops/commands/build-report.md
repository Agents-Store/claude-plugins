---
description: Build an aggregation report from NocoDB table data
allowed-tools: ["mcp__plugin_nocodb-ops_nocodb__aggregate", "mcp__plugin_nocodb-ops_nocodb__queryRecords", "mcp__plugin_nocodb-ops_nocodb__getTablesList", "mcp__plugin_nocodb-ops_nocodb__getTableSchema", "mcp__plugin_nocodb-ops_nocodb__countRecords"]
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
3. Run `aggregate` with `aggregations: [{ "field": "<field>", "type": "<type>" }]` and `filterGroups: [{ "alias": "All" }]` -- both parameters are required; add one filter group per segment (`{ "alias": "North", "filter": { ... } }`) for a breakdown.
4. If no field specified, run a count aggregation on the whole table, or `groupByRecords` for a count per distinct value.
5. Present results in a clear summary format.
6. Suggest additional aggregations or filters for deeper analysis.

## Example Usage

```
/build-report Orders sum Amount
/build-report Contacts count
/build-report Products avg Price
/build-report Deals max Value
```
