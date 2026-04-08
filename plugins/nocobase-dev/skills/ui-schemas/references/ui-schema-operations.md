# UI Schema Operations Reference

Detailed request/response formats, position semantics, and worked examples for all NocoBase V2 UI schema operations.

## Operation Index

| Operation | Method | Path | Purpose |
|-----------|--------|------|---------|
| getJsonSchema | GET | `/api/uiSchemas:getJsonSchema/{uid}` | Full nested schema tree |
| getProperties | GET | `/api/uiSchemas:getProperties/{uid}` | Immediate children only |
| getParentJsonSchema | GET | `/api/uiSchemas:getParentJsonSchema/{uid}` | Parent node schema tree |
| getParentProperty | GET | `/api/uiSchemas:getParentProperty/{uid}` | Parent property metadata |
| insert | POST | `/api/uiSchemas:insert` | Create root-level node |
| insertNewSchema | POST | `/api/uiSchemas:insertNewSchema` | Bulk-insert (SQL optimized) |
| remove | POST | `/api/uiSchemas:remove/{uid}` | Delete node and descendants |
| patch | POST | `/api/uiSchemas:patch` | Update single node |
| batchPatch | POST | `/api/uiSchemas:batchPatch` | Update multiple nodes |
| insertAdjacent | POST | `/api/uiSchemas:insertAdjacent/{uid}?position=X` | Insert relative to node |
| insertBeforeBegin | POST | `/api/uiSchemas:insertBeforeBegin/{uid}` | Insert as sibling before |
| insertAfterBegin | POST | `/api/uiSchemas:insertAfterBegin/{uid}` | Insert as first child |
| insertBeforeEnd | POST | `/api/uiSchemas:insertBeforeEnd/{uid}` | Insert as last child |
| insertAfterEnd | POST | `/api/uiSchemas:insertAfterEnd/{uid}` | Insert as sibling after |
| initializeActionContext | POST | `/api/uiSchemas:initializeActionContext` | Lazy-init action context |
| saveAsTemplate | POST | `/api/uiSchemas:saveAsTemplate?filterByTk={uid}` | Save subtree as template |
| clearAncestor | POST | `/api/uiSchemas:clearAncestor/{uid}` | Detach from parent |

## getJsonSchema

**Request:**
```
GET /api/uiSchemas:getJsonSchema/{uid}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "data": {
    "type": "void",
    "x-uid": "abc123",
    "x-component": "Page",
    "x-component-props": {
      "title": "Orders"
    },
    "properties": {
      "grid1": {
        "type": "void",
        "x-uid": "grid1uid",
        "x-component": "Grid",
        "properties": {
          "row1": {
            "type": "void",
            "x-uid": "row1uid",
            "x-component": "Grid.Row",
            "properties": {
              "col1": {
                "type": "void",
                "x-uid": "col1uid",
                "x-component": "Grid.Col",
                "properties": {
                  "block1": {
                    "type": "void",
                    "x-uid": "block1uid",
                    "x-component": "TableBlockProvider",
                    "x-component-props": {
                      "collection": "orders"
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

The response is a deeply nested JSON structure. Navigate `properties` to find specific child components.

## insertAdjacent Position Options

The position parameter controls where the new schema is placed relative to the target node (identified by `uid` in the URL path).

```
                    beforeBegin
                         |
  [parent] ─── [ target node ] ─── [sibling]
                  |          |
            afterBegin    beforeEnd
                                |
                           afterEnd
```

### beforeBegin

Insert as a **sibling before** the target node. The new node shares the same parent.

```
Before: parent → [A, TARGET, B]
After:  parent → [A, NEW, TARGET, B]
```

### afterBegin

Insert as the **first child** of the target node.

```
Before: TARGET → [child1, child2]
After:  TARGET → [NEW, child1, child2]
```

### beforeEnd

Insert as the **last child** of the target node.

```
Before: TARGET → [child1, child2]
After:  TARGET → [child1, child2, NEW]
```

### afterEnd

Insert as a **sibling after** the target node. The new node shares the same parent.

```
Before: parent → [A, TARGET, B]
After:  parent → [A, TARGET, NEW, B]
```

## Example: Creating a Form Block

Add a form block for the `contacts` collection to an existing page.

### Step 1: Get the Page Schema

```bash
curl -X GET "${NOCOBASE_URL}/api/uiSchemas:getJsonSchema/pageUid123" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Find the `Grid` component's `x-uid` in the response. Suppose it is `gridUid456`.

