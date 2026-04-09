# NocoBase UX Constructor — Backend API Reference

Complete reference for all backend API endpoints used by the NocoBase visual UI constructor.

---

## Table of Contents

1. [Overview & Authentication](#1-overview--authentication)
2. [UI Schema Management](#2-ui-schema-management)
3. [UI Schema Templates (Legacy)](#3-ui-schema-templates-legacy)
4. [Flow Models (v2.x Block Engine)](#4-flow-models-v2x-block-engine)
5. [Flow Model Templates](#5-flow-model-templates)
6. [Desktop Routes (Pages & Menus)](#6-desktop-routes-pages--menus)
7. [Mobile Routes](#7-mobile-routes)
8. [Collection & Field Management](#8-collection--field-management)
9. [System Settings](#9-system-settings)
10. [Data Visualization (Charts)](#10-data-visualization-charts)
11. [Roles & Permissions](#11-roles--permissions)
12. [Application](#12-application)
13. [Generic CRUD Actions](#13-generic-crud-actions)

---

## 1. Overview & Authentication

### Base URL

```
https://{nocobase-url}/api
```

All endpoints are prefixed with `/api`.

### URL Pattern

NocoBase uses a `resource:action` URL convention:

```
GET  /api/<resource>:<action>
POST /api/<resource>:<action>
```

For nested resources (associations):

```
GET  /api/<resource>/<resourceOf>/<action>
POST /api/<resource>/<resourceOf>/<action>
```

### HTTP Method Rules

| Action Names     | HTTP Method |
|------------------|-------------|
| `get`, `list`    | `GET`       |
| Everything else  | `POST`      |

### Authentication Headers

All authenticated requests require:

```
Authorization: Bearer <jwt_token>
```

Optional headers:

| Header            | Type   | Description                        |
|-------------------|--------|------------------------------------|
| `X-Role`          | string | Current active role name           |
| `X-Locale`        | string | Locale code (e.g. `en-US`, `zh-CN`)|
| `X-Authenticator` | string | Authentication provider name       |

### Query Parameter Serialization

- Arrays use bracket format: `arrayFormat=brackets` (e.g. `ids[]=1&ids[]=2`)
- Null values are preserved: `strictNullHandling=true`
- Filter objects are JSON-stringified: `filter={"name":"users"}`

---

## 2. UI Schema Management

The core of the visual constructor. UI schemas are stored as a tree structure using a Closure Table pattern. Each node has a unique `x-uid` identifier.

**Resource name:** `uiSchemas`

### Schema Node Structure

Every UI schema node can contain these properties:

| Property             | Type    | Description                                                  |
|----------------------|---------|--------------------------------------------------------------|
| `x-uid`              | string  | Unique identifier (auto-generated if not provided)           |
| `name`               | string  | Node name (auto-generated uid if not provided)               |
| `type`               | string  | JSON Schema type (`void`, `object`, `array`, `string`, etc.) |
| `title`              | string  | Display title                                                |
| `x-component`        | string  | React component name (e.g. `Table`, `Form`, `Menu`)         |
| `x-component-props`  | object  | Props passed to the component                                |
| `x-decorator`        | string  | Wrapper component name (e.g. `CardItem`, `BlockItem`)        |
| `x-decorator-props`  | object  | Props passed to the decorator                                |
| `x-designer`         | string  | Design-time configurator component                           |
| `x-initializer`      | string  | Initializer component for adding child blocks                |
| `x-settings`         | string  | Settings configurator component                              |
| `x-toolbar`          | string  | Toolbar component                                            |
| `x-async`            | boolean | Whether to load this node asynchronously (lazy load)         |
| `x-index`            | number  | Sort order among siblings                                    |
| `x-server-hooks`     | array   | Server-side hook definitions                                 |
| `x-action`           | string  | Action identifier (for action buttons)                       |
| `x-action-context`   | object  | Context data for action execution                            |
| `x-collection-field` | string  | Associated collection field path                             |
| `properties`         | object  | Child schema nodes (keyed by name)                           |

---

### 2.1 Get JSON Schema

Retrieves the full JSON schema tree for a given node.

```bash
curl -X GET 'https://{nocobase-url}/api/uiSchemas:getJsonSchema/<x-uid>' \
  -H 'Authorization: Bearer <token>'
```

**With async nodes included:**

```bash
curl -X GET 'https://{nocobase-url}/api/uiSchemas:getJsonSchema/<x-uid>?includeAsyncNode=true' \
  -H 'Authorization: Bearer <token>'
```

| Parameter          | Type    | Required | Description                                              |
|--------------------|---------|----------|----------------------------------------------------------|
| `<x-uid>` (URL)   | string  | Yes      | The `x-uid` of the root schema node (resourceIndex)      |
| `includeAsyncNode` | boolean | No       | If `true`, includes nodes marked as `x-async`. Default: `false`. When `false`, results are cached. |

**Response:** Full JSON schema tree object.

```json
{
  "data": {
    "type": "void",
    "x-uid": "abc123",
    "x-component": "Grid",
    "x-async": false,
    "x-index": 1,
    "properties": {
      "row1": {
        "type": "void",
        "x-uid": "def456",
        "x-component": "Grid.Row",
        "x-index": 1,
        "properties": {
          "col1": {
            "type": "void",
            "x-uid": "ghi789",
            "x-component": "Grid.Col",
            "x-index": 1
          }
        }
      }
    }
  }
}
```

**ACL:** `loggedIn` (any authenticated user)

---

### 2.2 Get Properties

Retrieves only the properties (child nodes) of a schema node (cached).

```bash
curl -X GET 'https://{nocobase-url}/api/uiSchemas:getProperties/<x-uid>' \
  -H 'Authorization: Bearer <token>'
```

| Parameter        | Type   | Required | Description                            |
|------------------|--------|----------|----------------------------------------|
| `<x-uid>` (URL) | string | Yes      | The `x-uid` of the parent schema node  |

**Response:** Properties object of the node.

```json
{
  "data": {
    "type": "void",
    "x-uid": "abc123",
    "properties": {
      "child1": { "type": "void", "x-uid": "c1", "x-component": "FormItem" },
      "child2": { "type": "void", "x-uid": "c2", "x-component": "FormItem" }
    }
  }
}
```

**ACL:** `loggedIn`

---

### 2.3 Get Parent JSON Schema

Retrieves the full schema of the parent node.

```bash
curl -X GET 'https://{nocobase-url}/api/uiSchemas:getParentJsonSchema/<x-uid>' \
  -H 'Authorization: Bearer <token>'
```

| Parameter        | Type   | Required | Description                        |
|------------------|--------|----------|------------------------------------|
| `<x-uid>` (URL) | string | Yes      | The `x-uid` of the child node     |

**Response:** Parent schema tree or `null` if root node.

**ACL:** `loggedIn`

---

### 2.4 Get Parent Property

Retrieves the parent property metadata for a given node.

```bash
curl -X GET 'https://{nocobase-url}/api/uiSchemas:getParentProperty/<x-uid>' \
  -H 'Authorization: Bearer <token>'
```

| Parameter        | Type   | Required | Description                        |
|------------------|--------|----------|------------------------------------|
| `<x-uid>` (URL) | string | Yes      | The `x-uid` of the child node     |

**Response:** Parent schema tree or `null`.

---

### 2.5 Insert Schema

Inserts a new complete schema tree. The schema and all nested `properties` are recursively stored as individual nodes.

```bash
curl -X POST 'https://{nocobase-url}/api/uiSchemas:insert' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "void",
    "name": "myBlock",
    "x-component": "CardItem",
    "x-decorator": "BlockItem",
    "x-component-props": {
      "title": "My Card"
    },
    "properties": {
      "grid1": {
        "type": "void",
        "x-component": "Grid",
        "properties": {
          "row1": {
            "type": "void",
            "x-component": "Grid.Row"
          }
        }
      }
    }
  }'
```

| Parameter  | Type   | Required | Description                                                     |
|------------|--------|----------|-----------------------------------------------------------------|
| `values`   | object | Yes      | The schema object (request body). `x-uid` and `name` are auto-generated if omitted. |

**Response:** The inserted schema tree with generated `x-uid` values.

**ACL:** Requires `ui.uiSchemas` snippet permission.

---

### 2.6 Insert New Schema

Inserts a new schema using a fast bulk-insert approach (SQL batch insert). Similar to `insert` but optimized for new schemas.

```bash
curl -X POST 'https://{nocobase-url}/api/uiSchemas:insertNewSchema' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
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

| Parameter | Type   | Required | Description        |
|-----------|--------|----------|--------------------|
| `values`  | object | Yes      | The schema object  |

**Response:** The inserted schema tree.

**ACL:** Requires `ui.uiSchemas` snippet permission.

---

### 2.7 Patch Schema

Updates an existing schema node. If `properties` is included, child nodes are traversed and updated in-place.

```bash
curl -X POST 'https://{nocobase-url}/api/uiSchemas:patch' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "x-uid": "abc123",
    "title": "Updated Title",
    "x-component-props": {
      "bordered": true
    }
  }'
```

**With nested properties update:**

```bash
curl -X POST 'https://{nocobase-url}/api/uiSchemas:patch' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "x-uid": "abc123",
    "title": "Updated Block",
    "properties": {
      "child1": {
        "title": "Updated Child",
        "x-component-props": { "size": "large" }
      }
    }
  }'
```

| Parameter | Type   | Required | Description                                                     |
|-----------|--------|----------|-----------------------------------------------------------------|
| `values`  | object | Yes      | Partial schema object. Must include `x-uid` to identify target. |

**Key fields in values:**

| Field                | Type   | Description                              |
|----------------------|--------|------------------------------------------|
| `x-uid`              | string | **Required.** Identifies the target node |
| `title`              | string | Updated title                            |
| `x-component-props`  | object | Updated component props (merged)         |
| `x-decorator-props`  | object | Updated decorator props (merged)         |
| `x-server-hooks`     | array  | Updated server hooks                     |
| `x-action-context`   | object | Updated action context                   |
| `properties`         | object | Nested property updates (recursive)      |

**Response:** `{ "result": "ok" }` or void.

**ACL:** Requires `ui.uiSchemas` snippet permission. **Audit logged.**

---

### 2.8 Batch Patch

Updates multiple schema nodes in a single transaction.

```bash
curl -X POST 'https://{nocobase-url}/api/uiSchemas:batchPatch' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '[
    {
      "x-uid": "node1",
      "title": "Updated Node 1"
    },
    {
      "x-uid": "node2",
      "x-component-props": { "visible": false }
    }
  ]'
```

| Parameter | Type  | Required | Description                                  |
|-----------|-------|----------|----------------------------------------------|
| `values`  | array | Yes      | Array of partial schema objects with `x-uid`  |

**Response:** `{ "result": "ok" }`

**ACL:** Requires `ui.uiSchemas` snippet permission.

---

### 2.9 Remove Schema

Removes a schema node and all its descendants.

```bash
curl -X POST 'https://{nocobase-url}/api/uiSchemas:remove/<x-uid>' \
  -H 'Authorization: Bearer <token>'
```

| Parameter        | Type   | Required | Description                      |
|------------------|--------|----------|----------------------------------|
| `<x-uid>` (URL) | string | Yes      | The `x-uid` of the node to remove |

**Response:** `{ "result": "ok" }`

**ACL:** Requires `ui.uiSchemas` snippet permission. **Audit logged.**

---

### 2.10 Insert Adjacent

Inserts a schema node at a position relative to an existing target node. This is the most commonly used insertion method in the visual constructor for drag-and-drop and "add block" operations.

```bash
curl -X POST 'https://{nocobase-url}/api/uiSchemas:insertAdjacent/<target-x-uid>?position=afterEnd' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "schema": {
      "type": "void",
      "x-component": "CardItem",
      "x-decorator": "BlockItem",
      "properties": {
        "form1": {
          "type": "void",
          "x-component": "FormV2"
        }
      }
    },
    "wrap": null
  }'
```

**Simplified form (schema as body directly):**

```bash
curl -X POST 'https://{nocobase-url}/api/uiSchemas:insertAdjacent/<target-x-uid>?position=beforeEnd' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "void",
    "x-component": "Grid.Row",
    "properties": {
      "col1": {
        "type": "void",
        "x-component": "Grid.Col"
      }
    }
  }'
```

| Parameter                    | Type    | Required | Description                                                                 |
|------------------------------|---------|----------|-----------------------------------------------------------------------------|
| `<target-x-uid>` (URL)      | string  | Yes      | The `x-uid` of the reference node (resourceIndex)                           |
| `position`                   | string  | Yes      | One of: `beforeBegin`, `afterBegin`, `beforeEnd`, `afterEnd`                |
| `values.schema`              | object  | Yes      | The schema to insert (or pass schema directly as body)                      |
| `values.wrap`                | object  | No       | Optional wrapper schema; the new schema is inserted inside the wrapper      |
| `removeParentsIfNoChildren`  | boolean | No       | If `true`, removes parent nodes that become empty after a move              |
| `breakRemoveOn`              | object  | No       | Stop criteria for parent removal (matched against schema properties)        |

**Position values explained:**

| Position        | Description                                      |
|-----------------|--------------------------------------------------|
| `beforeBegin`   | Before the target node (as a sibling before it)  |
| `afterBegin`    | As the first child of the target node             |
| `beforeEnd`     | As the last child of the target node              |
| `afterEnd`      | After the target node (as a sibling after it)     |

**Response:** The inserted schema tree.

**ACL:** Requires `ui.uiSchemas` snippet permission. **Audit logged.**

---

### 2.11 Insert Before Begin

Convenience shorthand for `insertAdjacent` with `position=beforeBegin`.

```bash
curl -X POST 'https://{nocobase-url}/api/uiSchemas:insertBeforeBegin/<target-x-uid>' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "schema": {
      "type": "void",
      "x-component": "Divider"
    }
  }'
```

---

### 2.12 Insert After Begin

Convenience shorthand for `insertAdjacent` with `position=afterBegin`.

```bash
curl -X POST 'https://{nocobase-url}/api/uiSchemas:insertAfterBegin/<target-x-uid>' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "schema": {
      "type": "void",
      "x-component": "FormItem",
      "x-decorator": "FormItem",
      "x-collection-field": "users.name"
    }
  }'
```

---

### 2.13 Insert Before End

Convenience shorthand for `insertAdjacent` with `position=beforeEnd`. Most commonly used when appending new blocks.

```bash
curl -X POST 'https://{nocobase-url}/api/uiSchemas:insertBeforeEnd/<target-x-uid>' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "schema": {
      "type": "void",
      "x-component": "Grid.Row",
      "properties": {
        "col1": {
          "type": "void",
          "x-component": "Grid.Col",
          "x-component-props": { "width": 50 }
        }
      }
    }
  }'
```

---

### 2.14 Insert After End

Convenience shorthand for `insertAdjacent` with `position=afterEnd`.

```bash
curl -X POST 'https://{nocobase-url}/api/uiSchemas:insertAfterEnd/<target-x-uid>' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "void",
    "x-component": "Action",
    "x-action": "create",
    "title": "Add New",
    "x-component-props": {
      "type": "primary"
    }
  }'
```

---

### 2.15 Initialize Action Context

Sets the `x-action-context` on a schema node, but only if it is not already set. Used to lazily initialize action popup contexts.

```bash
curl -X POST 'https://{nocobase-url}/api/uiSchemas:initializeActionContext' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "x-uid": "action-btn-uid",
    "x-action-context": {
      "dataSource": "main",
      "collection": "users"
    }
  }'
```

| Parameter           | Type   | Required | Description                                          |
|---------------------|--------|----------|------------------------------------------------------|
| `values.x-uid`     | string | Yes      | The `x-uid` of the action node                       |
| `values.x-action-context` | object | Yes | The action context to initialize (only set if empty) |

**Response:** `{ "result": "ok" }` or void.

**ACL:** `loggedIn`

---

### 2.16 Clear Ancestor

Detaches a schema subtree from its parent in the tree path hierarchy (breaks the closure table links to ancestors). Used when converting a block into a template.

```bash
curl -X POST 'https://{nocobase-url}/api/uiSchemas:clearAncestor/<x-uid>' \
  -H 'Authorization: Bearer <token>'
```

| Parameter        | Type   | Required | Description                                |
|------------------|--------|----------|--------------------------------------------|
| `<x-uid>` (URL) | string | Yes      | The `x-uid` of the node to detach          |

**Response:** `{ "result": "ok" }`

**ACL:** Requires `ui.uiSchemas` snippet permission.

---

### 2.17 Save As Template

Saves an existing schema as a reusable template. Creates a record in `uiSchemaTemplates` and detaches the schema from its parent hierarchy.

```bash
curl -X POST 'https://{nocobase-url}/api/uiSchemas:saveAsTemplate?filterByTk=<x-uid>' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "My Table Template",
    "componentName": "Table",
    "collectionName": "users",
    "resourceName": "users",
    "dataSourceKey": "main"
  }'
```

| Parameter            | Type   | Required | Description                              |
|----------------------|--------|----------|------------------------------------------|
| `filterByTk`        | string | Yes      | The `x-uid` of the schema to save        |
| `values.name`        | string | Yes      | Template display name                    |
| `values.componentName` | string | No    | Component type identifier                |
| `values.collectionName` | string | No   | Associated collection name               |
| `values.resourceName`| string | No      | Associated resource name                 |
| `values.associationName` | string | No  | Association field name                   |
| `values.dataSourceKey` | string | No    | Data source identifier                   |

**Response:** `{ "result": "ok" }`

**ACL:** Requires `ui.uiSchemas` snippet permission.

---

## 3. UI Schema Templates (Legacy)

Legacy block template system. Templates reference schema nodes by `uid`.

**Resource name:** `uiSchemaTemplates`

### 3.1 List Templates

```bash
curl -X GET 'https://{nocobase-url}/api/uiSchemaTemplates:list' \
  -H 'Authorization: Bearer <token>'
```

**ACL:** `loggedIn`

### 3.2 Get Template

```bash
curl -X GET 'https://{nocobase-url}/api/uiSchemaTemplates:get?filterByTk=<template-key>' \
  -H 'Authorization: Bearer <token>'
```

**ACL:** `loggedIn`

### Template Collection Fields

| Field            | Type   | Description                     |
|------------------|--------|---------------------------------|
| `key`            | uid    | Primary key (auto-generated)    |
| `name`           | string | Template display name           |
| `componentName`  | string | Component type                  |
| `associationName`| string | Association name                |
| `resourceName`   | string | Resource name                   |
| `collectionName` | string | Collection name                 |
| `dataSourceKey`  | string | Data source key                 |
| `uid`            | string | Foreign key to `uiSchemas.x-uid`|

---

## 4. Flow Models (v2.x Block Engine)

The new block engine in NocoBase v2.x. Flow models replace the legacy `uiSchemas` for block-level UI storage. They use the same tree structure (Closure Table) but store data in the `flowModels` collection with `uid` as primary key and `options` as the magic JSON attribute.

**Resource name:** `flowModels`

### Flow Model Collection Fields

| Field     | Type   | Description                                    |
|-----------|--------|------------------------------------------------|
| `uid`     | uid    | Primary key (auto-generated if not provided)   |
| `name`    | string | Node name (auto-generated uid if not provided) |
| `options` | json   | Model options (magic attribute — merged into root) |

### Flow Model Options Structure

The `options` JSON typically contains:

| Property        | Type   | Description                                          |
|-----------------|--------|------------------------------------------------------|
| `use`           | string | Model class name (e.g. `TableBlockModel`, `FormBlockModel`, `RouteModel`, `ReferenceBlockModel`) |
| `stepParams`    | object | Step parameters for the model                        |
| `title`         | string | Display title                                        |
| `description`   | string | Description                                          |
| `x-component-props` | object | Component props                                 |
| `x-decorator-props` | object | Decorator props                                 |

---

### 4.1 Find One Flow Model

Retrieves a single flow model by `uid` or by `parentId`.

**By uid:**

```bash
curl -X GET 'https://{nocobase-url}/api/flowModels:findOne?uid=<model-uid>' \
  -H 'Authorization: Bearer <token>'
```

**By parentId (find child):**

```bash
curl -X GET 'https://{nocobase-url}/api/flowModels:findOne?parentId=<parent-uid>&subKey=properties' \
  -H 'Authorization: Bearer <token>'
```

| Parameter          | Type    | Required | Description                                              |
|--------------------|---------|----------|----------------------------------------------------------|
| `uid`              | string  | No       | Flow model uid (use this OR `parentId`)                  |
| `parentId`         | string  | No       | Parent model uid (finds child node)                      |
| `subKey`           | string  | No       | Child key type filter (e.g. `properties`, `items`)       |
| `includeAsyncNode` | boolean | No       | Include async child nodes (default: `false`)             |

**Response:** Flow model tree object.

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

---

### 4.2 Save Flow Model

Creates or updates a flow model (upsert). If the model with the given `uid` exists, updates it; otherwise creates it. Handles nested children.

```bash
curl -X POST 'https://{nocobase-url}/api/flowModels:save' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
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

**With parent attachment:**

```bash
curl -X POST 'https://{nocobase-url}/api/flowModels:save' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
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

| Parameter               | Type   | Required | Description                                    |
|-------------------------|--------|----------|------------------------------------------------|
| `values.uid`            | string | No       | Model uid (auto-generated if omitted)          |
| `values.name`           | string | No       | Model name                                     |
| `values.use`            | string | No       | Model class name                               |
| `values.stepParams`     | object | No       | Step parameters                                |
| `values.title`          | string | No       | Display title                                  |
| `values.parentId`       | string | No       | Parent model uid (for attaching as child)      |
| `values.subKey`         | string | No       | Child key under parent (e.g. `properties`)     |
| `values.properties`     | object | No       | Nested child models                            |
| `values.*`              | any    | No       | Any other options (stored in `options` JSON)    |

**Response:** The uid of the saved model.

```json
{
  "data": "model-abc123"
}
```

**ACL:** Requires `ui.flowModels` snippet permission. **Audit logged.**

---

### 4.3 Duplicate Flow Model

Creates a deep copy of a flow model and all its descendants with new uids.

```bash
curl -X POST 'https://{nocobase-url}/api/flowModels:duplicate?uid=<model-uid>' \
  -H 'Authorization: Bearer <token>'
```

| Parameter | Type   | Required | Description             |
|-----------|--------|----------|-------------------------|
| `uid`     | string | Yes      | uid of the model to copy |

**Response:** The duplicated model tree.

**ACL:** Requires `ui.flowModels` snippet permission. **Audit logged.**

---

### 4.4 Attach Flow Model

Attaches an existing flow model as a child of another model.

```bash
curl -X POST 'https://{nocobase-url}/api/flowModels:attach' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "uid": "child-model-uid",
    "parentId": "parent-model-uid",
    "subKey": "properties",
    "subType": "object",
    "position": "last"
  }'
```

| Parameter  | Type   | Required | Description                                                      |
|------------|--------|----------|------------------------------------------------------------------|
| `uid`      | string | Yes      | uid of the model to attach                                       |
| `parentId` | string | Yes      | uid of the target parent model                                   |
| `subKey`   | string | Yes      | Key under which to attach (e.g. `properties`, `items`)           |
| `subType`  | string | Yes      | `"object"` (keyed by name) or `"array"` (ordered list)           |
| `position` | string | No       | `"first"`, `"last"`, or a target position object                 |

**Response:** The attached model tree.

**ACL:** Requires `ui.flowModels` snippet permission.

---

### 4.5 Move Flow Model

Repositions a flow model relative to another model (drag-and-drop).

```bash
curl -X POST 'https://{nocobase-url}/api/flowModels:move' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "sourceId": "model-to-move",
    "targetId": "reference-model",
    "position": "after"
  }'
