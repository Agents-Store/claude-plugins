---
name: record-operations
description: |
  CRUD operations on NocoBase records across MCP, CLI, and HTTP transports. Create, read, update, delete, filter, sort, paginate, aggregate, import, export, file uploads, firstOrCreate, updateOrCreate. Use when:
  - "create a record in NocoBase"
  - "query NocoBase records"
  - "update NocoBase data"
  - "delete records"
  - "import data into NocoBase"
  - "export NocoBase records"
  - "upload a file to NocoBase"
  - "NocoBase record CRUD"
  - "first or create"
  - "update or create"
  - "upsert record"
  - "toggle association"
  - "resource_list nocobase"
  - "resource_query nocobase"
  - "count records NocoBase"
  - "aggregate records NocoBase"
  - "group by in NocoBase"
---

# Record Operations

Perform all data operations on NocoBase collection records across three transports. This skill covers listing, getting, creating, updating, destroying, reordering, importing, exporting, uploading files, and server-side aggregation.

## MCP `resource_*` family (generic CRUD)

The `resource_*` tools operate uniformly against **any** collection. No collection-specific tool.

| Operation | MCP tool | CLI fallback | HTTP |
|-----------|----------|--------------|------|
| List | `resource_list` | `nocobase-ctl resource list --resource <name> -j` | `GET /api/<name>:list` |
| Query (aggregate) | `resource_query` | `nocobase-ctl resource query --resource <name> -j` | `GET /api/<name>:query` |
| Get one | `resource_get` | `nocobase-ctl resource get --resource <name> --filter-by-tk <pk>` | `GET /api/<name>:get?filterByTk=<pk>` |
| Create | `resource_create` | `nocobase-ctl resource create --resource <name> --body @rec.json` | `POST /api/<name>:create` |
| Update | `resource_update` | `nocobase-ctl resource update --resource <name> --filter-by-tk <pk> --body @patch.json` | `POST /api/<name>:update?filterByTk=<pk>` |
| Destroy | `resource_destroy` | `nocobase-ctl resource destroy --resource <name> --filter-by-tk <pk>` | `POST /api/<name>:destroy?filterByTk=<pk>` |

`resource_list` accepts `{ resource, filter?, fields?, page?, pageSize?, sort?, appends?, dataSource? }` — same semantics as the HTTP query string.

### Example: list + filter + paginate (MCP)

```
resource_list({
  resource: "orders",
  filter: { status: { $eq: "pending" } },
  sort: ["-createdAt"],
  page: 1,
  pageSize: 20,
  appends: ["customer"]
})
```

## Aggregation via `resource_query`

Server-side grouped queries without fetching all rows. Great for dashboards, reports, and counts without needing the chart plugin.

```
resource_query({
  resource: "orders",
  measures: [
    { field: "amount", type: "sum", alias: "total" },
    { field: "id", type: "count", alias: "orderCount" }
  ],
  dimensions: [
    { field: "status" }
  ],
  filter: { createdAt: { $dateBetween: ["2026-01-01", "2026-04-30"] } }
})
```

Returns one row per unique `status` with `total` and `orderCount`. Equivalent HTTP: `GET /api/orders:query`.

### Common aggregations

| Measure type | What it does |
|--------------|--------------|
| `count` | Row count (or distinct count if `distinct: true`) |
| `sum` | Sum of a numeric field |
| `avg` | Average |
| `min`, `max` | Extrema |
| `first`, `last` | First/last value by sort order |

Dimensions group rows. Supports date bucketing via `{ field: "createdAt", type: "date", granularity: "day" }`.

## Data analysis patterns

- **Top-N list:** `resource_list` with `sort` + `pageSize:N`
- **Total count by group:** `resource_query` with one measure (`count`) + one dimension
- **Time series:** `resource_query` with a `date` dimension (granularity `day`/`week`/`month`)
- **Segment health:** two `resource_query` calls with different filters; compute ratios client-side
- **Raw DB view analytics:** `db_views_query` for read-only SQL views not managed by NocoBase

## Multi-datasource

Pass `dataSource: "<key>"` to target an external DB. Default is `"main"`.

```
resource_list({
  resource: "external_logs",
  dataSource: "analytics_db",
  filter: { level: { $eq: "error" } }
})
```

## List Records

