# NocoBase API — Record Operations & Associations

All endpoints use base URL `${NOCOBASE_URL}/api/` with header `Authorization: Bearer ${NOCOBASE_API_KEY}`.

Replace `{collection}` with the actual collection name (e.g., `posts`, `orders`, `products`).

---

## Record Operations (10 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/{collection}:list` | List records with filtering, sorting, pagination |
| GET | `/api/{collection}:get?filterByTk={id}` | Get a single record by primary key |
| POST | `/api/{collection}:create` | Create a new record |
| POST | `/api/{collection}:update?filterByTk={id}` | Update an existing record |
| POST | `/api/{collection}:destroy?filterByTk={id}` | Delete a record |
| POST | `/api/{collection}:move` | Reorder a record in a sorted list |
| POST | `/api/{collection}:export` | Export records to XLSX |
| POST | `/api/{collection}:importXlsx` | Import records from XLSX (multipart/form-data) |
| POST | `/api/{collection}:downloadXlsxTemplate` | Download an XLSX import template |
| POST | `/api/{fileCollection}:create` | Upload a file (multipart/form-data) |

### List Records

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/posts:list?filter={\"status\":{\"$eq\":\"published\"}}&sort=[-createdAt]&page=1&pageSize=20&fields=[id,title,status]&appends=[author,tags]"
```

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `filter` | JSON | Filter conditions with `$`-prefixed operators |
| `sort` | array | Field names; prefix `-` for descending (e.g., `[-createdAt,title]`) |
| `page` | integer | Page number (1-based, default: 1) |
| `pageSize` | integer | Records per page (default: 20) |
| `fields` | array | Select specific fields to return |
| `appends` | array | Include related association data |
| `except` | array | Exclude specific fields |

**Response:**
```json
{
  "data": [ { "id": 1, "title": "...", "author": { "id": 5, "name": "..." } } ],
  "meta": { "count": 150, "page": 1, "pageSize": 20, "totalPage": 8 }
}
```

### Get Record

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/posts:get?filterByTk=42&appends=[author,tags]"
```

**Query parameters:** `filterByTk` (required), `fields`, `appends`, `except`

### Create Record

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/posts:create" \
  -d '{
    "title": "New Post",
    "content": "Post body here",
    "status": "draft",
    "author_id": 5
  }'
```

**Query parameters:** `whitelist` (array), `blacklist` (array) — restrict writable fields

### Update Record

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/posts:update?filterByTk=42" \
  -d '{ "status": "published", "publishedAt": "2025-06-01T12:00:00Z" }'
```

**Query parameters:** `filterByTk` (required), `filter` (optional additional filter), `whitelist`, `blacklist`

### Destroy Record

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/posts:destroy?filterByTk=42"
```

To bulk destroy, pass `filter` instead of `filterByTk`:

```bash
curl -X POST -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/posts:destroy?filter={\"status\":{\"$eq\":\"archived\"}}"
```

### Move Record

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/posts:move" \
  -d '{
    "sourceId": 42,
    "targetId": 38,
    "method": "insertAfter",
    "sortField": "sort"
  }'
```

**Body fields:** `sourceId`, `targetId`, `method` (`insertAfter` | `insertBefore`), `sortField` (optional, defaults to `sort`)

### Export Records

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/posts:export" \
  -d '{
    "columns": [
      { "dataIndex": ["title"], "title": "Title" },
      { "dataIndex": ["status"], "title": "Status" },
      { "dataIndex": ["createdAt"], "title": "Created" }
    ]
  }' \
  --output posts.xlsx
```

Returns an XLSX file as binary response.

### Import from XLSX

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -F "file=@products.xlsx" \
  -F 'columns=[{"dataIndex":["title"],"title":"Title"},{"dataIndex":["price"],"title":"Price"}]' \
  "${NOCOBASE_URL}/api/products:importXlsx"
```

Uses `multipart/form-data`. The `columns` field maps spreadsheet columns to collection fields.

### Download XLSX Template

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/products:downloadXlsxTemplate" \
  -d '{
    "columns": [
      { "dataIndex": ["title"], "title": "Title" },
      { "dataIndex": ["price"], "title": "Price" }
    ]
  }' \
  --output products-template.xlsx
```

### File Upload

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -F "file=@photo.jpg" \
  "${NOCOBASE_URL}/api/attachments:create"
```

Uses `multipart/form-data`. The default file collection is `attachments`. Returns the file record with `url`, `filename`, `mimetype`, `size`.

---

## Association Endpoints

Associations use the nested URL pattern: `/api/{collection}/{sourceId}/{association}:{action}`

Replace `{collection}` with the source collection, `{sourceId}` with the source record's primary key, and `{association}` with the association field name.

### HasOne / BelongsTo Associations (6 endpoints each)

