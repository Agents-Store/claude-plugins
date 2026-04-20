---
name: flow-models
description: |
  Flow models (v2.x block engine), flow SQL queries, and template variable resolution. Use when:
  - "flow model"
  - "v2 block engine"
  - "flowModels API"
  - "save flow model"
  - "duplicate flow model"
  - "attach flow model"
  - "move flow model"
  - "flow SQL"
  - "execute SQL in NocoBase"
  - "resolve variables"
  - "template variables"
  - "block engine v2"
  - "NocoBase v2 blocks"
---

# Flow Models (v2.x Block Engine)

The new block engine in NocoBase v2.x. Flow models replace the legacy `uiSchemas` for block-level UI storage. They use the same tree structure (Closure Table) but store data in the `flowModels` collection with `uid` as primary key and `options` as the magic JSON attribute.

> **For step-by-step page and block creation workflows** (creating Modern Pages, adding table/form blocks, configuring columns and buttons), use the **ux-constructor** skill with `flow_surfaces_apply_blueprint`. This skill covers the low-level flow model operations for when the high-level surface tools aren't enough.

## MCP tools for flow-model-level introspection

When `flow_surfaces_apply_blueprint` / `flow_surfaces_add_*` don't fit, drop down to these MCP tools to read and shape flow models directly:

| Task | MCP tool | Purpose |
|------|----------|---------|
| Get a subtree | `flow_surfaces_get` | Read one surface node and its subtree |
| Enumerate available children | `flow_surfaces_catalog` | What can be added at this target |
| Full structural dump | `flow_surfaces_describe_surface` | Everything about a surface |
| Live context at a node | `flow_surfaces_context` | Scope (form, resource, filter) at a node — needed for reaction design |
| Reaction meta | `flow_surfaces_get_reaction_meta` | Source/target paths available for reactions |
| Compose partial input | `flow_surfaces_compose` | Build a subtree from partial inputs |
| Low-level configure | `flow_surfaces_configure` | Apply a configure payload to a node |
| Update surface settings | `flow_surfaces_update_settings` | Tab/popup settings |
| Lowest-level mutation | `flow_surfaces_mutate` | Escape hatch for anything the higher tools can't do |

For anything blueprint-shaped (whole pages, named blocks, reactions), stay in `ux-constructor`. Reach for this skill only when you need the raw flow model layer.

## Authentication

All requests require the API key header:

```
Authorization: Bearer ${NOCOBASE_API_KEY}
```

Base URL: `${NOCOBASE_URL}/api/`

## Flow Model Structure

**Resource name:** `flowModels`

### Collection Fields

| Field | Type | Description |
|-------|------|-------------|
| `uid` | uid | Primary key (auto-generated if not provided) |
| `name` | string | Node name (auto-generated uid if not provided) |
| `options` | json | Model options (magic attribute — merged into root) |

### Options Structure

The `options` JSON typically contains:

| Property | Type | Description |
|----------|------|-------------|
| `use` | string | Model class name (e.g. `TableBlockModel`, `FormBlockModel`, `RouteModel`, `ReferenceBlockModel`) |
| `stepParams` | object | Step parameters for the model |
| `title` | string | Display title |
| `description` | string | Description |
| `x-component-props` | object | Component props |
| `x-decorator-props` | object | Decorator props |

## Core Operations

### Find One

Retrieves a single flow model by `uid` or by `parentId`.

```bash
curl -X GET "${NOCOBASE_URL}/api/flowModels:findOne?uid=model-abc123" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

By parentId (find child):

```bash
curl -X GET "${NOCOBASE_URL}/api/flowModels:findOne?parentId=parent-uid&subKey=properties" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `uid` | string | No | Flow model uid (use this OR `parentId`) |
| `parentId` | string | No | Parent model uid (finds child node) |
| `subKey` | string | No | Child key type filter (e.g. `properties`, `items`) |
| `includeAsyncNode` | boolean | No | Include async child nodes (default: `false`) |

Response returns the flow model tree:

```json
{
  "data": {
    "uid": "model-abc123",
    "name": "model-abc123",
    "use": "TableBlockModel",
    "stepParams": { ... },
    "properties": {
      "actions": {
        "uid": "model-def456",
        "use": "ActionBarModel"
      }
    }
  }
}
```

**ACL:** `loggedIn`

### Save (Upsert)

Creates or updates a flow model. If a model with the given `uid` exists, updates it; otherwise creates it. Handles nested children.