```

| Parameter  | Type   | Required | Description                                    |
|------------|--------|----------|------------------------------------------------|
| `sourceId` | string | Yes      | uid of the model to move                       |
| `targetId` | string | Yes      | uid of the reference model                     |
| `position` | string | Yes      | `"before"` (maps to `beforeBegin`) or `"after"` (maps to `afterEnd`) |

**Response:** `"ok"`

**ACL:** Requires `ui.flowModels` snippet permission.

---

### 4.6 Destroy Flow Model

Removes a flow model and all its descendants.

```bash
curl -X POST 'https://{nocobase-url}/api/flowModels:destroy?filterByTk=<model-uid>' \
  -H 'Authorization: Bearer <token>'
```

| Parameter    | Type   | Required | Description              |
|--------------|--------|----------|--------------------------|
| `filterByTk` | string | Yes     | uid of the model to remove |

**Response:** `"ok"`

**ACL:** Requires `ui.flowModels` snippet permission. **Audit logged.**

---

### 4.7 Flow Models — Inherited Schema Actions

The `flowModels` resource also inherits all the same tree-manipulation actions as `uiSchemas`. These work identically but operate on the `flowModels` collection. The `values` payload uses `options` instead of `schema`.

| Action               | URL                                                           |
|----------------------|---------------------------------------------------------------|
| getJsonSchema        | `GET /api/flowModels:getJsonSchema/<uid>`                     |
| getProperties        | `GET /api/flowModels:getProperties/<uid>`                     |
| getParentJsonSchema  | `GET /api/flowModels:getParentJsonSchema/<uid>`               |
| getParentProperty    | `GET /api/flowModels:getParentProperty/<uid>`                 |
| insert               | `POST /api/flowModels:insert`                                 |
| insertNewSchema      | `POST /api/flowModels:insertNewSchema`                        |
| patch                | `POST /api/flowModels:patch`                                  |
| batchPatch           | `POST /api/flowModels:batchPatch`                             |
| remove               | `POST /api/flowModels:remove/<uid>`                           |
| clearAncestor        | `POST /api/flowModels:clearAncestor/<uid>`                    |
| insertAdjacent       | `POST /api/flowModels:insertAdjacent/<uid>?position=beforeEnd`|
| insertBeforeBegin    | `POST /api/flowModels:insertBeforeBegin/<uid>`                |
| insertAfterBegin     | `POST /api/flowModels:insertAfterBegin/<uid>`                 |
| insertBeforeEnd      | `POST /api/flowModels:insertBeforeEnd/<uid>`                  |
| insertAfterEnd       | `POST /api/flowModels:insertAfterEnd/<uid>`                   |
| initializeActionContext | `POST /api/flowModels:initializeActionContext`             |

See [Section 2: UI Schema Management](#2-ui-schema-management) for full parameter documentation. The only difference is that `insertAdjacent` values use `options` key instead of `schema`:

```bash
curl -X POST 'https://{nocobase-url}/api/flowModels:insertAdjacent/<target-uid>?position=beforeEnd' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
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

