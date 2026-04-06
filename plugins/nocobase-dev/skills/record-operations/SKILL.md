---
name: record-operations
description: |
  CRUD operations on NocoBase records: create, read, update, delete, filter, sort, paginate, import, export, and file uploads. Use when:
  - "create a record in NocoBase"
  - "query NocoBase records"
  - "update NocoBase data"
  - "delete records"
  - "import data into NocoBase"
  - "export NocoBase records"
  - "upload a file to NocoBase"
  - "NocoBase record CRUD"
---

# Record Operations

Perform all data operations on NocoBase collection records through the API. This skill covers listing, getting, creating, updating, destroying, reordering, importing, exporting, and uploading files.

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

## Association Operations

For managing related records (adding tags, linking orders to customers, etc.), use the association URL pattern:

```
POST|GET  ${NOCOBASE_URL}/api/{collection}/{sourceId}/{association}:{action}
```

See `references/association-operations.md` for the complete reference covering all four association types (one-to-one, many-to-one, one-to-many, many-to-many) with their specific actions: `get`, `list`, `create`, `update`, `destroy`, `set`, `add`, `remove`, `toggle`, and `move`.