```bash
curl -X POST "${NOCOBASE_URL}/api/flowModels:save" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "model-abc123",
    "name": "model-abc123",
    "use": "FormBlockModel",
    "stepParams": {
      "dataSource": {
        "dataSourceKey": "main",
        "collectionName": "users"
      }
    },
    "title": "User Form",
    "properties": {
      "fields": {
        "uid": "model-fields-1",
        "use": "FormFieldListModel"
      }
    }
  }'
```

With parent attachment (create as child of existing model):

```bash
curl -X POST "${NOCOBASE_URL}/api/flowModels:save" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "new-child-model",
    "parentId": "parent-model-uid",
    "subKey": "properties",
    "use": "FormFieldModel",
    "stepParams": {
      "fieldPath": "users.name"
    }
  }'
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `uid` | string | No | Model uid (auto-generated if omitted) |
| `name` | string | No | Model name |
| `use` | string | No | Model class name |
| `stepParams` | object | No | Step parameters |
| `title` | string | No | Display title |
| `parentId` | string | No | Parent model uid (for attaching as child) |
| `subKey` | string | No | Child key under parent (e.g. `properties`) |
| `properties` | object | No | Nested child models |
| `*` | any | No | Any other options (stored in `options` JSON) |

Response returns the uid: `{ "data": "model-abc123" }`

**ACL:** Requires `ui.flowModels` snippet permission. **Audit logged.**

### Duplicate

Creates a deep copy of a flow model and all its descendants with new uids.

```bash
curl -X POST "${NOCOBASE_URL}/api/flowModels:duplicate?uid=model-abc123" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Returns the duplicated model tree with new uids.

**ACL:** Requires `ui.flowModels` snippet permission. **Audit logged.**

### Attach

Attaches an existing flow model as a child of another model.

```bash
curl -X POST "${NOCOBASE_URL}/api/flowModels:attach" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "child-model-uid",
    "parentId": "parent-model-uid",
    "subKey": "properties",
    "subType": "object",
    "position": "last"
  }'
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `uid` | string | Yes | uid of the model to attach |
| `parentId` | string | Yes | uid of the target parent model |
| `subKey` | string | Yes | Key under which to attach (e.g. `properties`, `items`) |
| `subType` | string | Yes | `"object"` (keyed by name) or `"array"` (ordered list) |
| `position` | string | No | `"first"`, `"last"`, or a target position object |

**ACL:** Requires `ui.flowModels` snippet permission.

### Move

Repositions a flow model relative to another model (drag-and-drop).

```bash
curl -X POST "${NOCOBASE_URL}/api/flowModels:move" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "sourceId": "model-to-move",
    "targetId": "reference-model",
    "position": "after"
  }'
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sourceId` | string | Yes | uid of the model to move |
| `targetId` | string | Yes | uid of the reference model |
| `position` | string | Yes | `"before"` or `"after"` |

**ACL:** Requires `ui.flowModels` snippet permission.

### Destroy

Removes a flow model and all its descendants.

```bash
curl -X POST "${NOCOBASE_URL}/api/flowModels:destroy?filterByTk=model-abc123" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

**ACL:** Requires `ui.flowModels` snippet permission. **Audit logged.**

## Inherited Schema Actions

The `flowModels` resource inherits all tree-manipulation actions from `uiSchemas`. They work identically but operate on the `flowModels` collection.

| Action | URL |
|--------|-----|
| getJsonSchema | `GET /api/flowModels:getJsonSchema/<uid>` |
| getProperties | `GET /api/flowModels:getProperties/<uid>` |
| getParentJsonSchema | `GET /api/flowModels:getParentJsonSchema/<uid>` |
| getParentProperty | `GET /api/flowModels:getParentProperty/<uid>` |
| insert | `POST /api/flowModels:insert` |
| insertNewSchema | `POST /api/flowModels:insertNewSchema` |
| patch | `POST /api/flowModels:patch` |
| batchPatch | `POST /api/flowModels:batchPatch` |
| remove | `POST /api/flowModels:remove/<uid>` |
| clearAncestor | `POST /api/flowModels:clearAncestor/<uid>` |
| insertAdjacent | `POST /api/flowModels:insertAdjacent/<uid>?position=X` |
| insertBeforeBegin | `POST /api/flowModels:insertBeforeBegin/<uid>` |
| insertAfterBegin | `POST /api/flowModels:insertAfterBegin/<uid>` |
| insertBeforeEnd | `POST /api/flowModels:insertBeforeEnd/<uid>` |
| insertAfterEnd | `POST /api/flowModels:insertAfterEnd/<uid>` |
| initializeActionContext | `POST /api/flowModels:initializeActionContext` |