---

### 4.8 Flow SQL

Endpoints for executing and managing SQL queries within flow models.

**Resource name:** `flowSql`

#### Save Flow SQL

```bash
curl -X POST 'https://{nocobase-url}/api/flowSql:save' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "uid": "sql-block-uid",
    "sql": "SELECT * FROM {{users}} WHERE status = :status",
    "dataSourceKey": "main"
  }'
```

| Parameter             | Type   | Required | Description                |
|-----------------------|--------|----------|----------------------------|
| `values.uid`          | string | Yes      | Flow SQL identifier        |
| `values.sql`          | string | Yes      | SQL query (with Liquid templates and bind params) |
| `values.dataSourceKey`| string | No       | Data source key            |

**ACL:** Requires `ui.flowSql` snippet permission. **Audit logged.**

#### Run Flow SQL by ID

```bash
curl -X POST 'https://{nocobase-url}/api/flowSql:runById' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "uid": "sql-block-uid",
    "type": "SELECT",
    "filter": {},
    "bind": { "status": "active" },
    "liquidContext": { "users": "public.users" },
    "dataSourceKey": "main"
  }'
```

| Parameter               | Type   | Required | Description                          |
|-------------------------|--------|----------|--------------------------------------|
| `values.uid`            | string | Yes      | Flow SQL identifier                  |
| `values.type`           | string | No       | SQL type (`SELECT`, `INSERT`, etc.)  |
| `values.filter`         | object | No       | Additional filters                   |
| `values.bind`           | object | No       | Bind parameters for the query        |
| `values.liquidContext`   | object | No      | Liquid template context variables    |
| `values.dataSourceKey`  | string | No       | Data source key override             |

