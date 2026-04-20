---
name: ui-schemas
description: |
  UI schema operations — JSON-based UI definitions, component trees, themes, maps, and block templates. Use when:
  - "read UI schema"
  - "modify page layout"
  - "insert UI components"
  - "manage themes"
  - "save schema templates"
  - "configure map settings"
  - "get parent schema"
  - "flow model templates"
  - "block templates"
  - "initialize action context"
  - "insert before/after"
---

# UI Schemas

Manage NocoBase Classic (v1) user interface definitions through the HTTP API. UI schemas are JSON-based structures that define visual components for legacy v1 pages — `type: "page"`, `x-component: "Page"`, and `uiSchemas:insertAdjacent`-based block insertion.

> **⚠️ Legacy (v1) surface.** For new NocoBase work, use `ux-constructor` (Modern v2) with `flow_surfaces_apply_blueprint` and related MCP tools — v2 is simpler, idempotent, and the default for current NocoBase versions. Use `ui-schemas` only when:
> - maintaining an existing v1 page that cannot be migrated yet
> - working with themes (`uiSchemaTemplates` for themes lives here)
> - managing block templates (legacy `uiSchemaTemplates` resource)
> - the `initializeActionContext` action is needed for a v1 block
>
> There is no MCP path for v1 UI schemas. HTTP is the only transport.

## Authentication

All requests require the API key header:

```
Authorization: Bearer ${NOCOBASE_API_KEY}
```

Base URL for all endpoints: `${NOCOBASE_URL}/api/`

## What Are UI Schemas

NocoBase stores its entire user interface as a tree of JSON schema nodes. Each node has a unique `uid` (also called `x-uid`) and can contain:

- `type` — schema type (`void`, `object`, `array`, `string`, `number`, `boolean`)
- `x-component` — the React component to render (e.g., `Grid`, `Form`, `Table`, `Action`)
- `x-component-props` — props passed to the component
- `x-decorator` — wrapper component (e.g., `BlockItem`, `FormItem`)
- `x-decorator-props` — props for the wrapper
- `properties` — child schema nodes (nested components)
- `x-uid` — unique identifier for addressing this node
- `x-designer` — design-time configurator component
- `x-initializer` — initializer component for adding child blocks
- `x-settings` — settings configurator component
- `x-toolbar` — toolbar component
- `x-async` — whether to load this node asynchronously (lazy load)
- `x-index` — sort order among siblings
- `x-server-hooks` — server-side hook definitions (array)
- `x-action` — action identifier (for action buttons)
- `x-action-context` — context data for action execution
- `x-collection-field` — associated collection field path (e.g. `orders.status`)

Every page, menu item, form field, table column, and button in the NocoBase UI corresponds to a schema node.

## V2.x Migration — Use ux-constructor for New Pages

In NocoBase v2.x, the new **Flow Models** system (`flowModels` resource) replaces `uiSchemas` for block-level UI storage. **For creating new pages, table blocks, form blocks, and columns, use the ux-constructor skill** — it documents the verified Modern Page (v2) workflow using `flowPage` routes and `flowModels:save`.

The `uiSchemas` resource is still used for the page-level schema node (`x-component: "FlowRoute"`) but blocks are managed via flow models. See the **flow-models** skill for low-level flow model operations, or the **ux-constructor** skill for complete page creation workflows.

## Core Operations

### Get JSON Schema

Retrieve the full schema tree starting from a given node.

```bash
curl -X GET "${NOCOBASE_URL}/api/uiSchemas:getJsonSchema/abc123uid" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

To include nodes marked as `x-async` (lazy-loaded), add `includeAsyncNode=true`:

```bash
curl -X GET "${NOCOBASE_URL}/api/uiSchemas:getJsonSchema/abc123uid?includeAsyncNode=true" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Without `includeAsyncNode`, results are cached. With it, you get the complete tree including lazy nodes.

Returns the complete nested JSON schema from the specified `uid` downward, including all child properties.

### Get Properties

Retrieve only the immediate properties (children) of a schema node.

```bash
curl -X GET "${NOCOBASE_URL}/api/uiSchemas:getProperties/abc123uid" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Use this when you only need the direct children, not the full nested tree.

### Get Parent JSON Schema

Retrieve the full schema of a node's parent. Returns `null` if the node is a root node.

```bash
curl -X GET "${NOCOBASE_URL}/api/uiSchemas:getParentJsonSchema/abc123uid" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### Get Parent Property

Retrieve the parent property metadata for a given node.

```bash
curl -X GET "${NOCOBASE_URL}/api/uiSchemas:getParentProperty/abc123uid" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### Insert Root Schema

Create a new root-level UI schema node.

```bash
curl -X POST "${NOCOBASE_URL}/api/uiSchemas:insert" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "void",
    "x-component": "Page",
    "x-component-props": {
      "title": "My Custom Page"
    },
    "properties": {}
  }'
