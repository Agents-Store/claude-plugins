# NocoBase API — Data Sources, Data-Source-Scoped Collections & Fields

All endpoints use base URL `${NOCOBASE_URL}/api/` with header `Authorization: Bearer ${NOCOBASE_API_KEY}`.

---

## Data Sources (5 endpoints)

| Method | Endpoint | Description | ACL |
|--------|----------|-------------|-----|
| GET | `/api/dataSources:listEnabled` | List all enabled data sources | `loggedIn` |
| POST | `/api/dataSources:testConnection` | Test database connection | `pm.data-source-manager` |
| POST | `/api/dataSources:refresh?filterByTk={key}` | Reload data source schema | `pm.data-source-manager` |
| POST | `/api/dataSources:readTables` | List available DB tables | `pm.data-source-manager` |
| POST | `/api/dataSources:loadTables` | Import tables as collections | `pm.data-source-manager` |

### List Enabled

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/dataSources:listEnabled"
```

### Test Connection

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/dataSources:testConnection" \
  -d '{ "type": "postgres", "options": { "host": "localhost", "port": 5432, "database": "mydb", "username": "user", "password": "pass" } }'
```

### Refresh

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/dataSources:refresh?filterByTk=external-pg" \
  -d '{ "clientStatus": "loaded" }'
```

### Read Tables

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/dataSources:readTables" \
  -d '{ "dataSourceKey": "external-pg" }'
```

### Load Tables

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/dataSources:loadTables" \
  -d '{ "dataSourceKey": "external-pg", "tables": ["users", "orders"] }'
```

---

## Data-Source-Scoped Collections (2 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dataSources/{key}/collections:list` | List collections |
| POST | `/api/dataSources/{key}/collections:update?filterByTk={name}` | Update collection |

### List Collections

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/dataSources/external-pg/collections:list?page=1&pageSize=50"
```

Non-paginated: add `paginate=false`.

### Update Collection

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/dataSources/external-pg/collections:update?filterByTk=users" \
  -d '{ "title": "Updated Title" }'
```

---

## Data-Source-Scoped Fields (5 endpoints)

URL format uses combined key: `{dataSourceKey}.{collectionName}`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dataSourcesCollections/{key}.{coll}/fields:list` | List fields |
| GET | `/api/dataSourcesCollections/{key}.{coll}/fields:get?filterByTk={name}` | Get field |
| POST | `/api/dataSourcesCollections/{key}.{coll}/fields:create` | Create field |
| POST | `/api/dataSourcesCollections/{key}.{coll}/fields:update?filterByTk={name}` | Update field |
| POST | `/api/dataSourcesCollections/{key}.{coll}/fields:destroy?filterByTk={name}` | Delete field |

### List Fields

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/dataSourcesCollections/external-pg.users/fields:list"
```

### Create Field

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/dataSourcesCollections/external-pg.users/fields:create" \
  -d '{
    "name": "phone",
    "type": "string",
    "interface": "phone",
    "uiSchema": { "type": "string", "title": "Phone", "x-component": "Input" }
  }'
```

---

## Role Permissions per Data Source (1 endpoint)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/dataSources/{key}/roles:update?filterByTk={role}` | Set role access for data source |

### Set Role Access

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/dataSources/external-pg/roles:update?filterByTk=editor" \
  -d '{
    "strategy": { "actions": ["view", "export"] },
    "resources": [
      { "name": "users", "actions": [{ "name": "view", "fields": ["id", "name"] }] }
    ]
  }'
```