**ACL:** `loggedIn`

#### Get Flow SQL Bind Parameters

```bash
curl -X GET 'https://{nocobase-url}/api/flowSql:getBind?uid=<sql-uid>' \
  -H 'Authorization: Bearer <token>'
```

**Response:**

```json
{
  "data": {
    "bind": { "status": null },
    "liquidContext": { "users": "public.users" }
  }
}
```

**ACL:** `loggedIn`

---

### 4.9 Variables — Resolve Template Variables

Resolves context variables in JSON templates (used by flow models for dynamic data).

**Resource name:** `variables`

```bash
curl -X POST 'https://{nocobase-url}/api/variables:resolve' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
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

**Batch resolve:**

```bash
curl -X POST 'https://{nocobase-url}/api/variables:resolve' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
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

| Parameter                       | Type   | Required | Description                                    |
|---------------------------------|--------|----------|------------------------------------------------|
| `values.template`               | any    | Yes*     | JSON template with variable placeholders       |
| `values.contextParams`          | object | No       | Context parameters for variable resolution     |
| `values.batch`                  | array  | Yes*     | Array of `{ id?, template, contextParams }` for batch resolution |

*Either `template` or `batch` is required.

**Batch response:**

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

---

## 5. Flow Model Templates

New template system for reusable blocks (v2.x+). Tracks usage and supports reference blocks.

**Resource name:** `flowModelTemplates`

### 4.1 List Flow Model Templates

```bash
curl -X GET 'https://{nocobase-url}/api/flowModelTemplates:list?page=1&pageSize=20' \
  -H 'Authorization: Bearer <token>'
```

**With search:**

```bash
curl -X GET 'https://{nocobase-url}/api/flowModelTemplates:list?search=my+template' \
  -H 'Authorization: Bearer <token>'
```

| Parameter  | Type   | Required | Description                              |
|------------|--------|----------|------------------------------------------|
| `page`     | number | No       | Page number (default: 1)                 |
| `pageSize` | number | No       | Items per page (default: 20)             |
| `search`   | string | No       | Search by name or description            |
| `filter`   | object | No       | JSON filter object                       |

**Response:**

```json
{
  "data": {
    "rows": [
      {
        "uid": "tpl_abc123",
        "name": "User Table Template",
        "description": "Standard user listing table",
        "targetUid": "block_xyz",
        "useModel": "TableBlockModel",
        "type": "block",
        "dataSourceKey": "main",
        "collectionName": "users",
        "usageCount": 3
      }
    ],
    "count": 1,
    "page": 1,
    "pageSize": 20,
    "totalPage": 1
  }
}
```

**ACL:** `loggedIn`

---

### 4.2 Get Flow Model Template

```bash
curl -X GET 'https://{nocobase-url}/api/flowModelTemplates:get?filterByTk=<uid>' \
  -H 'Authorization: Bearer <token>'
```

| Parameter    | Type   | Required | Description      |
|--------------|--------|----------|------------------|
| `filterByTk` | string | Yes     | Template uid     |

**Response:** Template object with `usageCount`.

**ACL:** `loggedIn`

---

### 4.3 Create Flow Model Template

```bash
curl -X POST 'https://{nocobase-url}/api/flowModelTemplates:create' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "My Block Template",
    "description": "Reusable form block for user creation",
    "targetUid": "block_uid_to_template",
    "useModel": "FormBlockModel",
    "type": "block",
    "dataSourceKey": "main",
    "collectionName": "users",
    "detachParent": true
  }'
```

