# NocoBase API — Collections, Fields, Categories & Database Views

All endpoints use base URL `${NOCOBASE_URL}/api/` with header `Authorization: Bearer ${NOCOBASE_API_KEY}`.

---

## Collections (7 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/collections:list` | List all collections |
| GET | `/api/collections:get?filterByTk={name}` | Get collection details by name |
| POST | `/api/collections:create` | Create a new collection |
| POST | `/api/collections:update?filterByTk={name}` | Update collection metadata |
| POST | `/api/collections:destroy?filterByTk={name}` | Delete a collection |
| POST | `/api/collections:move` | Reorder a collection in the list |
| POST | `/api/collections:setFields?filterByTk={name}` | Bulk set/replace all fields on a collection |

### List Collections

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/collections:list?page=1&pageSize=100"
```

**Query parameters:** `filter`, `sort`, `page`, `pageSize`, `fields`, `appends`

### Get Collection

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/collections:get?filterByTk=posts&appends=[fields]"
```

The `filterByTk` value is the collection `name` (not numeric ID).

### Create Collection

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections:create" \
  -d '{
    "name": "products",
    "title": "Products",
    "fields": [
      { "type": "string", "name": "title", "interface": "input" },
      { "type": "float", "name": "price", "interface": "number" },
      { "type": "text", "name": "description", "interface": "textarea" },
      { "type": "boolean", "name": "active", "interface": "checkbox", "defaultValue": true }
    ]
  }'
```

**Required body fields:**
- `name` (string) — Internal collection name (lowercase, no spaces)
- `title` (string) — Display name

**Optional body fields:**
- `fields` (array) — Field definitions to create with the collection
- `inherits` (array) — Parent collection names for inheritance
- `category` (array) — Collection category associations
- `sortable` (boolean|string) — Enable sorting

### Update Collection

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections:update?filterByTk=products" \
  -d '{ "title": "Product Catalog" }'
```

### Destroy Collection

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/collections:destroy?filterByTk=products"
```

### Move Collection

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections:move" \
  -d '{
    "sourceId": "products",
    "targetId": "orders",
    "method": "insertAfter"
  }'
```

**Body fields:** `sourceId`, `targetId`, `method` (`insertAfter` | `insertBefore` | `prepend` | `append`)

### Set Fields (Bulk)

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections:setFields?filterByTk=products" \
  -d '{
    "fields": [
      { "type": "string", "name": "sku", "interface": "input" },
      { "type": "float", "name": "price", "interface": "number" }
    ]
  }'
```

Replaces the entire field set for the collection.

---

## Fields (6 endpoints)

Fields use a nested resource pattern: `collections/{collectionName}/fields`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/collections/{name}/fields:list` | List all fields in a collection |
| GET | `/api/collections/{name}/fields:get?filterByTk={fieldName}` | Get a single field definition |
| POST | `/api/collections/{name}/fields:create` | Create a new field |
| POST | `/api/collections/{name}/fields:update?filterByTk={fieldName}` | Update field definition |
| POST | `/api/collections/{name}/fields:destroy?filterByTk={fieldName}` | Delete a field |
| POST | `/api/collections/{name}/fields:move` | Reorder a field |

### List Fields

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/collections/products/fields:list"
```

### Get Field

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/collections/products/fields:get?filterByTk=title"
```

### Create Field

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections/products/fields:create" \
  -d '{
    "type": "string",
    "name": "category",
    "interface": "select",
    "uiSchema": {
      "title": "Category",
      "enum": [
        { "value": "electronics", "label": "Electronics" },
        { "value": "clothing", "label": "Clothing" }
      ]
    }
  }'
```

**Required body fields:**
- `type` (string) — Database column type (`string`, `text`, `integer`, `float`, `boolean`, `date`, `json`, `belongsTo`, `hasMany`, `belongsToMany`, etc.)
- `name` (string) — Internal field name
- `interface` (string) — UI interface type (`input`, `textarea`, `number`, `select`, `checkbox`, `datetime`, `richText`, `attachment`, `linkTo`, etc.)

**Optional body fields:**
- `uiSchema` (object) — UI rendering configuration
- `defaultValue` — Default value for new records
- `unique` (boolean) — Enforce uniqueness
- `description` (string) — Field description

### Update Field

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections/products/fields:update?filterByTk=category" \
  -d '{ "uiSchema": { "title": "Product Category" } }'
```

### Destroy Field

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/collections/products/fields:destroy?filterByTk=category"
```

### Move Field

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections/products/fields:move" \
  -d '{
    "sourceId": "category",
    "targetId": "title",
    "method": "insertAfter"
  }'
```

---

## Collection Categories (6 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/collectionCategories:list` | List all collection categories |
| GET | `/api/collectionCategories:get?filterByTk={id}` | Get a category by ID |
| POST | `/api/collectionCategories:create` | Create a new category |
| POST | `/api/collectionCategories:update?filterByTk={id}` | Update a category |
| POST | `/api/collectionCategories:destroy?filterByTk={id}` | Delete a category |
| POST | `/api/collectionCategories:move` | Reorder categories |

### List Categories

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/collectionCategories:list"
```

### Create Category

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collectionCategories:create" \
  -d '{ "name": "CRM", "color": "blue", "sort": 1 }'
```

**Body fields:** `name` (string, required), `color` (string), `sort` (integer)

### Update Category

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collectionCategories:update?filterByTk=1" \
  -d '{ "name": "Customer Relations", "color": "green" }'
```

### Destroy Category

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/collectionCategories:destroy?filterByTk=1"
```

---

## Database Views (3 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dbViews:list` | List available database views |
| GET | `/api/dbViews:get?filterByTk={viewName}` | Get view schema/details |
| POST | `/api/dbViews:query` | Execute a query against a database view |

### List Database Views

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/dbViews:list"
```

### Get Database View

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/dbViews:get?filterByTk=my_view&schema=public"
```

### Query Database View

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/dbViews:query" \
  -d '{ "sql": "SELECT * FROM my_view LIMIT 10" }'
```