### Step 2: Insert a New Grid Row with Form Block

```bash
curl -X POST "${NOCOBASE_URL}/api/uiSchemas:insertAdjacent/gridUid456?position=beforeEnd" \
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
          "properties": {
            "formBlock": {
              "type": "void",
              "x-component": "FormBlockProvider",
              "x-decorator": "BlockItem",
              "x-component-props": {
                "collection": "contacts",
                "action": "create"
              },
              "properties": {
                "form": {
                  "type": "void",
                  "x-component": "FormV2",
                  "properties": {
                    "name": {
                      "type": "string",
                      "x-component": "CollectionField",
                      "x-decorator": "FormItem",
                      "x-collection-field": "contacts.name"
                    },
                    "email": {
                      "type": "string",
                      "x-component": "CollectionField",
                      "x-decorator": "FormItem",
                      "x-collection-field": "contacts.email"
                    },
                    "actions": {
                      "type": "void",
                      "x-component": "ActionBar",
                      "properties": {
                        "submit": {
                          "type": "void",
                          "x-component": "Action",
                          "x-component-props": {
                            "type": "primary",
                            "htmlType": "submit"
                          },
                          "title": "Submit"
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }'
```

This creates a complete form block with:
- A Grid row and column wrapper
- A FormBlockProvider targeting the `contacts` collection
- Form fields for `name` and `email`
- A submit action button

## Example: Adding a Table Column

Add a new column to an existing table block.

### Step 1: Find the Table Schema

```bash
curl -X GET "${NOCOBASE_URL}/api/uiSchemas:getJsonSchema/tableBlockUid" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Locate the `Table.Column` container inside the table schema. Suppose its uid is `columnsUid`.

### Step 2: Insert a New Column

```bash
curl -X POST "${NOCOBASE_URL}/api/uiSchemas:insertAdjacent/columnsUid?position=beforeEnd" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "schema": {
      "type": "void",
      "x-component": "Table.Column",
      "x-component-props": {
        "title": "Phone"
      },
      "properties": {
        "phone": {
          "type": "string",
          "x-component": "CollectionField",
          "x-read-pretty": true,
          "x-collection-field": "contacts.phone"
        }
      }
    }
  }'
```

## Example: Batch Update Hidden State

Hide multiple schema nodes at once.

```bash
curl -X POST "${NOCOBASE_URL}/api/uiSchemas:batchPatch" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '[
    { "x-uid": "field1uid", "x-hidden": true },
    { "x-uid": "field2uid", "x-hidden": true },
    { "x-uid": "field3uid", "x-hidden": true }
  ]'
