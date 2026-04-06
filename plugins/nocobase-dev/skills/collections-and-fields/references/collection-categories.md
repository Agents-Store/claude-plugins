# Collection Categories

Collection categories organize collections into logical groups (folders) in the NocoBase sidebar. Each category has a name, optional color, and sort position.

---

## Endpoints

### List All Categories

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/collectionCategories:list"
```

Response:

```json
{
  "data": [
    { "id": 1, "name": "E-Commerce", "color": "#1890ff", "sort": 1 },
    { "id": 2, "name": "CRM", "color": "#52c41a", "sort": 2 },
    { "id": 3, "name": "Internal", "color": "#faad14", "sort": 3 }
  ],
  "meta": { "count": 3, "page": 1, "pageSize": 20, "totalPage": 1 }
}
```

### Get a Single Category

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/collectionCategories:get?filterByTk=1"
```

### Create a Category

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collectionCategories:create" \
  -d '{
    "name": "Analytics",
    "color": "#722ed1"
  }'
```

Supported color values: any hex color string (e.g., `#1890ff`, `#52c41a`, `#f5222d`).

### Update a Category

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collectionCategories:update?filterByTk=1" \
  -d '{
    "name": "Online Store",
    "color": "#13c2c2"
  }'
```

### Destroy a Category

Deleting a category does not delete the collections assigned to it. They become uncategorized.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/collectionCategories:destroy?filterByTk=3"
```

### Move a Category

Reorder categories in the sidebar.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collectionCategories:move" \
  -d '{
    "sourceId": 3,
    "targetId": 1,
    "method": "insertBefore"
  }'
```

## Assigning Collections to Categories

When creating or updating a collection, set the `category` field to associate it with a category:

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections:update?filterByTk=products" \
  -d '{
    "category": [1]
  }'
```

A collection can belong to multiple categories by passing an array of category IDs.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections:update?filterByTk=orders" \
  -d '{
    "category": [1, 2]
  }'
```
