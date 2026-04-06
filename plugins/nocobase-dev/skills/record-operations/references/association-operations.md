# Association Operations

Complete reference for managing related records through the NocoBase API. Association operations use a nested URL pattern that targets the relationship between a source record and its associated records.

## URL Pattern

```
POST|GET  ${NOCOBASE_URL}/api/{collection}/{sourceId}/{association}:{action}
```

Where:
- `{collection}` -- the source collection name
- `{sourceId}` -- the primary key of the source record
- `{association}` -- the association field name defined on the source collection
- `{action}` -- the operation to perform

---

## One-to-One Associations (hasOne / belongsTo)

A single related record. Example: `users` hasOne `profile`, or `orders` belongsTo `customer`.

### Available Actions

| Action | HTTP Method | Description |
|--------|-------------|-------------|
| `get` | GET | Get the associated record |
| `create` | POST | Create and link a new associated record |
| `update` | POST | Update the associated record |
| `destroy` | POST | Delete the associated record |
| `set` | POST | Link an existing record by its primary key |
| `remove` | POST | Unlink the associated record (sets foreign key to null) |

### Get

Retrieve the associated record.

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/users/1/profile:get"
```

### Create

Create a new record and link it to the source.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/users/1/profile:create" \
  -d '{
    "bio": "Software engineer",
    "avatar": "https://example.com/avatar.png",
    "timezone": "UTC"
  }'
```

### Update

Update the associated record's fields.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/users/1/profile:update" \
  -d '{"bio": "Senior software engineer"}'
```

### Destroy

Delete the associated record.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/users/1/profile:destroy"
```

### Set

Link an existing record to the source. Replaces any previously linked record.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/users/1/profile:set" \
  -d '{"tk": 42}'
```

The `tk` value is the primary key of the existing record to link.

### Remove

Unlink the associated record without deleting it. Sets the foreign key to null.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/users/1/profile:remove"
```

---

## Many-to-One Associations (belongsTo)

The source record references a single parent. Example: `orders` belongsTo `customer`.

### Available Actions

| Action | HTTP Method | Description |
|--------|-------------|-------------|
| `get` | GET | Get the associated parent record |
| `create` | POST | Create a new parent record and link it |
| `update` | POST | Update the associated parent record |
| `destroy` | POST | Delete the associated parent record |
| `set` | POST | Link to a different existing parent record |
| `remove` | POST | Unlink from the parent (sets foreign key to null) |

### Get

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/orders/101/customer:get"
```

### Set

Change which parent record is linked.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/orders/101/customer:set" \
  -d '{"tk": 7}'
```

### Remove

Unlink from the parent without deleting the parent record.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/orders/101/customer:remove"
```

---

## One-to-Many Associations (hasMany)

The source has multiple children. Example: `customers` hasMany `orders`.

### Available Actions

| Action | HTTP Method | Description |
|--------|-------------|-------------|
| `list` | GET | List all associated records (paginated) |
| `get` | GET | Get a specific associated record by primary key |
| `create` | POST | Create a new child record linked to the source |
| `update` | POST | Update a specific associated record |
| `destroy` | POST | Delete a specific associated record |
| `move` | POST | Reorder an associated record |
| `set` | POST | Replace all associations with a new set of record IDs |
| `add` | POST | Link existing records to the source |
| `remove` | POST | Unlink records from the source (sets foreign key to null) |

### List

Retrieve all child records with pagination.

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/customers/5/orders:list?page=1&pageSize=20&sort=[-createdAt]"
```

Supports all standard query parameters: `filter`, `sort`, `page`, `pageSize`, `fields`, `appends`.

### Get

Retrieve a specific child record.

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/customers/5/orders:get?filterByTk=101"
```

### Create

Create a new child record automatically linked to the parent.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/customers/5/orders:create" \
  -d '{
    "title": "Order #104",
    "status": "pending",
    "amount": 75.00
  }'
```

The foreign key (`customerId`) is set automatically.

### Update

Update a specific child record.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/customers/5/orders:update?filterByTk=101" \
  -d '{"status": "shipped"}'
```

### Destroy

Delete a specific child record.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/customers/5/orders:destroy?filterByTk=101"
```

### Set

Replace all associations. Unlinks all current children and links only the specified IDs.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/customers/5/orders:set" \
  -d '{"tk": [101, 102, 103]}'