| Parameter          | Type    | Required | Description                                              |
|--------------------|---------|----------|----------------------------------------------------------|
| `values.uid`       | string  | No       | Custom uid (auto-generated if omitted)                   |
| `values.name`      | string  | Yes      | Template name                                            |
| `values.description` | string | No     | Template description                                     |
| `values.targetUid` | string  | No       | Target flow model uid to template from                   |
| `values.useModel`  | string  | No       | Model type (e.g. `TableBlockModel`, `FormBlockModel`)    |
| `values.type`      | string  | No       | Template type                                            |
| `values.dataSourceKey` | string | No    | Data source key                                          |
| `values.collectionName` | string | No   | Collection name                                          |
| `values.associationName` | string | No  | Association name                                         |
| `values.detachParent` | boolean | No    | If `true`, detaches the target from its parent hierarchy |
| `values.filterByTk` | string | No      | Filter key                                               |
| `values.sourceId`  | string  | No       | Source identifier                                        |

**Response:** Created template with `usageCount: 0`.

**ACL:** `loggedIn`. **Audit logged.**

---

### 4.4 Update Flow Model Template

```bash
curl -X POST 'https://{nocobase-url}/api/flowModelTemplates:update?filterByTk=<uid>' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Updated Template Name",
    "description": "Updated description"
  }'
```

| Parameter            | Type   | Required | Description                  |
|----------------------|--------|----------|------------------------------|
| `filterByTk`        | string | Yes      | Template uid                 |
| `values.name`        | string | No       | Updated name                 |
| `values.description` | string | No       | Updated description          |

**Side effect:** Syncs template metadata to all reference blocks using this template.

**Response:** Updated template with `usageCount`.

**ACL:** `loggedIn`. **Audit logged.**

---

### 4.5 Destroy Flow Model Template

```bash
curl -X POST 'https://{nocobase-url}/api/flowModelTemplates:destroy?filterByTk=<uid>' \
  -H 'Authorization: Bearer <token>'
```

| Parameter    | Type   | Required | Description    |
|--------------|--------|----------|----------------|
| `filterByTk` | string | Yes     | Template uid   |

**Validation:** Fails with HTTP 400 and code `TEMPLATE_IN_USE` if `usageCount > 0`.

**Response:** `{ "result": "ok" }` on success.

**Error response (if in use):**

```json
{
  "errors": [{
    "code": "TEMPLATE_IN_USE",
    "message": "Template is in use and cannot be deleted",
    "data": { "usageCount": 3 }
  }]
}
```

**ACL:** `loggedIn`. **Audit logged.**

---

## 6. Desktop Routes (Pages & Menus)

Desktop routes define the page/menu structure of the application. Stored as an adjacency-list tree.

**Resource name:** `desktopRoutes`

### Desktop Route Fields

| Field           | Type      | Description                                      |
|-----------------|-----------|--------------------------------------------------|
| `id`            | snowflakeId | Primary key (auto-generated)                    |
| `parentId`      | bigInt    | Parent route ID (null for root)                  |
| `title`         | string    | Menu/page display title                          |
| `tooltip`       | string    | Tooltip text                                     |
| `icon`          | string    | Icon identifier                                  |
| `schemaUid`     | string    | Associated UI schema `x-uid` for the page body   |
| `menuSchemaUid` | string    | Associated UI schema `x-uid` for the menu item   |
| `tabSchemaName` | string    | Tab schema name (for tabbed pages)               |
| `type`          | string    | Route type (e.g. `page`, `link`, `group`, `tabs`) |
| `options`       | json      | Additional route options                         |
| `sort`          | sort      | Sort order (scoped by `parentId`)                |
| `hideInMenu`    | boolean   | Whether to hide in menu navigation               |
| `enableTabs`    | boolean   | Whether to enable tab sub-pages                  |
| `enableHeader`  | boolean   | Whether to show page header                      |
| `displayTitle`  | boolean   | Whether to display title in header               |
| `hidden`        | boolean   | Whether completely hidden (used for tab children) |

---

### 6.1 List Accessible Desktop Routes

Lists all desktop routes accessible to the current user based on their roles.

```bash
curl -X GET 'https://{nocobase-url}/api/desktopRoutes:listAccessible' \
  -H 'Authorization: Bearer <token>' \
  -H 'X-Role: admin'
```

**Response:** Array of route objects in tree structure.

```json
{
  "data": [
    {
      "id": 1,
      "title": "Dashboard",
      "icon": "DashboardOutlined",
      "type": "page",
      "schemaUid": "page-uid-123",
      "sort": 1,
      "children": [
        {
          "id": 2,
          "title": "Tab 1",
          "type": "tabs",
          "parentId": 1,
          "schemaUid": "tab-uid-456"
        }
      ]
    }
  ]
}
```

**ACL:** `loggedIn`

---

### 6.2 Get Accessible Desktop Route

```bash
curl -X GET 'https://{nocobase-url}/api/desktopRoutes:getAccessible?filterByTk=<route-id>' \
  -H 'Authorization: Bearer <token>' \
  -H 'X-Role: admin'
```

| Parameter    | Type   | Required | Description       |
|--------------|--------|----------|-------------------|
| `filterByTk` | number | Yes     | Route ID          |

**Response:** Single route object with children.

**ACL:** `loggedIn`

---

### 6.3 Create Desktop Route

```bash
curl -X POST 'https://{nocobase-url}/api/desktopRoutes:create' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "New Page",
    "icon": "FileOutlined",
    "type": "page",
    "schemaUid": "new-schema-uid",
    "parentId": null,
    "enableHeader": true,
    "displayTitle": true
  }'
```

**Side effect:** Roles with `allowNewMenu=true` (default: `admin`, `member`) automatically get access.

**ACL:** Requires `ui.desktopRoutes` snippet permission.

---

### 6.4 Update Desktop Route

```bash
curl -X POST 'https://{nocobase-url}/api/desktopRoutes:update?filterByTk=<route-id>' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Renamed Page",
    "icon": "EditOutlined",
    "enableTabs": true
  }'
```

**Side effect:** If `enableTabs` changes, all child routes' `hidden` field is updated.

**ACL:** Requires `ui.desktopRoutes` snippet permission.

---

### 6.5 Move Desktop Route

Repositions a route within the tree (for drag-and-drop reordering).

```bash
curl -X POST 'https://{nocobase-url}/api/desktopRoutes:move' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "sourceId": 5,
    "targetId": 3,
    "sortField": "sort",
    "targetScope": { "parentId": 1 },
    "method": "insertAfter"
  }'
```

| Parameter      | Type   | Required | Description                                       |
|----------------|--------|----------|---------------------------------------------------|
| `sourceId`     | number | Yes      | ID of the route being moved                       |
| `targetId`     | number | Yes      | ID of the reference route                         |
| `sortField`    | string | No       | Field to use for sorting (default: `sort`)        |
| `targetScope`  | object | No       | Scope for sort (e.g. `{ "parentId": 1 }`)        |
| `method`       | string | No       | `insertAfter` or `insertBefore` or `prepend`      |

**ACL:** Requires `ui.desktopRoutes` snippet permission.

---

### 6.6 Destroy Desktop Route

```bash
curl -X POST 'https://{nocobase-url}/api/desktopRoutes:destroy?filterByTk=<route-id>' \
  -H 'Authorization: Bearer <token>'
```

**Side effect:** Also destroys the associated `flowModels` record (if exists) and cascades to child routes.

**ACL:** Requires `ui.desktopRoutes` snippet permission.

---

### 6.7 Set Role Desktop Routes

Configures which desktop routes are accessible for a specific role.

```bash
curl -X POST 'https://{nocobase-url}/api/roles/<role-name>/desktopRoutes:set' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '[1, 3, 5, 7]'
```

| Parameter      | Type    | Required | Description                                 |
|----------------|---------|----------|---------------------------------------------|
| `<role-name>`  | string  | Yes      | Role name (URL path segment)                |
| `values`       | array   | Yes      | Array of route IDs to grant access to       |

**Note:** Automatically includes child tab routes for any parent route in the list.

**ACL:** Requires `pm.desktopRoutes` snippet permission.

---

## 7. Mobile Routes

Mobile navigation routes. Nearly identical structure to desktop routes but for the mobile interface.

**Resource name:** `mobileRoutes`

### Mobile Route Fields