**Key difference from uiSchemas:** The `insertAdjacent` payload uses the `options` key instead of `schema`:

```bash
curl -X POST "${NOCOBASE_URL}/api/flowModels:insertAdjacent/target-uid?position=beforeEnd" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "options": {
      "uid": "new-block-uid",
      "use": "TableBlockModel",
      "stepParams": {
        "dataSource": { "dataSourceKey": "main", "collectionName": "orders" }
      }
    }
  }'
```

For full parameter documentation of inherited actions, see the **ui-schemas** skill.

## Flow SQL

Execute and manage SQL queries within flow models.

**Resource name:** `flowSql`

### Save Flow SQL

Store a SQL query with Liquid template support.

```bash
curl -X POST "${NOCOBASE_URL}/api/flowSql:save" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "sql-block-uid",
    "sql": "SELECT * FROM {{users}} WHERE status = :status",
    "dataSourceKey": "main"
  }'
```

**ACL:** Requires `ui.flowSql` snippet permission. **Audit logged.**

### Run Flow SQL

Execute a saved SQL query with bind parameters and Liquid context.

```bash
curl -X POST "${NOCOBASE_URL}/api/flowSql:runById" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "sql-block-uid",
    "type": "SELECT",
    "filter": {},
    "bind": { "status": "active" },
    "liquidContext": { "users": "public.users" },
    "dataSourceKey": "main"
  }'
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `uid` | string | Yes | Flow SQL identifier |
| `type` | string | No | SQL type (`SELECT`, `INSERT`, etc.) |
| `filter` | object | No | Additional filters |
| `bind` | object | No | Bind parameters for the query |
| `liquidContext` | object | No | Liquid template context variables |
| `dataSourceKey` | string | No | Data source key override |

**ACL:** `loggedIn`

### Get Bind Parameters

Retrieve the bind parameters and liquid context for a saved SQL query.

```bash
curl -X GET "${NOCOBASE_URL}/api/flowSql:getBind?uid=sql-block-uid" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Response:

```json
{
  "data": {
    "bind": { "status": null },
    "liquidContext": { "users": "public.users" }
  }
}
```

**ACL:** `loggedIn`

## Template Variables

Resolve context variables in JSON templates used by flow models for dynamic data.

**Resource name:** `variables`

### Resolve Variables

Single resolution:

```bash
curl -X POST "${NOCOBASE_URL}/api/variables:resolve" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "template": {
      "title": "{{ $nRecord.name }}",
      "count": "{{ $nPopup.count }}"
    },
    "contextParams": {
      "$nRecord": { "collectionName": "users", "filterByTk": 1 }
    }
  }'
```

Batch resolution:

```bash
curl -X POST "${NOCOBASE_URL}/api/variables:resolve" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "batch": [
      {
        "id": "var1",
        "template": "{{ $nRecord.name }}",
        "contextParams": { "$nRecord": { "collectionName": "users", "filterByTk": 1 } }
      },
      {
        "id": "var2",
        "template": "{{ $nRecord.email }}",
        "contextParams": { "$nRecord": { "collectionName": "users", "filterByTk": 2 } }
      }
    ]
  }'
```

Either `template` or `batch` is required, not both.

Batch response:

```json
{
  "data": {
    "results": [
      { "id": "var1", "result": "John Doe" },
      { "id": "var2", "result": "jane@example.com" }
    ]
  }
}
```

**ACL:** `loggedIn`

## Templates

Flow model templates (`flowModelTemplates` resource) allow saving reusable block configurations. See the **ui-schemas** skill for template CRUD operations (list, get, create, update, destroy) and `TEMPLATE_IN_USE` validation. For flow-surfaces templates via MCP, see `ux-constructor` (`flow_surfaces_{list,get,save,update,destroy}_template`).

For detailed endpoint reference, see `references/flow-model-endpoints.md`.

## See also

- `ux-constructor` — default v2 UI authoring (start here for most tasks)
- `ui-builder-index` — router between UI authoring skills
- `ui-schemas` — legacy v1 UI schemas
- `mcp-patterns` — transport conventions
- `routes-and-menus` — route/menu CRUD that anchors a page