```

Creates a new top-level schema node. The system assigns a `x-uid` automatically.

### Insert New Schema (Bulk)

Optimized bulk-insert approach using SQL batch insert. Similar to `insert` but faster for large schemas.

```bash
curl -X POST "${NOCOBASE_URL}/api/uiSchemas:insertNewSchema" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "void",
    "x-component": "Table",
    "properties": {
      "actions": {
        "type": "void",
        "x-component": "ActionBar"
      }
    }
  }'
```

### Remove Schema

Delete a schema node and all its descendants.

```bash
curl -X POST "${NOCOBASE_URL}/api/uiSchemas:remove/abc123uid" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Permanently removes the node identified by `uid` and every schema nested beneath it.

### Patch Schema

Update a single schema node's properties.

```bash
curl -X POST "${NOCOBASE_URL}/api/uiSchemas:patch" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "x-uid": "abc123uid",
    "x-component-props": {
      "title": "Updated Page Title"
    }
  }'
```

Merges the provided fields into the existing schema node. Include `x-uid` in the body to identify the target node.

### Batch Patch

Update multiple schema nodes in a single request.

```bash
curl -X POST "${NOCOBASE_URL}/api/uiSchemas:batchPatch" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "x-uid": "uid1",
      "x-component-props": { "title": "Section A" }
    },
    {
      "x-uid": "uid2",
      "x-component-props": { "title": "Section B" }
    }
  ]'
```

Send an array of schema patches. Each object must include `x-uid`.

### Insert Adjacent

Position a new schema node relative to an existing node.

```bash
curl -X POST "${NOCOBASE_URL}/api/uiSchemas:insertAdjacent/abc123uid?position=afterEnd" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "schema": {
      "type": "void",
      "x-component": "Grid.Row",
      "properties": {
        "col1": {
          "type": "void",
          "x-component": "Grid.Col",
          "properties": {}
        }
      }
    }
  }'
```

Position options:
- `beforeBegin` — insert as a sibling **before** the target node
- `afterBegin` — insert as the **first child** of the target node
- `beforeEnd` — insert as the **last child** of the target node
- `afterEnd` — insert as a sibling **after** the target node

This is the primary method for adding new components to an existing page layout.

**Advanced parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `wrap` | object | Optional wrapper schema; the new schema is inserted inside the wrapper |
| `removeParentsIfNoChildren` | boolean | If `true`, removes parent nodes that become empty after a move |
| `breakRemoveOn` | object | Stop criteria for parent removal (matched against schema properties) |

### Convenience Insert Shorthands

These are shorthand equivalents for `insertAdjacent` with a fixed position:

```bash
# Insert before the target (as sibling)
curl -X POST "${NOCOBASE_URL}/api/uiSchemas:insertBeforeBegin/targetUid" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{ "schema": { "type": "void", "x-component": "Divider" } }'

# Insert as first child of the target
curl -X POST "${NOCOBASE_URL}/api/uiSchemas:insertAfterBegin/targetUid" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{ "schema": { "type": "void", "x-component": "FormItem" } }'

# Insert as last child of the target (most common for appending blocks)
curl -X POST "${NOCOBASE_URL}/api/uiSchemas:insertBeforeEnd/targetUid" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{ "schema": { "type": "void", "x-component": "Grid.Row" } }'

# Insert after the target (as sibling)
curl -X POST "${NOCOBASE_URL}/api/uiSchemas:insertAfterEnd/targetUid" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{ "type": "void", "x-component": "Action", "title": "Add New" }'
```

### Initialize Action Context

Sets the `x-action-context` on a schema node, but only if it is not already set. Used to lazily initialize action popup contexts.

```bash
curl -X POST "${NOCOBASE_URL}/api/uiSchemas:initializeActionContext" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "x-uid": "action-btn-uid",
    "x-action-context": {
      "dataSource": "main",
      "collection": "users"
    }
  }'
```

Only initializes if the `x-action-context` is currently empty — will not overwrite an existing value.

### Save as Template

Save a schema subtree as a reusable template.

```bash
curl -X POST "${NOCOBASE_URL}/api/uiSchemas:saveAsTemplate" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "abc123uid",
    "name": "My Form Template",
    "key": "my-form-template"
  }'
```

### Clear Ancestor

Detach a schema node from its parent, making it a root node.

```bash
curl -X POST "${NOCOBASE_URL}/api/uiSchemas:clearAncestor/abc123uid" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

## Theme Management

NocoBase supports customizable themes that control colors, typography, spacing, and other visual properties.

### List Themes

```bash
curl -X GET "${NOCOBASE_URL}/api/themeConfig:list" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### Create Theme

```bash
curl -X POST "${NOCOBASE_URL}/api/themeConfig:create" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Corporate Blue",
    "config": {
      "token": {
        "colorPrimary": "#1677ff",
        "borderRadius": 6,
        "fontSize": 14,
        "colorBgContainer": "#ffffff",
        "colorBgLayout": "#f5f5f5"
      }
    },
    "default": false
  }'
```

Theme config uses Ant Design token system. Common tokens:
- `colorPrimary` — primary brand color
- `colorSuccess` / `colorWarning` / `colorError` — status colors
- `borderRadius` — default border radius in pixels
- `fontSize` — base font size in pixels
- `colorBgContainer` — background for cards, forms, tables
- `colorBgLayout` — page background