Retrieve a paginated list of records with optional filtering, sorting, and field selection.

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/orders:list?page=1&pageSize=20"
```

### With Filtering

Pass a JSON filter object in the `filter` query parameter. See the **api-patterns** skill for the full filter operator reference.

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/orders:list?filter={\"status\":{\"$eq\":\"pending\"}}&page=1&pageSize=20"
```

### With Sorting

Use the `sort` parameter with an array of field names. Prefix `-` for descending order.

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/orders:list?sort=[-createdAt,priority]&page=1&pageSize=20"
```

### With Field Selection and Appends

Select specific fields with `fields` and include related data with `appends`.

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/orders:list?fields=[id,title,status,amount]&appends=[customer,items]&page=1&pageSize=20"
```

### Combined Example

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/orders:list?filter={\"status\":{\"$in\":[\"pending\",\"processing\"]}}&sort=[-priority,-createdAt]&fields=[id,title,status,amount,priority]&appends=[customer]&page=1&pageSize=50"
```

Response:

```json
{
  "data": [
    {
      "id": 101,
      "title": "Order #101",
      "status": "pending",
      "amount": 249.99,
      "priority": 1,
      "customer": { "id": 5, "name": "Acme Corp" }
    }
  ],
  "meta": {
    "count": 87,
    "page": 1,
    "pageSize": 50,
    "totalPage": 2
  }
}
```

### Non-Paginated and Tree Lists

For non-paginated results, add `paginate=false`:

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/categories:list?paginate=false"
```

For tree collections, add `tree=true` to get nested structure:

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/categories:list?tree=true"
```

### Simple Pagination (Large Tables)

For collections with >1000 rows, NocoBase may return a simplified pagination response with `hasNext` instead of `totalPage`:

```json
{
  "data": {
    "rows": [...],
    "hasNext": true,
    "page": 1,
    "pageSize": 20
  }
}
```

## Get a Single Record

Retrieve one record by its primary key using `filterByTk`.

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/orders:get?filterByTk=101&appends=[customer,items]"
```

Response:

```json
{
  "data": {
    "id": 101,
    "title": "Order #101",
    "status": "pending",
    "amount": 249.99,
    "customer": { "id": 5, "name": "Acme Corp" },
    "items": [
      { "id": 1, "product": "Widget A", "quantity": 3 }
    ]
  }
}
```

## Create a Record

Send a JSON body with the field values.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/orders:create" \
  -d '{
    "title": "Order #102",
    "status": "pending",
    "amount": 150.00,
    "customerId": 5,
    "notes": "Rush delivery requested"
  }'
```

Response returns the created record with auto-generated fields (`id`, `createdAt`, etc.).

### Create with Nested Associations

Create a record along with its related records in a single request.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/orders:create" \
  -d '{
    "title": "Order #103",
    "status": "pending",
    "amount": 500.00,
    "customerId": 5,
    "items": [
      { "product": "Widget A", "quantity": 2, "price": 100.00 },
      { "product": "Widget B", "quantity": 3, "price": 100.00 }
    ]
  }'
```

To update association fields inline during creation, pass `updateAssociationValues` as a query parameter listing the association field names.

## Update a Record

Update specific fields of an existing record. Only the fields included in the body are modified.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/orders:update?filterByTk=101" \
  -d '{
    "status": "shipped",
    "trackingNumber": "1Z999AA10123456784"
  }'
```

### Bulk Update with Filter

Update multiple records matching a filter condition.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -g "${NOCOBASE_URL}/api/orders:update?filter={\"status\":{\"$eq\":\"pending\"},\"createdAt\":{\"$dateBefore\":\"2025-01-01\"}}" \
  -d '{
    "status": "cancelled",
    "cancelReason": "Expired"
  }'
```

Additional update parameters: `updateAssociationValues` (array of association field names to update inline) and `forceUpdate=true` to force update even when no fields changed.

**Warning:** Bulk updates without a filter or with a broad filter can modify many records. Always test the filter with a `list` call first.

## Destroy a Record

Delete a single record by primary key.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/orders:destroy?filterByTk=101"
```

### Bulk Destroy with Filter

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -g "${NOCOBASE_URL}/api/orders:destroy?filter={\"status\":{\"$eq\":\"cancelled\"}}"
```

## Move (Reorder) a Record

Reorder records within a sorted collection. Requires a `sort` field on the collection.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/tasks:move" \
  -d '{
    "sourceId": 5,
    "targetId": 2,
    "method": "insertAfter",
    "sortField": "sort"
  }'