| Field            | Type      | Description                           |
|------------------|-----------|---------------------------------------|
| `id`             | snowflakeId | Primary key                          |
| `parentId`       | bigInt    | Parent route ID                       |
| `title`          | string    | Display title                         |
| `icon`           | string    | Icon identifier                       |
| `schemaUid`      | string    | Associated UI schema `x-uid`          |
| `type`           | string    | Route type                            |
| `options`        | json      | Additional options                    |
| `sort`           | sort      | Sort order (scoped by `parentId`)     |
| `hideInMenu`     | boolean   | Hide from mobile menu                 |
| `enableTabs`     | boolean   | Enable tab sub-pages                  |
| `hidden`         | boolean   | Completely hidden                     |

---

### 7.1 List Accessible Mobile Routes

```bash
curl -X GET 'https://{nocobase-url}/api/mobileRoutes:listAccessible' \
  -H 'Authorization: Bearer <token>'
```

**Response:** Array of mobile route objects in tree structure.

**ACL:** `loggedIn`

---

### 7.2 Create Mobile Route

```bash
curl -X POST 'https://{nocobase-url}/api/mobileRoutes:create' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Mobile Page",
    "icon": "HomeOutlined",
    "type": "page",
    "schemaUid": "mobile-schema-uid"
  }'
```

**ACL:** Requires `ui.mobile` snippet permission.

---

### 7.3 Update Mobile Route

```bash
curl -X POST 'https://{nocobase-url}/api/mobileRoutes:update?filterByTk=<route-id>' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Updated Mobile Page",
    "enableTabs": true
  }'
```

**ACL:** Requires `ui.mobile` snippet permission.

---

### 7.4 Move Mobile Route

```bash
curl -X POST 'https://{nocobase-url}/api/mobileRoutes:move' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "sourceId": 10,
    "targetId": 8,
    "method": "insertAfter"
  }'
```

**ACL:** Requires `ui.mobile` snippet permission.

---

### 7.5 Destroy Mobile Route

```bash
curl -X POST 'https://{nocobase-url}/api/mobileRoutes:destroy?filterByTk=<route-id>' \
  -H 'Authorization: Bearer <token>'
```

**ACL:** Requires `ui.mobile` snippet permission.

---

## 8. Collection & Field Management

APIs for managing data sources, collections (tables), and fields. The visual constructor uses these to configure which data each UI block displays.

### Data Sources

**Resource name:** `dataSources`

#### 8.1 List Enabled Data Sources

```bash
curl -X GET 'https://{nocobase-url}/api/dataSources:listEnabled' \
  -H 'Authorization: Bearer <token>'
```

**Response:** Array of enabled data source objects (excluding the `main` data source).

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

---

#### 8.2 Test Data Source Connection

```bash
curl -X POST 'https://{nocobase-url}/api/dataSources:testConnection' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
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

| Parameter       | Type   | Required | Description                    |
|-----------------|--------|----------|--------------------------------|
| `values.type`   | string | Yes      | Data source type (e.g. `postgres`, `mysql`) |
| `values.options` | object | Yes     | Connection options             |

**Response:** `{ "success": true }`

**ACL:** Requires `pm.data-source-manager` snippet permission.

---

#### 8.3 Refresh Data Source

```bash
curl -X POST 'https://{nocobase-url}/api/dataSources:refresh?filterByTk=<data-source-key>' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "clientStatus": "loaded"
  }'
```

| Parameter      | Type   | Required | Description                                           |
|----------------|--------|----------|-------------------------------------------------------|
| `filterByTk`   | string | Yes     | Data source key                                       |
| `clientStatus`  | string | No      | Client-perceived status (refresh only if refreshable) |

**Response:** `{ "status": "reloading" }`

---

#### 8.4 Read Tables

Lists available database tables from a data source.

```bash
curl -X POST 'https://{nocobase-url}/api/dataSources:readTables' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "dataSourceKey": "external-pg"
  }'
```

| Parameter            | Type   | Required | Description                                |
|----------------------|--------|----------|--------------------------------------------|
| `values.dataSourceKey` | string | Yes   | Data source key                            |
| `values.dbOptions`   | object | No      | Alternative DB options (creates temp connection) |

**Response:** Array of table name strings.

---

#### 8.5 Load Tables

Imports selected tables as collections.

```bash
curl -X POST 'https://{nocobase-url}/api/dataSources:loadTables' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "dataSourceKey": "external-pg",
    "tables": ["users", "orders", "products"]
  }'
```

| Parameter            | Type     | Required | Description                |
|----------------------|----------|----------|----------------------------|
| `values.dataSourceKey` | string | Yes      | Data source key            |
| `values.tables`      | string[] | Yes      | Table names to import      |

---

### Collections

**Resource name:** `dataSources.collections` (nested under data source)

#### 8.6 List Collections

```bash
curl -X GET 'https://{nocobase-url}/api/dataSources/<data-source-key>/collections:list?page=1&pageSize=50' \
  -H 'Authorization: Bearer <token>'
```

**Non-paginated:**

```bash
curl -X GET 'https://{nocobase-url}/api/dataSources/<data-source-key>/collections:list?paginate=false' \
  -H 'Authorization: Bearer <token>'
```

| Parameter            | Type    | Required | Description                             |
|----------------------|---------|----------|-----------------------------------------|
| `<data-source-key>`  | string | Yes      | Data source key (URL path segment)       |
| `page`               | number | No       | Page number (default: 1)                |
| `pageSize`           | number | No       | Items per page (default: 20)            |
| `paginate`           | boolean| No       | Set to `false` for non-paginated results |
| `filter`             | object | No       | Filter object (JSON stringified)        |

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
          {
            "name": "id",
            "type": "bigInt",
            "interface": "id",
            "primaryKey": true
          },
          {
            "name": "email",
            "type": "string",
            "interface": "email"
          }
        ]
      }
    ],
    "meta": {
      "count": 15,
      "page": 1,
      "pageSize": 50,
      "totalPage": 1
    }
  }
}
```

**Non-paginated response:** Direct array of collection objects.

---

#### 8.7 Update Collection

```bash
curl -X POST 'https://{nocobase-url}/api/dataSources/<data-source-key>/collections:update?filterByTk=<collection-name>' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Updated Collection Title",
    "sortable": true
  }'
```

| Parameter              | Type   | Required | Description                     |
|------------------------|--------|----------|---------------------------------|
| `<data-source-key>`    | string | Yes      | Data source key (URL path)      |
| `filterByTk`           | string | Yes      | Collection name                 |
| `values`               | object | Yes      | Collection options to update    |

**Note:** Creates the collection record if it doesn't exist.

---

### Fields

**Resource name:** `dataSourcesCollections.fields` (nested under data source + collection)

The `associatedIndex` parameter uses the format `<dataSourceKey>.<collectionName>`.

#### 8.8 List Fields

```bash
curl -X GET 'https://{nocobase-url}/api/dataSourcesCollections/<dataSourceKey>.<collectionName>/fields:list' \
  -H 'Authorization: Bearer <token>'
```

| Parameter                   | Type   | Required | Description                              |
|-----------------------------|--------|----------|------------------------------------------|
| `<dataSourceKey>.<collectionName>` | string | Yes | Combined key (URL path segment) |

**Response:** Array of field option objects sorted by name.

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

---

#### 8.9 Get Field

```bash
curl -X GET 'https://{nocobase-url}/api/dataSourcesCollections/<dataSourceKey>.<collectionName>/fields:get?filterByTk=<field-name>' \
  -H 'Authorization: Bearer <token>'
```

---

#### 8.10 Create Field

```bash
curl -X POST 'https://{nocobase-url}/api/dataSourcesCollections/<dataSourceKey>.<collectionName>/fields:create' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
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

| Parameter           | Type   | Required | Description                          |
|---------------------|--------|----------|--------------------------------------|
| `values.name`       | string | Yes      | Field name (must be unique in collection) |
| `values.type`       | string | Yes      | Field type (`string`, `integer`, `boolean`, `date`, `json`, `belongsTo`, `hasMany`, etc.) |
| `values.interface`  | string | No       | UI interface type (`input`, `email`, `phone`, `select`, `checkbox`, `datePicker`, etc.) |
| `values.description`| string | No       | Field description                    |
| `values.uiSchema`   | object | No       | UI rendering schema                  |
| `values.defaultValue`| any   | No       | Default value                        |

**Validation:** Fails if field name already exists in the collection.

---

#### 8.11 Update Field

```bash
curl -X POST 'https://{nocobase-url}/api/dataSourcesCollections/<dataSourceKey>.<collectionName>/fields:update?filterByTk=<field-name>' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "interface": "textarea",
    "uiSchema": {
      "type": "string",
      "title": "Description",
      "x-component": "Input.TextArea"
    }
  }'