### Update Theme

```bash
curl -X POST "${NOCOBASE_URL}/api/themeConfig:update?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "token": {
        "colorPrimary": "#722ed1"
      }
    }
  }'
```

### Destroy Theme

```bash
curl -X POST "${NOCOBASE_URL}/api/themeConfig:destroy?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

## Map Configuration

Configure map provider settings for map-type fields and blocks.

### Get Map Configuration

```bash
curl -X GET "${NOCOBASE_URL}/api/map-configuration:get" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### Set Map Configuration

```bash
curl -X POST "${NOCOBASE_URL}/api/map-configuration:set" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "amap",
    "accessKey": "your-map-api-key",
    "securityJsCode": "your-security-code"
  }'
```

Supported map types: `amap` (AMap/Gaode), `google` (Google Maps).

## Common Workflows

### Inspect a Page Layout

```
1. GET uiSchemas:getJsonSchema/{pageUid} → retrieve full page schema
2. Examine the properties tree to understand the component hierarchy
3. Identify x-uid values for components you want to modify
```

### Add a Block to an Existing Page

```
1. GET uiSchemas:getProperties/{pageUid} → find the Grid container uid
2. POST uiSchemas:insertAdjacent/{gridUid}?position=beforeEnd → add a new row
3. Inside the row, nest Grid.Col with your block component
```

### Update Component Properties

```
1. GET uiSchemas:getJsonSchema/{componentUid} → verify current state
2. POST uiSchemas:patch → update specific x-component-props
```

### Create a Custom Theme

```
1. GET themeConfig:list → check existing themes
2. POST themeConfig:create → create with Ant Design tokens
3. Set "default": true on the new theme to apply globally
```

For detailed reference on each operation with full request/response formats, see `references/ui-schema-operations.md`.

## Block Templates

NocoBase has two template systems for reusable UI blocks.

### Legacy Templates (uiSchemaTemplates)

The original template system. Templates reference schema nodes by `uid`.

```bash
# List all templates
curl -X GET "${NOCOBASE_URL}/api/uiSchemaTemplates:list" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"

# Get a specific template
curl -X GET "${NOCOBASE_URL}/api/uiSchemaTemplates:get?filterByTk=template-key" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Template fields: `key` (primary key), `name`, `componentName`, `associationName`, `resourceName`, `collectionName`, `dataSourceKey`, `uid` (foreign key to `uiSchemas.x-uid`).

### Flow Model Templates (v2.x+)

The new template system with usage tracking and reference block support.

**List templates** (with search and pagination):

```bash
curl -X GET "${NOCOBASE_URL}/api/flowModelTemplates:list?page=1&pageSize=20&search=my+template" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

**Create a template** from an existing block:

```bash
curl -X POST "${NOCOBASE_URL}/api/flowModelTemplates:create" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "User Form Template",
    "description": "Reusable form block for user creation",
    "targetUid": "block_uid_to_template",
    "useModel": "FormBlockModel",
    "type": "block",
    "dataSourceKey": "main",
    "collectionName": "users",
    "detachParent": true
  }'
```

**Update a template:**

```bash
curl -X POST "${NOCOBASE_URL}/api/flowModelTemplates:update?filterByTk=tpl-uid" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Template Name",
    "description": "Updated description"
  }'
```

Updating syncs template metadata to all reference blocks using this template.

**Destroy a template:**

```bash
curl -X POST "${NOCOBASE_URL}/api/flowModelTemplates:destroy?filterByTk=tpl-uid" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Fails with HTTP 400 and code `TEMPLATE_IN_USE` if `usageCount > 0`. You must remove all blocks using the template before deleting it.

Key fields: `uid`, `name`, `description`, `targetUid`, `useModel` (e.g. `TableBlockModel`, `FormBlockModel`), `type`, `dataSourceKey`, `collectionName`, `usageCount`.

## Best Practices

1. **Read before modifying** — always `getJsonSchema` first to understand the current structure.
2. **Use insertAdjacent** — prefer `insertAdjacent` with position options over manually constructing full schema trees.
3. **Patch minimally** — send only the properties you want to change in `patch` calls.
4. **Use batch patch** — when updating multiple nodes, use `batchPatch` to reduce API calls.
5. **Keep x-uid references** — store uid values when inspecting schemas; you need them for all subsequent operations.
6. **Test on non-production** — UI schema changes are immediate and affect all users; test in a staging environment first.
7. **Save templates** — use `saveAsTemplate` for reusable page layouts.
8. **Theme tokens** — use standard Ant Design tokens for consistent theming.

## See also

- `ux-constructor` — Modern v2 UI authoring (preferred for all new work)
- `ui-builder-index` — router between UI authoring skills
- `flow-models` — v2 block engine (replaces `uiSchemas` for block-level storage in v2)
- `mcp-patterns` — note that there is no MCP path for legacy v1 UI schemas
- `troubleshoot` — debugging v1 rendering issues
