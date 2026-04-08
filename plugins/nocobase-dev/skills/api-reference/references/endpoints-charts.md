# NocoBase API — Data Visualization (Charts)

All endpoints use base URL `${NOCOBASE_URL}/api/` with header `Authorization: Bearer ${NOCOBASE_API_KEY}`.

---

## Charts (1 endpoint)

| Method | Endpoint | Description | ACL |
|--------|----------|-------------|-----|
| POST | `/api/charts:query` | Query aggregated data for charts | `loggedIn` |

### Query Chart Data

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/charts:query" \
  -d '{
    "collection": "orders",
    "dataSource": "main",
    "measures": [
      { "field": "amount", "aggregation": "sum", "alias": "totalAmount" }
    ],
    "dimensions": [
      { "field": "status", "alias": "orderStatus" }
    ],
    "filter": { "createdAt": { "$gte": "2024-01-01" } },
    "orders": [ { "field": "totalAmount", "order": "desc" } ],
    "limit": 100
  }'
```

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `collection` | string | Yes | Collection name to query |
| `dataSource` | string | No | Data source key (default: `main`) |
| `measures` | array | Yes | Aggregation definitions |
| `dimensions` | array | No | Grouping fields |
| `filter` | object | No | Filter conditions |
| `orders` | array | No | Sort orders |
| `limit` | number | No | Max rows to return |

### Measure Object

| Field | Type | Description |
|-------|------|-------------|
| `field` | string | Field name to aggregate |
| `aggregation` | string | `sum`, `avg`, `min`, `max`, `count` |
| `alias` | string | Result column alias |

### Dimension Object

| Field | Type | Description |
|-------|------|-------------|
| `field` | string | Field name to group by |
| `alias` | string | Result column alias |
| `format` | string | Date format (for date fields, e.g. `YYYY-MM`) |

### Response

```json
{
  "data": [
    { "orderStatus": "pending", "totalAmount": 15000 },
    { "orderStatus": "completed", "totalAmount": 85000 }
  ]
}
```

### Caching

Results are cached in memory for 30 seconds with a maximum of 1000 cache entries.
