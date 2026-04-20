---
name: api-patterns
description: |
  NocoBase transport conventions — HTTP Resource:Action URL pattern, MCP ⇄ HTTP mapping, query parameters, filtering, sorting, and pagination. Use when:
  - "how does the NocoBase API work"
  - "NocoBase API URL format"
  - "how to filter NocoBase records"
  - "NocoBase pagination"
  - "NocoBase sort query"
  - "NocoBase API request format"
  - "resource action pattern"
  - "map NocoBase MCP to HTTP"
  - "NocoBase filter operators"
  - "NocoBase $eq $in $dateOn"
---

# NocoBase API Patterns

The NocoBase HTTP API follows a Resource & Action model. Every endpoint is a combination of a resource name and an action name separated by a colon. Master this pattern and all NocoBase operations become predictable — across MCP, CLI, and HTTP.

## Transport fallback chain

Three ways to talk to NocoBase, in preference order:

1. **MCP first** — `*` tools. See `mcp-patterns` for the tool catalog and naming convention.
2. **`nocobase-ctl` CLI** — upstream CLI wrapper. Example: `nocobase-ctl resource list --resource posts --filter '{"status":"published"}' -j`.
3. **HTTP curl** — raw REST at `/api/{resource}:{action}`. Universal fallback documented below.

All three reach the same backend. Pick the first available tier.

## MCP ⇄ HTTP mapping

Every HTTP Resource:Action endpoint has an equivalent MCP tool. The mapping is mechanical:

| HTTP | MCP tool |
|------|----------|
| `GET  /api/collections:list` | `collections_list` |
| `POST /api/collections:create` | `collections_create` |
| `POST /api/collections:apply` | `collections_apply` |
| `GET  /api/{collection}:list` | `resource_list` with `resource: "{collection}"` |
| `POST /api/{collection}:create` | `resource_create` with `resource: "{collection}"` |
| `POST /api/{collection}:update?filterByTk={id}` | `resource_update` with `resource, filterByTk` |
| `POST /api/workflows:execute?filterByTk={id}` | `workflows_execute` with `filterByTk: {id}` |
| `POST /api/roles/{name}/users:add` | `roles_users_add` with `roleName: "{name}"` |
| `GET  /api/availableActions:list` | `available_actions_list` |

Filter, sort, pagination, and `appends` parameters are identical in both transports — same JSON shape. See `mcp-patterns/references/nc-mcp-tool-map.md` for the complete mapping.

## Base URL and Authentication

All requests target the `/api/` path prefix on the NocoBase instance.

```
Base URL: ${NOCOBASE_URL}/api/
```

Authenticate every request with a Bearer token in the `Authorization` header:

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/{resource}:{action}"
```

To make a request as a specific role, add the `X-Role` header:

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "X-Role: admin" \
  "${NOCOBASE_URL}/api/{resource}:{action}"
```

## Resource & Action URL Pattern

The core URL pattern is:

```
POST|GET  ${NOCOBASE_URL}/api/{resource}:{action}
```

Where `{resource}` is a collection name or system resource, and `{action}` is the operation to perform.

### Standard Actions

Every collection resource supports these actions:

| Action | HTTP Method | Description |
|--------|-------------|-------------|
| `list` | GET | List records with pagination |
| `get` | GET | Get a single record by primary key |
| `create` | POST | Create a new record |
| `update` | POST | Update an existing record |
| `destroy` | POST | Delete a record |
| `move` | POST | Reorder a record within a sorted list |

### Smart Actions

| Action | HTTP Method | Description |
|--------|-------------|-------------|
| `firstOrCreate` | POST | Find the first matching record or create it |
| `updateOrCreate` | POST | Update a matching record or create it if none exists |

### RESTful Alternatives

NocoBase also supports standard RESTful URL patterns as an alternative:

| REST Pattern | Equivalent Resource:Action |
|-------------|---------------------------|
| `GET /api/{collection}` | `{collection}:list` |
| `GET /api/{collection}/{id}` | `{collection}:get?filterByTk={id}` |
| `POST /api/{collection}` | `{collection}:create` |
| `PUT /api/{collection}/{id}` | `{collection}:update?filterByTk={id}` |
| `DELETE /api/{collection}/{id}` | `{collection}:destroy?filterByTk={id}` |

The Resource:Action style is preferred because it is unambiguous and supports all actions including custom ones.

## Query Parameters

### filter

A JSON object with `$`-prefixed operators. Pass as a URL-encoded JSON string.

```bash
# Simple equality
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/posts:list?filter={\"status\":{\"$eq\":\"published\"}}"

# Multiple conditions (AND)
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/posts:list?filter={\"$and\":[{\"status\":{\"$eq\":\"published\"}},{\"category\":{\"$eq\":\"tech\"}}]}"

# OR conditions
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/posts:list?filter={\"$or\":[{\"status\":{\"$eq\":\"draft\"}},{\"status\":{\"$eq\":\"review\"}}]}"
```