```

**Warning:** Records not in the `tk` array will have their foreign key set to null, effectively orphaning them.

### Add

Link existing records to the parent without unlinking current children.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/customers/5/orders:add" \
  -d '{"tk": [104, 105]}'
```

### Remove

Unlink specific records from the parent without deleting them.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/customers/5/orders:remove" \
  -d '{"tk": [101]}'
```

### Move

Reorder a child record within the association.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/customers/5/orders:move" \
  -d '{
    "sourceId": 103,
    "targetId": 101,
    "method": "insertBefore",
    "sortField": "sort"
  }'
```

---

## Many-to-Many Associations (belongsToMany)

Both sides have multiple related records connected through a junction table. Example: `posts` belongsToMany `tags` through `postsTags`.

### Available Actions

| Action | HTTP Method | Description |
|--------|-------------|-------------|
| `list` | GET | List all associated records (paginated) |
| `get` | GET | Get a specific associated record |
| `create` | POST | Create a new record and add it to the association |
| `update` | POST | Update a specific associated record |
| `destroy` | POST | Delete a specific associated record |
| `move` | POST | Reorder an associated record |
| `set` | POST | Replace all associations with a new set of IDs |
| `add` | POST | Add records to the association |
| `remove` | POST | Remove records from the association |
| `toggle` | POST | Toggle a record's presence in the association |

### List

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/posts/42/tags:list?page=1&pageSize=50"
```

### Get

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/posts/42/tags:get?filterByTk=7"
```

### Create

Create a new tag and link it to the post in one call.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/posts/42/tags:create" \
  -d '{"name": "tutorial", "color": "blue"}'
```

This creates the tag in the `tags` collection and adds a row in the `postsTags` junction table.

### Update

Update a specific associated record's fields.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/posts/42/tags:update?filterByTk=7" \
  -d '{"color": "green"}'
```

### Destroy

Delete an associated record entirely (removes it from the target collection and junction table).

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/posts/42/tags:destroy?filterByTk=7"
```

### Set

Replace all associations. Removes all existing junction rows and creates new ones for the specified IDs.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/posts/42/tags:set" \
  -d '{"tk": [1, 3, 5]}'
```

**Important:** `set` removes all existing associations first. Tags 2, 4, 6, etc. will be unlinked from this post (but not deleted from the `tags` collection).

### Add

Add records to the association without removing existing ones.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/posts/42/tags:add" \
  -d '{"tk": [8, 9]}'
```

If a record is already associated, it is silently ignored (no duplicate junction rows).

### Remove

Remove specific records from the association (deletes junction rows, not the target records).

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/posts/42/tags:remove" \
  -d '{"tk": [3, 5]}'
```

### Toggle

Toggle a single record's membership in the association. If the record is currently associated, remove it. If not associated, add it.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/posts/42/tags:toggle" \
  -d '{"tk": 7}'
```

This is useful for bookmark/favorite/star toggles in the UI.

### Move

Reorder an associated record within the many-to-many relationship.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/posts/42/tags:move" \
  -d '{
    "sourceId": 5,
    "targetId": 1,
    "method": "insertBefore",
    "sortField": "sort"
  }'
```

---

## Action Summary by Association Type

| Action | hasOne | belongsTo | hasMany | belongsToMany |
|--------|--------|-----------|---------|---------------|
| `list` | -- | -- | Yes | Yes |
| `get` | Yes | Yes | Yes | Yes |
| `create` | Yes | Yes | Yes | Yes |
| `update` | Yes | Yes | Yes | Yes |
| `destroy` | Yes | Yes | Yes | Yes |
| `move` | -- | -- | Yes | Yes |
| `set` | Yes | Yes | Yes | Yes |
| `add` | -- | -- | Yes | Yes |
| `remove` | Yes | Yes | Yes | Yes |
| `toggle` | -- | -- | -- | Yes |

**Key distinctions:**
- **`set`** replaces all current associations with the provided list. For singular associations (hasOne, belongsTo), it takes a single `tk` value. For plural associations, it takes an array.
- **`add`** appends to existing associations without removing current ones. Only available on hasMany and belongsToMany.
- **`remove`** unlinks records without deleting them from the target collection. For singular associations, no `tk` is needed.
- **`toggle`** is exclusive to belongsToMany and flips the association on/off for a single record.
