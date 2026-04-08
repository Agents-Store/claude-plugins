# Flow Model Endpoints Reference

Complete endpoint reference for flow models (v2.x block engine), flow SQL, and template variables.

## Flow Models — Endpoint Summary

| Method | Endpoint | Description | ACL |
|--------|----------|-------------|-----|
| GET | `/api/flowModels:findOne` | Get model by uid or parentId | `loggedIn` |
| POST | `/api/flowModels:save` | Create or update (upsert) | `ui.flowModels` |
| POST | `/api/flowModels:duplicate?uid={uid}` | Deep copy with new uids | `ui.flowModels` |
| POST | `/api/flowModels:attach` | Attach model as child | `ui.flowModels` |
| POST | `/api/flowModels:move` | Reposition model | `ui.flowModels` |
| POST | `/api/flowModels:destroy?filterByTk={uid}` | Remove model and descendants | `ui.flowModels` |

## Inherited Schema Actions

These work identically to `uiSchemas` but use `options` key instead of `schema` in payloads.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/flowModels:getJsonSchema/{uid}` | Full nested model tree |
| GET | `/api/flowModels:getProperties/{uid}` | Immediate children |
| GET | `/api/flowModels:getParentJsonSchema/{uid}` | Parent model tree |
| GET | `/api/flowModels:getParentProperty/{uid}` | Parent property metadata |
| POST | `/api/flowModels:insert` | Create root-level model |
| POST | `/api/flowModels:insertNewSchema` | Bulk-insert (SQL optimized) |
| POST | `/api/flowModels:patch` | Update single model |
| POST | `/api/flowModels:batchPatch` | Update multiple models |
| POST | `/api/flowModels:remove/{uid}` | Remove model and descendants |
| POST | `/api/flowModels:clearAncestor/{uid}` | Detach from parent |
| POST | `/api/flowModels:insertAdjacent/{uid}?position=X` | Insert relative to model |
| POST | `/api/flowModels:insertBeforeBegin/{uid}` | Insert as sibling before |
| POST | `/api/flowModels:insertAfterBegin/{uid}` | Insert as first child |
| POST | `/api/flowModels:insertBeforeEnd/{uid}` | Insert as last child |
| POST | `/api/flowModels:insertAfterEnd/{uid}` | Insert as sibling after |
| POST | `/api/flowModels:initializeActionContext` | Lazy-init action context |

## Flow SQL — Endpoint Summary

| Method | Endpoint | Description | ACL |
|--------|----------|-------------|-----|
| POST | `/api/flowSql:save` | Save SQL query | `ui.flowSql` |
| POST | `/api/flowSql:runById` | Execute saved SQL | `loggedIn` |
| GET | `/api/flowSql:getBind?uid={uid}` | Get bind parameters | `loggedIn` |

## Variables — Endpoint Summary

| Method | Endpoint | Description | ACL |
|--------|----------|-------------|-----|
| POST | `/api/variables:resolve` | Resolve template variables | `loggedIn` |

## findOne Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `uid` | string | No | Flow model uid (use this OR parentId) |
| `parentId` | string | No | Parent model uid |
| `subKey` | string | No | Child key type filter (`properties`, `items`) |
| `includeAsyncNode` | boolean | No | Include async child nodes (default: false) |

## save Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `uid` | string | No | Model uid (auto-generated if omitted) |
| `name` | string | No | Model name |
| `use` | string | No | Model class name |
| `stepParams` | object | No | Step parameters |
| `title` | string | No | Display title |
| `parentId` | string | No | Parent uid (attach as child) |
| `subKey` | string | No | Child key under parent |
| `properties` | object | No | Nested child models |

Response: `{ "data": "<uid>" }`

## attach Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `uid` | string | Yes | uid of model to attach |
| `parentId` | string | Yes | uid of target parent |
| `subKey` | string | Yes | Key under which to attach |
| `subType` | string | Yes | `"object"` or `"array"` |
| `position` | string | No | `"first"`, `"last"`, or position object |

## move Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sourceId` | string | Yes | uid of model to move |
| `targetId` | string | Yes | uid of reference model |
| `position` | string | Yes | `"before"` or `"after"` |

## flowSql:save Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `uid` | string | Yes | Flow SQL identifier |
| `sql` | string | Yes | SQL with Liquid templates and bind params |
| `dataSourceKey` | string | No | Data source key |

## flowSql:runById Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `uid` | string | Yes | Flow SQL identifier |
| `type` | string | No | SQL type (`SELECT`, `INSERT`, etc.) |
| `filter` | object | No | Additional filters |
| `bind` | object | No | Bind parameters |
| `liquidContext` | object | No | Liquid template context |
| `dataSourceKey` | string | No | Data source key override |

## variables:resolve Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `template` | any | Yes* | JSON template with variable placeholders |
| `contextParams` | object | No | Context parameters for resolution |
| `batch` | array | Yes* | Array of `{ id?, template, contextParams }` |

*Either `template` or `batch` is required.

## Model Class Names

Common `use` values for flow models:

| Model Class | Description |
|-------------|-------------|
| `TableBlockModel` | Data table block |
| `FormBlockModel` | Form block (create/edit) |
| `DetailsBlockModel` | Read-only detail view |
| `KanbanBlockModel` | Kanban board |
| `CalendarBlockModel` | Calendar view |
| `RouteModel` | Page route model |
| `ReferenceBlockModel` | Block referencing a template |
| `ActionBarModel` | Group of action buttons |
| `FormFieldModel` | Individual form field |
| `FormFieldListModel` | List of form fields |
| `TableColumnModel` | Table column definition |

## ACL Summary

| Resource | Read Actions | Write Actions |
|----------|-------------|---------------|
| `flowModels` | `loggedIn` (findOne, getJsonSchema, getProperties) | `ui.flowModels` (save, duplicate, attach, move, destroy, insert, patch, remove) |
| `flowSql` | `loggedIn` (runById, getBind) | `ui.flowSql` (save) |
| `variables` | — | `loggedIn` (resolve) |
