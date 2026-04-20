---
name: data-sources
description: |
  External data source connections, multi-database collections and fields via data-source-scoped API paths. Use when:
  - "connect an external database"
  - "add a data source to NocoBase"
  - "test database connection"
  - "import tables from external DB"
  - "NocoBase data sources"
  - "manage external collections"
  - "multi-database setup"
  - "data source scoped fields"
  - "list enabled data sources"
---

# Data Sources

Manage external database connections and their collections/fields across MCP, CLI, and HTTP. NocoBase supports connecting to multiple databases (PostgreSQL, MySQL, SQLite, etc.) as external data sources alongside the default `main` database.

## MCP tools

| Operation | MCP tool | Notes |
|-----------|----------|-------|
| List enabled datasources | `data_sources_list_enabled` | Excludes `main` |
| List collections in datasource (per role) | `roles_data_sources_collections_list` | Role-scoped |
| Get role config per-datasource | `data_sources_roles_get` | |
| Update role config per-datasource | `data_sources_roles_update` | |
| List resource scopes per-datasource-role | `data_sources_roles_resources_scopes_list` | |
| Get/Create/Update/Delete scope | `data_sources_roles_resources_scopes_{get,create,update,destroy}` | |

### Using `dataSource` parameter for record ops

Every `resource_*` and `collections_*` MCP tool accepts an optional `dataSource` parameter to target a non-`main` database:

```
resource_list({
  resource: "logs",
  dataSource: "external-pg",
  filter: { level: { $eq: "error" } }
})
```

```
collections_list_meta({ dataSource: "external-pg" })
```

Same pattern over HTTP: append `?dataSource=<key>` to any `/api/...` URL, or use the data-source-scoped paths below.

## Authentication (HTTP path)

All HTTP requests require the API key header:

```
Authorization: Bearer ${NOCOBASE_API_KEY}
```

Base URL for all endpoints: `${NOCOBASE_URL}/api/`

## Data Source Management

**Resource name:** `dataSources`

### List Enabled Data Sources

Returns all enabled external data sources (excludes the `main` data source).

```bash
curl -X GET "${NOCOBASE_URL}/api/dataSources:listEnabled" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

**Response:**

```json
{
  "data": [
    {
      "key": "external-pg",
      "displayName": "External PostgreSQL",
      "type": "postgres",
      "enabled": true,
      "status": "loaded"
    }
  ]
}
```

**ACL:** `loggedIn`

### Test Data Source Connection

Validate database credentials before committing a data source configuration.

```bash
curl -X POST "${NOCOBASE_URL}/api/dataSources:testConnection" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "postgres",
    "options": {
      "host": "localhost",
      "port": 5432,
      "database": "mydb",
      "username": "user",
      "password": "pass"
    }
  }'
```

**Response:** `{ "success": true }`

**ACL:** Requires `pm.data-source-manager` snippet permission.

### Refresh Data Source

Reload a data source schema after external database changes.

```bash
curl -X POST "${NOCOBASE_URL}/api/dataSources:refresh?filterByTk=external-pg" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "clientStatus": "loaded"
  }'
```

**Response:** `{ "status": "reloading" }`

### Read Tables

Discover available database tables from a data source.

```bash
curl -X POST "${NOCOBASE_URL}/api/dataSources:readTables" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "dataSourceKey": "external-pg"
  }'
```

Returns an array of table name strings. Optionally pass `dbOptions` to use temporary connection credentials without saving them.

### Load Tables

Import selected tables as NocoBase collections.

```bash
curl -X POST "${NOCOBASE_URL}/api/dataSources:loadTables" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "dataSourceKey": "external-pg",
    "tables": ["users", "orders", "products"]
  }'
```

## Data-Source-Scoped Collections

For external data sources, collections use a scoped URL pattern with the data source key in the path.

**Resource name:** `dataSources.collections`

### List Collections

```bash
curl -X GET "${NOCOBASE_URL}/api/dataSources/external-pg/collections:list?page=1&pageSize=50" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Non-paginated:

```bash
curl -X GET "${NOCOBASE_URL}/api/dataSources/external-pg/collections:list?paginate=false" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

**Paginated response:**

```json
{
  "data": {
    "data": [
      {
        "name": "users",
        "title": "Users",
        "tableName": "users",
        "fields": [
          { "name": "id", "type": "bigInt", "interface": "id", "primaryKey": true },
          { "name": "email", "type": "string", "interface": "email" }
        ]
      }
    ],
    "meta": { "count": 15, "page": 1, "pageSize": 50, "totalPage": 1 }
  }
}
```

### Update Collection

```bash
curl -X POST "${NOCOBASE_URL}/api/dataSources/external-pg/collections:update?filterByTk=users" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Collection Title",
    "sortable": true
  }'
```

Creates the collection record if it doesn't exist.

## Data-Source-Scoped Fields

Fields use a combined key format: `<dataSourceKey>.<collectionName>` as the path segment.

**Resource name:** `dataSourcesCollections.fields`

### List Fields

```bash
curl -X GET "${NOCOBASE_URL}/api/dataSourcesCollections/external-pg.users/fields:list" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

**Response:** Array of field objects sorted by name, each with `name`, `type`, `interface`, and `uiSchema`.

### Get Field

```bash
curl -X GET "${NOCOBASE_URL}/api/dataSourcesCollections/external-pg.users/fields:get?filterByTk=email" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### Create Field

```bash
curl -X POST "${NOCOBASE_URL}/api/dataSourcesCollections/external-pg.users/fields:create" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "phone",
    "type": "string",
    "interface": "phone",
    "description": "Phone number",
    "uiSchema": {
      "type": "string",
      "title": "Phone",
      "x-component": "Input",
      "x-component-props": {
        "placeholder": "Enter phone number"
      }
    }
  }'
```

Fails if field name already exists in the collection.

### Update Field

```bash
curl -X POST "${NOCOBASE_URL}/api/dataSourcesCollections/external-pg.users/fields:update?filterByTk=phone" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "interface": "textarea",
    "uiSchema": {
      "type": "string",
      "title": "Description",
      "x-component": "Input.TextArea"
    }
  }'
```

### Destroy Field

```bash
curl -X POST "${NOCOBASE_URL}/api/dataSourcesCollections/external-pg.users/fields:destroy?filterByTk=phone" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

## Role Permissions per Data Source

Configure resource-level access for a role within a specific data source.

```bash
curl -X POST "${NOCOBASE_URL}/api/dataSources/external-pg/roles:update?filterByTk=editor" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": {
      "actions": ["view", "export"]
    },
    "resources": [
      {
        "name": "users",
        "actions": [
          { "name": "view", "fields": ["id", "name", "email"] },
          { "name": "create", "fields": ["name", "email"] }
        ]
      }
    ]
  }'
```

## Path Comparison

The default `main` data source uses the simple paths documented in the `collections-and-fields` skill. External data sources use scoped paths:

| Operation | Main Database Path | External Data Source Path |
|-----------|-------------------|--------------------------|
| List collections | `collections:list` | `dataSources/<key>/collections:list` |
| List fields | `collections/<name>/fields:list` | `dataSourcesCollections/<key>.<name>/fields:list` |
| Create field | `collections/<name>/fields:create` | `dataSourcesCollections/<key>.<name>/fields:create` |
| Role permissions | `roles/<role>/collections:list` | `dataSources/<key>/roles:update` |

For detailed endpoint reference, see `references/data-source-endpoints.md`.

## See also

- `mcp-patterns` — MCP tool conventions and fallback chain
- `collections-and-fields` — schema CRUD (same tools with `dataSource` scope)
- `record-operations` — record CRUD with `dataSource` parameter
- `auth-and-users` — role-based access control, including per-datasource scopes
