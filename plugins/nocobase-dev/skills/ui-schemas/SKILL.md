---
name: ui-schemas
description: UI schema operations — JSON-based UI definitions, component trees, themes, maps. This skill should be used when the user asks to "read UI schema", "modify page layout", "insert UI components", "manage themes", "save schema templates", or "configure map settings" in NocoBase.
---

# UI Schemas

Manage NocoBase V2 user interface definitions through the HTTP API. UI schemas are JSON-based structures that define every visual component — pages, forms, tables, menus, blocks, and their layout.

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

Every page, menu item, form field, table column, and button in the NocoBase UI corresponds to a schema node.

## Core Operations

### Get JSON Schema

Retrieve the full schema tree starting from a given node.

```bash
curl -X GET "${NOCOBASE_URL}/api/uiSchemas:getJsonSchema/abc123uid" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Returns the complete nested JSON schema from the specified `uid` downward, including all child properties.

### Get Properties

Retrieve only the immediate properties (children) of a schema node.

```bash
curl -X GET "${NOCOBASE_URL}/api/uiSchemas:getProperties/abc123uid" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Use this when you only need the direct children, not the full nested tree.

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

## Best Practices

1. **Read before modifying** — always `getJsonSchema` first to understand the current structure.
2. **Use insertAdjacent** — prefer `insertAdjacent` with position options over manually constructing full schema trees.
3. **Patch minimally** — send only the properties you want to change in `patch` calls.
4. **Use batch patch** — when updating multiple nodes, use `batchPatch` to reduce API calls.
5. **Keep x-uid references** — store uid values when inspecting schemas; you need them for all subsequent operations.
6. **Test on non-production** — UI schema changes are immediate and affect all users; test in a staging environment first.
7. **Save templates** — use `saveAsTemplate` for reusable page layouts.
8. **Theme tokens** — use standard Ant Design tokens for consistent theming.
