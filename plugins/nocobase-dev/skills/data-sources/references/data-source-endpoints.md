# Data Source Endpoints Reference

Complete endpoint reference for data source management and data-source-scoped collections/fields.

## Data Sources — Endpoint Summary

| Method | Endpoint | Description | ACL |
|--------|----------|-------------|-----|
| GET | `/api/dataSources:listEnabled` | List enabled data sources | `loggedIn` |
| POST | `/api/dataSources:testConnection` | Test DB connection | `pm.data-source-manager` |
| POST | `/api/dataSources:refresh?filterByTk={key}` | Reload data source schema | `pm.data-source-manager` |
| POST | `/api/dataSources:readTables` | List available DB tables | `pm.data-source-manager` |
| POST | `/api/dataSources:loadTables` | Import tables as collections | `pm.data-source-manager` |

## Data-Source-Scoped Collections — Endpoint Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dataSources/{key}/collections:list` | List collections in data source |
| POST | `/api/dataSources/{key}/collections:update?filterByTk={name}` | Update collection metadata |

## Data-Source-Scoped Fields — Endpoint Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dataSourcesCollections/{key}.{coll}/fields:list` | List fields |
| GET | `/api/dataSourcesCollections/{key}.{coll}/fields:get?filterByTk={field}` | Get field |
| POST | `/api/dataSourcesCollections/{key}.{coll}/fields:create` | Create field |
| POST | `/api/dataSourcesCollections/{key}.{coll}/fields:update?filterByTk={field}` | Update field |
| POST | `/api/dataSourcesCollections/{key}.{coll}/fields:destroy?filterByTk={field}` | Delete field |

## Role Permissions per Data Source

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/dataSources/{key}/roles:update?filterByTk={role}` | Set role access for data source |

## testConnection Request Format

```json
{
  "type": "postgres",
  "options": {
    "host": "localhost",
    "port": 5432,
    "database": "mydb",
    "username": "user",
    "password": "pass"
  }
}
```

Supported types: `postgres`, `mysql`, and others depending on installed plugins.

## readTables Request Format

```json
{
  "dataSourceKey": "external-pg"
}
```

Optionally pass `dbOptions` to use temporary connection credentials:

```json
{
  "dataSourceKey": "external-pg",
  "dbOptions": {
    "host": "new-host",
    "port": 5432,
    "database": "otherdb",
    "username": "tempuser",
    "password": "temppass"
  }
}
```

## refresh Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `filterByTk` | string | Yes | Data source key |
| `clientStatus` | string | No | Client-perceived status (refresh only if refreshable) |

## Field Creation Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Field name (unique in collection) |
| `type` | string | Yes | DB type: `string`, `integer`, `boolean`, `date`, `json`, `belongsTo`, `hasMany`, etc. |
| `interface` | string | No | UI interface: `input`, `email`, `phone`, `select`, `checkbox`, `datePicker`, etc. |
| `description` | string | No | Field description |
| `uiSchema` | object | No | UI rendering schema |
| `defaultValue` | any | No | Default value |

## Field Response Format

```json
{
  "data": [
    {
      "name": "id",
      "type": "bigInt",
      "interface": "id",
      "primaryKey": true,
      "uiSchema": {
        "type": "number",
        "title": "ID",
        "x-component": "InputNumber",
        "x-read-pretty": true
      }
    },
    {
      "name": "email",
      "type": "string",
      "interface": "email",
      "uiSchema": {
        "type": "string",
        "title": "Email",
        "x-component": "Input",
        "x-validator": "email"
      }
    }
  ]
}
```

## Role Permissions Request Format

```json
{
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
}
```
