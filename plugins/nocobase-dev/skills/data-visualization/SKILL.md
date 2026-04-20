---
name: data-visualization
description: |
  Chart queries, aggregations, and dashboard data via the NocoBase charts API. Use when:
  - "query chart data"
  - "NocoBase charts"
  - "aggregate records"
  - "data visualization"
  - "dashboard analytics"
  - "sum average count min max"
  - "group by field"
  - "NocoBase dashboard"
---

# Data Visualization

Query aggregated data for charts and dashboards. The NocoBase `charts:query` HTTP endpoint supports measures (aggregations), dimensions (grouping), filtering, sorting, and limits.

> **MCP note:** `nc-mcp` has no dedicated chart tools. For server-side aggregation via MCP, use `resource_query` (see `record-operations`). Fall back to the HTTP `charts:query` endpoint below for the full chart plugin's extra features (cache behavior, date-granularity bucketing, named-series output).

## Authentication

All requests require the API key header:

```
Authorization: Bearer ${NOCOBASE_API_KEY}
```

Base URL: `${NOCOBASE_URL}/api/`

## Query Chart Data

**Resource name:** `charts`

```bash
curl -X POST "${NOCOBASE_URL}/api/charts:query" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "collection": "orders",
    "dataSource": "main",
    "measures": [
      {
        "field": "amount",
        "aggregation": "sum",
        "alias": "totalAmount"
      }
    ],
    "dimensions": [
      {
        "field": "status",
        "alias": "orderStatus"
      }
    ],
    "filter": {
      "createdAt": { "$gte": "2024-01-01" }
    },
    "orders": [
      { "field": "totalAmount", "order": "desc" }
    ],
    "limit": 100
  }'
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `collection` | string | Yes | Collection name to query |
| `dataSource` | string | No | Data source key (default: `main`) |
| `measures` | array | Yes | Aggregation definitions |
| `dimensions` | array | No | Grouping fields |
| `filter` | object | No | Filter conditions (same syntax as record filtering) |
| `orders` | array | No | Sort orders |
| `limit` | number | No | Max rows to return |

### Measure Object

| Field | Type | Description |
|-------|------|-------------|
| `field` | string | Field name to aggregate |
| `aggregation` | string | Function: `sum`, `avg`, `min`, `max`, `count` |
| `alias` | string | Result column alias |

### Dimension Object

| Field | Type | Description |
|-------|------|-------------|
| `field` | string | Field name to group by |
| `alias` | string | Result column alias |
| `format` | string | Date format string (for date fields) |

### Response

```json
{
  "data": [
    { "orderStatus": "pending", "totalAmount": 15000 },
    { "orderStatus": "completed", "totalAmount": 85000 }
  ]
}
```

**ACL:** `loggedIn`. Results are cached for 30 seconds (in-memory cache, max 1000 entries).

## Aggregation Functions

| Function | Description | Example |
|----------|-------------|---------|
| `sum` | Sum of values | Total revenue |
| `avg` | Average of values | Average order value |
| `min` | Minimum value | Lowest price |
| `max` | Maximum value | Highest sale |
| `count` | Count of records | Number of orders |

## Examples

### Sales by Status

```bash
curl -X POST "${NOCOBASE_URL}/api/charts:query" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "collection": "orders",
    "measures": [
      { "field": "amount", "aggregation": "sum", "alias": "total" },
      { "field": "id", "aggregation": "count", "alias": "orderCount" }
    ],
    "dimensions": [
      { "field": "status", "alias": "status" }
    ]
  }'
```

### Monthly Revenue Trend

Use the `format` field on a date dimension to group by month.

```bash
curl -X POST "${NOCOBASE_URL}/api/charts:query" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "collection": "orders",
    "measures": [
      { "field": "amount", "aggregation": "sum", "alias": "revenue" }
    ],
    "dimensions": [
      { "field": "createdAt", "alias": "month", "format": "YYYY-MM" }
    ],
    "orders": [
      { "field": "month", "order": "asc" }
    ],
    "filter": {
      "createdAt": { "$gte": "2024-01-01" }
    }
  }'
```

### Top 10 Customers by Order Count

```bash
curl -X POST "${NOCOBASE_URL}/api/charts:query" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "collection": "orders",
    "measures": [
      { "field": "id", "aggregation": "count", "alias": "orderCount" },
      { "field": "amount", "aggregation": "sum", "alias": "totalSpent" }
    ],
    "dimensions": [
      { "field": "customerId", "alias": "customer" }
    ],
    "orders": [
      { "field": "orderCount", "order": "desc" }
    ],
    "limit": 10
  }'
```

### Multi-Data-Source Query

Query chart data from an external data source:

```bash
curl -X POST "${NOCOBASE_URL}/api/charts:query" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "collection": "transactions",
    "dataSource": "external-pg",
    "measures": [
      { "field": "amount", "aggregation": "avg", "alias": "avgTransaction" }
    ],
    "dimensions": [
      { "field": "type", "alias": "transactionType" }
    ]
  }'
```

## Caching

Query results are cached in memory for 30 seconds with a maximum of 1000 cache entries. Repeated identical queries within 30 seconds return cached results. To get fresh data, wait for the cache to expire or modify the query slightly.

## See also

- `record-operations` — `resource_query` for MCP-native aggregation (simpler, no charts plugin dependency)
- `mcp-patterns` — transport conventions
- `api-patterns` — filter syntax (shared with `charts:query`)
- `ux-constructor` — chart block authoring via `flow_surfaces_*` (see `ux-constructor/references/ui-builder/blocks/chart.md`)