```

The `method` accepts `insertAfter` or `insertBefore`. The `sortField` specifies which field stores the sort order (defaults to `sort`).

## Pagination Patterns

### Iterate All Pages

To process all records, loop through pages until `page` exceeds `totalPage`:

```bash
# Page 1
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/orders:list?page=1&pageSize=100"

# Check meta.totalPage, then fetch page 2, 3, etc.
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/orders:list?page=2&pageSize=100"
```

### Get Total Count Only

Use `pageSize=1` to get the count without transferring much data:

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/orders:list?page=1&pageSize=1&fields=[id]"
```

The `meta.count` field in the response gives the total record count.

## Import and Export

### Export Records to XLSX

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/orders:export" \
  -d '{
    "columns": [
      { "dataIndex": ["title"], "defaultTitle": "Title" },
      { "dataIndex": ["status"], "defaultTitle": "Status" },
      { "dataIndex": ["amount"], "defaultTitle": "Amount" },
      { "dataIndex": ["createdAt"], "defaultTitle": "Created" }
    ]
  }' \
  --output orders.xlsx
```

The response is a binary XLSX file. Use `--output` to save it.

### Download Import Template

Download a blank XLSX template with the correct column headers for a collection.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/orders:downloadXlsxTemplate" \
  -d '{
    "columns": [
      { "dataIndex": ["title"], "defaultTitle": "Title" },
      { "dataIndex": ["status"], "defaultTitle": "Status" },
      { "dataIndex": ["amount"], "defaultTitle": "Amount" }
    ]
  }' \
  --output orders_template.xlsx
```

### Import Records from XLSX

Upload a filled XLSX file to import records.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -F "file=@orders_import.xlsx" \
  -F 'columns=[{"dataIndex":["title"],"defaultTitle":"Title"},{"dataIndex":["status"],"defaultTitle":"Status"},{"dataIndex":["amount"],"defaultTitle":"Amount"}]' \
  "${NOCOBASE_URL}/api/orders:importXlsx"
```

The request uses `multipart/form-data` with the file in the `file` field and column mappings in the `columns` field.

## File Uploads

Upload files to a file collection (e.g., `attachments`, `storages`) using multipart/form-data.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -F "file=@/path/to/document.pdf" \
  "${NOCOBASE_URL}/api/attachments:create"
```

Response returns the file record with `url`, `filename`, `size`, and `mimetype`:

```json
{
  "data": {
    "id": 42,
    "filename": "document.pdf",
    "url": "/storage/uploads/document-abc123.pdf",
    "size": 1048576,
    "mimetype": "application/pdf"
  }
}
```

### Upload with Custom Storage

If NocoBase has multiple storage backends configured, specify the storage name:

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -F "file=@/path/to/image.png" \
  -F "storageId=s3-storage" \
  "${NOCOBASE_URL}/api/attachments:create"
```

## First Or Create

Finds the first matching record or creates a new one. Use `filterKeys` to specify which fields to match on.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/tags:firstOrCreate" \
  -d '{
    "filterKeys": ["name"],
    "values": {
      "name": "urgent",
      "color": "red"
    }
  }'
```

If a tag with `name=urgent` exists, returns it. Otherwise creates a new tag with both `name` and `color`.

## Update Or Create

Finds a matching record and updates it, or creates a new one if no match is found.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/settings:updateOrCreate" \
  -d '{
    "filterKeys": ["key"],
    "values": {
      "key": "site_title",
      "value": "My Application"
    }
  }'
```

Matches on `key=site_title`. If found, updates the `value`. If not found, creates a new record with both fields.

## Association Operations

For managing related records (adding tags, linking orders to customers, etc.), use the association URL pattern:

```
POST|GET  ${NOCOBASE_URL}/api/{collection}/{sourceId}/{association}:{action}
```

See `references/association-operations.md` for the complete reference covering all four association types (one-to-one, many-to-one, one-to-many, many-to-many) with their specific actions: `get`, `list`, `create`, `update`, `destroy`, `set`, `add`, `remove`, `toggle`, and `move`.

Via MCP, access associations by passing the association name as the `resource`:

```
resource_list({
  resource: "posts.tags",
  sourceId: 42
})
```

## See also

- `mcp-patterns` — MCP tool catalog and fallback chain
- `collections-and-fields` — collection/field CRUD for the schema
- `data-visualization` — chart plugin wrapping `resource_query` with UI
- `api-patterns` — filter operator reference, pagination, sort syntax
- `data-sources` — multi-DB scoping via `dataSource` parameter
