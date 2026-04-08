# NocoBase API — Flow Models, Flow SQL, Variables

All endpoints use base URL `${NOCOBASE_URL}/api/` with header `Authorization: Bearer ${NOCOBASE_API_KEY}`.

---

## Flow Models (6 unique + 16 inherited endpoints)

| Method | Endpoint | Description | ACL |
|--------|----------|-------------|-----|
| GET | `/api/flowModels:findOne` | Get model by uid or parentId | `loggedIn` |
| POST | `/api/flowModels:save` | Upsert flow model | `ui.flowModels` |
| POST | `/api/flowModels:duplicate?uid={uid}` | Deep copy model tree | `ui.flowModels` |
| POST | `/api/flowModels:attach` | Attach model as child | `ui.flowModels` |
| POST | `/api/flowModels:move` | Reposition model | `ui.flowModels` |
| POST | `/api/flowModels:destroy?filterByTk={uid}` | Remove model tree | `ui.flowModels` |

Plus 16 inherited schema actions (getJsonSchema, getProperties, insert, patch, batchPatch, remove, insertAdjacent, etc.) — see flow-models skill for full list.

### Find One

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/flowModels:findOne?uid=model-abc123"
```

### Save (Upsert)

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/flowModels:save" \
  -d '{
    "uid": "model-abc123",
    "use": "FormBlockModel",
    "stepParams": { "dataSource": { "dataSourceKey": "main", "collectionName": "users" } },
    "title": "User Form"
  }'
```

### Duplicate

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/flowModels:duplicate?uid=model-abc123"
```

### Attach

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/flowModels:attach" \
  -d '{ "uid": "child-uid", "parentId": "parent-uid", "subKey": "properties", "subType": "object", "position": "last" }'
```

### Move

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/flowModels:move" \
  -d '{ "sourceId": "model-to-move", "targetId": "reference-model", "position": "after" }'
```

### Destroy

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/flowModels:destroy?filterByTk=model-abc123"
```

---

## Flow SQL (3 endpoints)

| Method | Endpoint | Description | ACL |
|--------|----------|-------------|-----|
| POST | `/api/flowSql:save` | Save SQL query | `ui.flowSql` |
| POST | `/api/flowSql:runById` | Execute saved SQL | `loggedIn` |
| GET | `/api/flowSql:getBind?uid={uid}` | Get bind parameters | `loggedIn` |

### Save

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/flowSql:save" \
  -d '{ "uid": "sql-uid", "sql": "SELECT * FROM {{users}} WHERE status = :status", "dataSourceKey": "main" }'
```

### Run

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/flowSql:runById" \
  -d '{ "uid": "sql-uid", "type": "SELECT", "bind": { "status": "active" }, "liquidContext": { "users": "public.users" } }'
```

### Get Bind

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/flowSql:getBind?uid=sql-uid"
```

---

## Variables (1 endpoint)

| Method | Endpoint | Description | ACL |
|--------|----------|-------------|-----|
| POST | `/api/variables:resolve` | Resolve template variables | `loggedIn` |

### Resolve

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/variables:resolve" \
  -d '{ "template": { "title": "{{ $nRecord.name }}" }, "contextParams": { "$nRecord": { "collectionName": "users", "filterByTk": 1 } } }'
```