```

## Theme Configuration Structure

Full theme config follows the Ant Design 5.x token system.

```json
{
  "name": "Corporate Theme",
  "config": {
    "token": {
      "colorPrimary": "#1677ff",
      "colorSuccess": "#52c41a",
      "colorWarning": "#faad14",
      "colorError": "#ff4d4f",
      "colorInfo": "#1677ff",
      "colorTextBase": "#000000",
      "colorBgBase": "#ffffff",
      "colorBgContainer": "#ffffff",
      "colorBgLayout": "#f5f5f5",
      "colorBgElevated": "#ffffff",
      "borderRadius": 6,
      "fontSize": 14,
      "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      "lineHeight": 1.5714,
      "controlHeight": 32,
      "wireframe": false
    }
  },
  "default": true
}
```

### Key Token Groups

**Colors:**
- `colorPrimary` — brand/accent color, used for buttons, links, active states
- `colorSuccess/Warning/Error/Info` — semantic status colors
- `colorTextBase` — base text color (system derives `colorText`, `colorTextSecondary`, etc.)
- `colorBgBase` — base background (system derives all background shades)

**Typography:**
- `fontSize` — base font size (14px default)
- `fontFamily` — font stack
- `lineHeight` — base line height multiplier

**Layout:**
- `borderRadius` — default radius for cards, buttons, inputs
- `controlHeight` — height of inputs, buttons (32px default)
- `wireframe` — if `true`, components use outlined/wireframe style

Set `"default": true` on a theme to apply it globally. Only one theme can be the default at a time.

## Common Schema Component Types

| x-component | Purpose |
|-------------|---------|
| `Page` | Top-level page container |
| `Grid` | Layout grid container |
| `Grid.Row` | Grid row |
| `Grid.Col` | Grid column |
| `TableBlockProvider` | Data table block |
| `Table` | Table renderer |
| `Table.Column` | Table column definition |
| `FormBlockProvider` | Form block (create/edit) |
| `FormV2` | Form renderer |
| `FormItem` | Form field wrapper (decorator) |
| `CollectionField` | Auto-configured field from collection |
| `Action` | Button/action |
| `ActionBar` | Group of action buttons |
| `BlockItem` | Generic block wrapper (decorator) |
| `CardItem` | Card-style block wrapper |
| `Menu` | Navigation menu |
| `Menu.Item` | Menu entry |
| `Tabs` | Tab container |
| `Tabs.TabPane` | Individual tab |
| `Details` | Read-only detail view |
| `Kanban` | Kanban board block |
| `Calendar` | Calendar view block |
| `Markdown` | Markdown content block |

## Schema Inspection Tips

1. **Start from the root** — every NocoBase page has a root schema node; get its uid from the URL or the `systemSettings`.
2. **Navigate by component type** — look for `Grid` to find the layout, `TableBlockProvider` for tables, `FormBlockProvider` for forms.
3. **Check x-collection-field** — this tells you which collection field a UI element is bound to.
4. **Use x-hidden** — set `"x-hidden": true` to hide a component without removing it.
5. **Respect the Grid** — all blocks live inside `Grid > Grid.Row > Grid.Col` hierarchy.

## Legacy Templates (uiSchemaTemplates)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/uiSchemaTemplates:list` | List all block templates |
| GET | `/api/uiSchemaTemplates:get?filterByTk={key}` | Get a template by key |

Template fields: `key` (PK), `name`, `componentName`, `associationName`, `resourceName`, `collectionName`, `dataSourceKey`, `uid` (FK to `uiSchemas.x-uid`).

## Flow Model Templates (v2.x+)

New template system with usage tracking and reference block support.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/flowModelTemplates:list` | List templates (paginated, searchable) |
| GET | `/api/flowModelTemplates:get?filterByTk={uid}` | Get template by uid |
| POST | `/api/flowModelTemplates:create` | Create template from block |
| POST | `/api/flowModelTemplates:update?filterByTk={uid}` | Update template metadata |
| POST | `/api/flowModelTemplates:destroy?filterByTk={uid}` | Delete template (if unused) |

### Create Flow Model Template

```json
{
  "name": "User Form Template",
  "description": "Reusable form block",
  "targetUid": "block_uid",
  "useModel": "FormBlockModel",
  "type": "block",
  "dataSourceKey": "main",
  "collectionName": "users",
  "detachParent": true
}
```

Fields: `uid`, `name`, `description`, `targetUid`, `useModel` (`TableBlockModel`, `FormBlockModel`, etc.), `type`, `dataSourceKey`, `collectionName`, `associationName`, `detachParent`, `usageCount`.

### Destroy Validation

Fails with HTTP 400 if `usageCount > 0`:

```json
{
  "errors": [{
    "code": "TEMPLATE_IN_USE",
    "message": "Template is in use and cannot be deleted",
    "data": { "usageCount": 3 }
  }]
}
```

Remove all blocks using the template before deletion.