These association types work on a single related record.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/{collection}/{sourceId}/{assoc}:get` | Get the associated record |
| POST | `/api/{collection}/{sourceId}/{assoc}:create` | Create and link a new associated record |
| POST | `/api/{collection}/{sourceId}/{assoc}:update` | Update the associated record |
| POST | `/api/{collection}/{sourceId}/{assoc}:destroy` | Destroy the associated record |
| POST | `/api/{collection}/{sourceId}/{assoc}:set` | Set (link) an existing record as the association |
| POST | `/api/{collection}/{sourceId}/{assoc}:remove` | Remove (unlink) the association without deleting the record |

#### Examples — HasOne

```bash
# Get the profile for user 5
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/users/5/profile:get"

# Create a profile for user 5
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/users/5/profile:create" \
  -d '{ "bio": "Developer", "avatar": "https://example.com/avatar.jpg" }'

# Set an existing profile record (id=10) as user 5's profile
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/users/5/profile:set" \
  -d '{ "tk": 10 }'

# Remove (unlink) user 5's profile
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/users/5/profile:remove"
```

#### Examples — BelongsTo

```bash
# Get the author of post 42
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/posts/42/author:get"

# Set user 5 as the author of post 42
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/posts/42/author:set" \
  -d '{ "tk": 5 }'
```

### HasMany Associations (9 endpoints)

In addition to the 6 endpoints above, hasMany adds `list`, `add`, and bulk operations.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/{collection}/{sourceId}/{assoc}:list` | List all associated records |
| GET | `/api/{collection}/{sourceId}/{assoc}:get?filterByTk={id}` | Get one associated record |
| POST | `/api/{collection}/{sourceId}/{assoc}:create` | Create a new record and link it |
| POST | `/api/{collection}/{sourceId}/{assoc}:update?filterByTk={id}` | Update an associated record |
| POST | `/api/{collection}/{sourceId}/{assoc}:destroy?filterByTk={id}` | Destroy an associated record |
| POST | `/api/{collection}/{sourceId}/{assoc}:set` | Replace all associated records |
| POST | `/api/{collection}/{sourceId}/{assoc}:remove` | Remove (unlink) specific records |
| POST | `/api/{collection}/{sourceId}/{assoc}:add` | Add existing records to the association |
| POST | `/api/{collection}/{sourceId}/{assoc}:move` | Reorder an associated record |

#### Examples — HasMany

```bash
# List all comments for post 42
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/posts/42/comments:list?page=1&pageSize=20&sort=[-createdAt]"

# Create a comment for post 42
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/posts/42/comments:create" \
  -d '{ "body": "Great post!", "author_id": 7 }'

# Add existing comment records (ids 10, 11) to post 42
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/posts/42/comments:add" \
  -d '{ "tk": [10, 11] }'

# Remove (unlink) comments 10 and 11 from post 42
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/posts/42/comments:remove" \
  -d '{ "tk": [10, 11] }'
```

### BelongsToMany Associations (11 endpoints)

Many-to-many associations support all hasMany endpoints plus `toggle`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/{collection}/{sourceId}/{assoc}:list` | List all associated records |
| GET | `/api/{collection}/{sourceId}/{assoc}:get?filterByTk={id}` | Get one associated record |
| POST | `/api/{collection}/{sourceId}/{assoc}:create` | Create a new record and link it |
| POST | `/api/{collection}/{sourceId}/{assoc}:update?filterByTk={id}` | Update an associated record |
| POST | `/api/{collection}/{sourceId}/{assoc}:destroy?filterByTk={id}` | Destroy an associated record |
| POST | `/api/{collection}/{sourceId}/{assoc}:set` | Replace all associated records |
| POST | `/api/{collection}/{sourceId}/{assoc}:remove` | Remove (unlink) specific records |
| POST | `/api/{collection}/{sourceId}/{assoc}:add` | Add existing records to the association |
| POST | `/api/{collection}/{sourceId}/{assoc}:move` | Reorder an associated record |
| POST | `/api/{collection}/{sourceId}/{assoc}:toggle` | Toggle: add if not linked, remove if linked |
| POST | `/api/{collection}/{sourceId}/{assoc}:setThrough` | Set pivot/through table data |

#### Examples — BelongsToMany

```bash
# List all tags for post 42
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/posts/42/tags:list"

# Add tag 7 to post 42
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/posts/42/tags:add" \
  -d '{ "tk": 7 }'

# Toggle tag 7 on post 42 (add if missing, remove if present)
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/posts/42/tags:toggle" \
  -d '{ "tk": 7 }'

# Replace all tags on post 42 with tags 1, 3, 5
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/posts/42/tags:set" \
  -d '{ "tk": [1, 3, 5] }'

# Remove tags 3, 5 from post 42
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/posts/42/tags:remove" \
  -d '{ "tk": [3, 5] }'
```

---

## Association Endpoint Summary

| Relationship Type | Available Actions | Total Endpoints |
|-------------------|-------------------|-----------------|
| HasOne | get, create, update, destroy, set, remove | 6 |
| BelongsTo | get, create, update, destroy, set, remove | 6 |
| HasMany | list, get, create, update, destroy, set, remove, add, move | 9 |
| BelongsToMany | list, get, create, update, destroy, set, remove, add, move, toggle, setThrough | 11 |
| **Total** | | **32** |

**Common body field for set/add/remove/toggle:** `tk` — the target key(s). Single value for one record, array for multiple records.