```

---

#### 8.12 Destroy Field

```bash
curl -X POST 'https://{nocobase-url}/api/dataSourcesCollections/<dataSourceKey>.<collectionName>/fields:destroy?filterByTk=<field-name>' \
  -H 'Authorization: Bearer <token>'
```

**Response:** `"ok"`

---

## 9. System Settings

Global application settings used by the UI shell.

**Resource name:** `systemSettings`

### 9.1 Get System Settings

```bash
curl -X GET 'https://{nocobase-url}/api/systemSettings:get' \
  -H 'Authorization: Bearer <token>'
```

**Response:**

```json
{
  "data": {
    "id": 1,
    "title": "My NocoBase App",
    "raw_title": "My NocoBase App",
    "appLang": "en-US",
    "enabledLanguages": ["en-US", "zh-CN"],
    "logo": {
      "title": "nocobase-logo",
      "filename": "logo.png",
      "extname": ".png",
      "mimetype": "image/png",
      "url": "/storage/uploads/logo.png"
    },
    "options": {
      "theme": "default"
    }
  }
}
```

**ACL:** `public` (no authentication required)

---

### 9.2 Update System Settings

```bash
curl -X POST 'https://{nocobase-url}/api/systemSettings:put' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "raw_title": "Updated App Title",
    "enabledLanguages": ["en-US", "zh-CN", "ja-JP"],
    "options": {
      "theme": "compact"
    }
  }'
```

| Parameter                  | Type     | Required | Description                        |
|----------------------------|----------|----------|------------------------------------|
| `values.raw_title`         | string   | No       | Application title                  |
| `values.appLang`           | string   | No       | Default application language       |
| `values.enabledLanguages`  | string[] | No       | Array of enabled locale codes      |
| `values.logo`              | object   | No       | Logo attachment object             |
| `values.options`           | object   | No       | Additional options (theme, etc.)   |

**Note:** Use `raw_title` instead of `title` — the server processes template variables in titles.

**Response:** Updated system settings object.

**ACL:** Requires `pm.system-settings.system-settings` snippet permission.

---

## 10. Data Visualization (Charts)

Query endpoint for chart/dashboard blocks.

**Resource name:** `charts`

### 12.1 Query Chart Data

```bash
curl -X POST 'https://{nocobase-url}/api/charts:query' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "collection": "orders",
    "dataSource": "main",
    "measures": [
      {
        "field": "amount",
        "aggregation": "sum",
        "alias": "totalAmount"
      }
    ],
    "dimensions": [
      {
        "field": "status",
        "alias": "orderStatus"
      }
    ],
    "filter": {
      "createdAt": {
        "$gte": "2024-01-01"
      }
    },
    "orders": [
      { "field": "totalAmount", "order": "desc" }
    ],
    "limit": 100
  }'
```

| Parameter       | Type     | Required | Description                                    |
|-----------------|----------|----------|------------------------------------------------|
| `collection`    | string   | Yes      | Collection name to query                       |
| `dataSource`    | string   | No       | Data source key (default: `main`)              |
| `measures`      | array    | Yes      | Aggregation definitions                        |
| `dimensions`    | array    | No       | Grouping fields                                |
| `filter`        | object   | No       | Filter conditions                              |
| `orders`        | array    | No       | Sort orders                                    |
| `limit`         | number   | No       | Max rows to return                             |

**Measure object:**

| Field          | Type   | Description                                          |
|----------------|--------|------------------------------------------------------|
| `field`        | string | Field name to aggregate                              |
| `aggregation`  | string | Aggregation function: `sum`, `avg`, `min`, `max`, `count` |
| `alias`        | string | Result column alias                                  |

**Dimension object:**

| Field   | Type   | Description              |
|---------|--------|--------------------------|
| `field` | string | Field name to group by   |
| `alias` | string | Result column alias      |
| `format`| string | Date format (for dates)  |

**Response:** Array of aggregated data rows.

```json
{
  "data": [
    { "orderStatus": "pending", "totalAmount": 15000 },
    { "orderStatus": "completed", "totalAmount": 85000 }
  ]
}
```

**ACL:** `loggedIn`. Results are cached for 30 seconds (in-memory cache, max 1000 entries).

---

## 11. Roles & Permissions

### 12.1 Check Current Role

Returns the current user's role, permissions, and allowed actions.

```bash
curl -X GET 'https://{nocobase-url}/api/roles:check' \
  -H 'Authorization: Bearer <token>' \
  -H 'X-Role: admin'
```

**Response:** Role details with action permissions.

```json
{
  "data": {
    "role": "admin",
    "strategy": { "actions": ["create", "view", "update", "destroy"] },
    "actions": {
      "users:list": { "fields": [] },
      "users:create": { "fields": [] },
      "users:update": { "fields": [], "own": false }
    },
    "snippets": ["ui.*", "pm.*"],
    "allowNewMenu": true,
    "allowNewMobileMenu": true
  }
}
```

**ACL:** `loggedIn`

---

### 12.2 List Roles

```bash
curl -X GET 'https://{nocobase-url}/api/roles:list' \
  -H 'Authorization: Bearer <token>'
```

**Response:** Paginated list of role objects.

---

### 12.3 Set Role Data Source Resources

Configures resource-level access for a role within a data source.

```bash
curl -X POST 'https://{nocobase-url}/api/dataSources/<data-source-key>/roles:update?filterByTk=<role-name>' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
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

---

## 12. Application

General application endpoints.

**Resource name:** `app`

### 12.1 Get App Info

Returns application metadata.

```bash
curl -X GET 'https://{nocobase-url}/api/app:getInfo' \
  -H 'Authorization: Bearer <token>'
```

**Response:**

```json
{
  "data": {
    "database": {
      "dialect": "postgres"
    },
    "version": "2.0.33",
    "lang": "en-US",
    "name": "main",
    "theme": "default"
  }
}
```

**ACL:** `public` (no auth required for basic info)

---

### 13.2 Get Language Resources

Returns locale strings for the current language.

```bash
curl -X GET 'https://{nocobase-url}/api/app:getLang?locale=en-US'
```

| Parameter | Type   | Required | Description               |
|-----------|--------|----------|---------------------------|
| `locale`  | string | No       | Override locale code       |

**Response:**

```json
{
  "data": {
    "lang": "en-US",
    "resources": {
      "client": { "Save": "Save", "Cancel": "Cancel" },
      "antd": { ... },
      "cronstrue": { ... },
      "cron": { ... }
    }
  }
}
```

**ACL:** `public`

---

### 12.3 Clear Cache

```bash
curl -X POST 'https://{nocobase-url}/api/app:clearCache' \
  -H 'Authorization: Bearer <token>'
```

**ACL:** Requires `app` snippet permission.

---

### 12.4 Restart Application

```bash
curl -X POST 'https://{nocobase-url}/api/app:restart' \
  -H 'Authorization: Bearer <token>'
```

**ACL:** Requires `app` snippet permission. **Audit logged.**

---

### 12.5 Refresh Application

```bash
curl -X POST 'https://{nocobase-url}/api/app:refresh' \
  -H 'Authorization: Bearer <token>'
```

**ACL:** Requires `app` snippet permission. **Audit logged.**

---

## 13. Generic CRUD Actions

Every collection/resource in NocoBase automatically exposes these standard actions. These work on any resource, including custom collections created through the UI.

### URL Pattern

```
GET  /api/<collection>:<action>
POST /api/<collection>:<action>
```

For associations:

```
GET  /api/<collection>/<recordId>/<association>:<action>
POST /api/<collection>/<recordId>/<association>:<action>
```

---

### 13.1 List