**Association filtering** — filter by related record fields using dot notation:

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/posts:list?filter={\"author.role\":{\"$eq\":\"admin\"}}"
```

**Date filtering** — use date-specific operators like `$dateOn`, `$dateBefore`, `$dateAfter`:

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/orders:list?filter={\"createdAt\":{\"$dateOn\":\"2025-01-15\"}}"
```

See `references/filter-operators.md` for the complete list of 50+ filter operators.

### filterByTk

Filter by the primary key (usually `id`). Use for single-record operations.

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/posts:get?filterByTk=42"
```

### sort

An array of field names. Prefix with `-` for descending order.

```bash
# Sort by createdAt descending, then name ascending
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/posts:list?sort=[-createdAt,name]"
```

### page and pageSize

Pagination parameters. Pages are 1-based. Default `pageSize` is 20.

```bash
# Page 3, 50 records per page
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/posts:list?page=3&pageSize=50"
```

### fields

Select specific fields to return. Reduces response size.

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/posts:list?fields=[name,title,status]"
```

### appends

Include related/association data in the response. Without this, association fields return only foreign keys.

```bash
# Include author and tags association data
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/posts:list?appends=[author,tags]"
```

### except

Exclude specific fields from the response.

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/posts:list?except=[content,internalNotes]"
```

### paginate

Set to `false` to get all records without pagination. The response is a direct array instead of the paginated structure.

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/categories:list?paginate=false"
```

### tree

For tree-type collections, set `tree=true` to get a nested parent-child structure instead of a flat list.

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/categories:list?tree=true"
```

### updateAssociationValues

When creating or updating records with association fields, list the association names that should be updated inline.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -g "${NOCOBASE_URL}/api/orders:create?updateAssociationValues=[items,tags]" \
  -d '{ "title": "Order", "items": [{ "product": "A" }], "tags": [1, 2] }'
```

### whitelist and blacklist

Restrict which fields can be written during create or update operations.

```bash
# Only allow writing title and status
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/posts:create?whitelist=[title,status]" \
  -d '{"title": "New Post", "status": "draft", "adminOnly": "ignored"}'
```

## Response Format

All list responses follow this structure:

```json
{
  "data": [
    { "id": 1, "name": "...", "createdAt": "2025-01-01T00:00:00Z" }
  ],
  "meta": {
    "count": 150,
    "page": 1,
    "pageSize": 20,
    "totalPage": 8
  }
}
```

Single-record responses (`get`, `create`, `update`) return:

```json
{
  "data": { "id": 1, "name": "...", "createdAt": "2025-01-01T00:00:00Z" }
}
```

Destroy responses return an empty body or the count of deleted records.

For large tables (>1000 rows), NocoBase may return a simplified pagination response:

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

This uses `hasNext` instead of `count`/`totalPage` for better performance.

## Association Access Pattern

Access related records through a nested URL pattern:

```
{collection}/{sourceId}/{association}:{action}
```

Examples:

```bash
# List all comments for post 42
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/posts/42/comments:list"

# Get the author of post 42
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/posts/42/author:get"

# Add tag 7 to post 42 (many-to-many)
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/posts/42/tags:add" \
  -d '{"tk": 7}'
```

## Curl Example Patterns

### List with filtering, sorting, and pagination

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/orders:list?filter={\"status\":{\"$eq\":\"pending\"}}&sort=[-createdAt]&page=1&pageSize=10&appends=[customer]"
```

### Create a record

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/orders:create" \
  -d '{
    "title": "Order #1001",
    "status": "pending",
    "amount": 99.99,
    "customer_id": 5
  }'
```

### Update a record

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/orders:update?filterByTk=1001" \
  -d '{"status": "shipped"}'
```

### Destroy a record

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/orders:destroy?filterByTk=1001"
```

### First or create

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/tags:firstOrCreate" \
  -d '{
    "filterKeys": ["name"],
    "values": { "name": "urgent", "color": "red" }
  }'
```

### Update or create

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/settings:updateOrCreate" \
  -d '{
    "filterKeys": ["key"],
    "values": { "key": "site_title", "value": "My App" }
  }'
```

## Same request — MCP vs CLI vs HTTP

Three ways to list 10 posts ordered by newest, with the author appended:

**MCP**
```
resource_list({
  resource: "posts",
  sort: ["-createdAt"],
  page: 1,
  pageSize: 10,
  appends: ["author"]
})
```

**CLI**
```bash
nocobase-ctl resource list \
  --resource posts \
  --sort '["-createdAt"]' \
  --page 1 --page-size 10 \
  --appends '["author"]' \
  -j
```

**HTTP**
```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/posts:list?sort=[-createdAt]&page=1&pageSize=10&appends=[author]"
```

## Expression and helper utilities

For formulas, filter operators, and UID generation referenced throughout the API:

- `references/utils/formulajs.md` — computed-field formulas (SUM, AVG, IF, DATE, STRING ops, full list)
- `references/utils/mathjs.md` — advanced math expressions for numeric formulas
- `references/utils/filter-syntax.md` — all `$` operators with examples
- `references/utils/uid.md` — NocoBase UID generation (11-char alphanumeric)

## See also

- `mcp-patterns` — MCP tool catalog, `*` naming, declarative-apply family
- `api-reference` — full HTTP endpoint catalog + MCP tool catalog
- `record-operations` — CRUD patterns using these conventions
- `troubleshoot` — diagnosing filter, pagination, and auth errors