```bash
curl -X GET 'https://{nocobase-url}/api/users:list?page=1&pageSize=20&sort=-createdAt&fields=id,name,email&filter={"status":"active"}' \
  -H 'Authorization: Bearer <token>'
```

| Parameter  | Type    | Required | Description                                        |
|------------|---------|----------|----------------------------------------------------|
| `page`     | number  | No       | Page number (default: 1)                           |
| `pageSize` | number  | No       | Items per page (default: 50)                       |
| `paginate` | boolean | No       | Set to `false` for non-paginated results           |
| `sort`     | string  | No       | Sort field(s), prefix with `-` for descending      |
| `fields`   | string  | No       | Comma-separated field names to include             |
| `appends`  | string  | No       | Comma-separated association names to eager load    |
| `except`   | string  | No       | Comma-separated field names to exclude             |
| `filter`   | string  | No       | JSON filter object (stringified)                   |
| `tree`     | boolean | No       | If `true`, returns tree structure for tree collections |

**Paginated response:**

```json
{
  "data": {
    "count": 150,
    "rows": [ ... ],
    "page": 1,
    "pageSize": 20,
    "totalPage": 8
  }
}
```

**Simple pagination (for large tables, >1000 rows):**

```json
{
  "data": {
    "rows": [ ... ],
    "hasNext": true,
    "page": 1,
    "pageSize": 20
  }
}
```

**Non-paginated response:** Direct array of records.

---

### 13.2 Get

```bash
curl -X GET 'https://{nocobase-url}/api/users:get?filterByTk=1&appends=roles,department' \
  -H 'Authorization: Bearer <token>'
```

| Parameter         | Type   | Required | Description                             |
|-------------------|--------|----------|-----------------------------------------|
| `filterByTk`      | any   | Yes      | Primary key value                       |
| `fields`          | string | No       | Fields to include                       |
| `appends`         | string | No       | Associations to eager load              |
| `except`          | string | No       | Fields to exclude                       |
| `filter`          | string | No       | Additional filter                       |
| `targetCollection`| string | No       | Target collection for polymorphic       |

---

### 13.3 Create

```bash
curl -X POST 'https://{nocobase-url}/api/users:create' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "roles": ["member"]
  }'
```

| Parameter                   | Type     | Required | Description                          |
|-----------------------------|----------|----------|--------------------------------------|
| `values`                    | object   | Yes      | Record data (request body)           |
| `whitelist`                 | string[] | No       | Only these fields can be set         |
| `blacklist`                 | string[] | No       | These fields cannot be set           |
| `updateAssociationValues`   | string[] | No       | Association fields to update inline  |

---

### 13.4 Update

```bash
curl -X POST 'https://{nocobase-url}/api/users:update?filterByTk=1' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Jane Doe",
    "email": "jane@example.com"
  }'
```

| Parameter                   | Type     | Required | Description                          |
|-----------------------------|----------|----------|--------------------------------------|
| `filterByTk`                | any      | No       | Primary key (update single record)   |
| `filter`                    | object   | No       | Filter (update multiple records)     |
| `values`                    | object   | Yes      | Fields to update (request body)      |
| `whitelist`                 | string[] | No       | Only these fields can be updated     |
| `blacklist`                 | string[] | No       | These fields cannot be updated       |
| `updateAssociationValues`   | string[] | No       | Association fields to update inline  |
| `forceUpdate`               | boolean  | No       | Force update even if no changes      |

---

### 13.5 Destroy

```bash
curl -X POST 'https://{nocobase-url}/api/users:destroy?filterByTk=1' \
  -H 'Authorization: Bearer <token>'
```

**Bulk destroy with filter:**

```bash
curl -X POST 'https://{nocobase-url}/api/users:destroy' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "filter": { "status": "inactive" }
  }'
```

| Parameter    | Type   | Required | Description                        |
|--------------|--------|----------|------------------------------------|
| `filterByTk` | any   | No       | Primary key (delete single record) |
| `filter`     | object | No       | Filter (delete matching records)   |

---

### 13.6 First Or Create

Finds the first matching record or creates a new one.

```bash
curl -X POST 'https://{nocobase-url}/api/users:firstOrCreate' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "filterKeys": ["email"],
    "values": {
      "email": "john@example.com",
      "name": "John Doe"
    }
  }'
```

| Parameter    | Type     | Required | Description                                 |
|--------------|----------|----------|---------------------------------------------|
| `values`     | object   | Yes      | Record data                                 |
| `filterKeys` | string[] | Yes     | Fields to match on (for finding existing)   |

---

### 13.7 Update Or Create

Finds a matching record and updates it, or creates a new one.

```bash
curl -X POST 'https://{nocobase-url}/api/users:updateOrCreate' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "filterKeys": ["email"],
    "values": {
      "email": "john@example.com",
      "name": "John Updated"
    }
  }'
```

| Parameter    | Type     | Required | Description                                 |
|--------------|----------|----------|---------------------------------------------|
| `values`     | object   | Yes      | Record data                                 |
| `filterKeys` | string[] | Yes     | Fields to match on                          |

---

### 13.8 Move (Sort)

Repositions a record in a sorted list. Available on collections with a `sort` field.

```bash
curl -X POST 'https://{nocobase-url}/api/users:move' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "sourceId": 5,
    "targetId": 3,
    "sortField": "sort",
    "targetScope": {},
    "method": "insertAfter"
  }'
```

| Parameter     | Type   | Required | Description                                     |
|---------------|--------|----------|-------------------------------------------------|
| `sourceId`    | any    | Yes      | Primary key of record to move                   |
| `targetId`    | any    | Yes      | Primary key of the target reference record      |
| `sortField`   | string | No       | Sort field name (default: `sort`)               |
| `targetScope` | object | No       | Scope for sorting (e.g. `{ "parentId": 1 }`)   |
| `method`      | string | No       | `insertAfter`, `insertBefore`, or `prepend`     |

---

### 13.9 Association Actions

For managing many-to-many and one-to-many relationships:

**Add association:**

```bash
curl -X POST 'https://{nocobase-url}/api/users/1/roles:add' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '["admin", "editor"]'
```

**Remove association:**

```bash
curl -X POST 'https://{nocobase-url}/api/users/1/roles:remove' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '["editor"]'
```

**Set association (replace all):**

```bash
curl -X POST 'https://{nocobase-url}/api/users/1/roles:set' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '["admin"]'
```

**Toggle association:**

```bash
curl -X POST 'https://{nocobase-url}/api/users/1/roles:toggle' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '["editor"]'
```

---

### Filter Syntax

NocoBase uses a JSON-based filter syntax. Common operators:

| Operator       | Description                    | Example                                    |
|----------------|--------------------------------|--------------------------------------------|
| `$eq`          | Equal                          | `{ "status": { "$eq": "active" } }`       |
| `$ne`          | Not equal                      | `{ "status": { "$ne": "deleted" } }`      |
| `$gt`          | Greater than                   | `{ "age": { "$gt": 18 } }`               |
| `$gte`         | Greater than or equal          | `{ "age": { "$gte": 18 } }`              |
| `$lt`          | Less than                      | `{ "price": { "$lt": 100 } }`            |
| `$lte`         | Less than or equal             | `{ "price": { "$lte": 100 } }`           |
| `$in`          | In array                       | `{ "status": { "$in": ["a", "b"] } }`    |
| `$notIn`       | Not in array                   | `{ "status": { "$notIn": ["deleted"] } }` |
| `$includes`    | Contains substring             | `{ "name": { "$includes": "john" } }`    |
| `$notIncludes` | Does not contain               | `{ "name": { "$notIncludes": "test" } }`  |
| `$empty`       | Is null/empty                  | `{ "email": { "$empty": true } }`        |
| `$notEmpty`    | Is not null/empty              | `{ "email": { "$notEmpty": true } }`     |
| `$and`         | Logical AND                    | `{ "$and": [ ... ] }`                     |
| `$or`          | Logical OR                     | `{ "$or": [ ... ] }`                      |

**Association filtering:**

```json
{
  "roles.name": { "$eq": "admin" }
}
```

**Date filtering:**

```json
{
  "createdAt": {
    "$dateOn": "2024-01-01"
  }
}
```
