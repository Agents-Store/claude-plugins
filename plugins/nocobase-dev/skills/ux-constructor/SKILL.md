---
name: ux-constructor
description: |
  Modern Page (v2) creation and editing — the correct algorithm for building pages, adding blocks (table, form), configuring columns, and editing existing UX components via the NocoBase API. Use when:
  - "create a NocoBase page"
  - "add a modern page"
  - "build a page with a table block"
  - "create page for collection"
  - "add form block to page"
  - "NocoBase UX constructor"
  - "flowPage creation"
  - "Modern page v2 API"
  - "add table block with columns"
  - "programmatic page creation"
  - "create UI via API"
  - "hide a column"
  - "show a column"
  - "remove a column from table"
  - "change column width"
  - "enable inline editing"
  - "edit table column settings"
  - "remove row action"
  - "modify existing page blocks"
---

# UX Constructor — Modern Page (v2)

Build NocoBase pages and blocks programmatically using the correct API request sequence. This skill documents the **verified algorithm** captured from the NocoBase v2.x visual constructor's network traffic.

## Authentication

All requests require:

```
Authorization: Bearer ${NOCOBASE_API_KEY}
Content-Type: application/json
X-Role: root
```

Base URL: `${NOCOBASE_URL}/api/`

## Critical Differences: Classic (v1) vs Modern (v2)

| Aspect | Classic page (v1) | Modern page (v2) |
|--------|-------------------|-------------------|
| Route type | `"page"` | `"flowPage"` |
| Schema component | `"Page"` | `"FlowRoute"` |
| Block storage | `uiSchemas:insertAdjacent` | `flowModels:save` |
| Block definition | JSON schema nodes | Flow model objects with `use` class |
| Model hierarchy | Flat schema tree | `RootPageModel` -> `BlockGridModel` -> `*BlockModel` |
| Tab support | Manual schema children | Built-in via `children` array in route |

**Always use Modern page (v2) for new pages.** Classic pages are legacy.

## UID Generation

NocoBase uses 11-character random alphanumeric strings as UIDs. Generate them as:

```
characters: a-z, 0-9
length: 11
example: "6s65g65nq2f"
```

All UIDs referenced below must be pre-generated before making API calls.

## Algorithm: Create a Modern Page (v2) with Table Block

### Phase 1: Create the Route

**Step 1 — Create desktop route**

```bash
curl -X POST "${NOCOBASE_URL}/api/desktopRoutes:create" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "flowPage",
    "title": "My Page",
    "icon": "tableoutlined",
    "parentId": null,
    "schemaUid": "<PAGE_SCHEMA_UID>",
    "menuSchemaUid": "<MENU_SCHEMA_UID>",
    "enableTabs": false,
    "children": [{
      "type": "tabs",
      "schemaUid": "<TAB_SCHEMA_UID>",
      "tabSchemaName": "<TAB_SCHEMA_NAME>",
      "hidden": true
    }]
  }'
```

Key fields:
- `type`: must be `"flowPage"` (NOT `"page"`)
- `parentId`: parent group route ID (null for root-level, or a group route ID)
- `schemaUid`: random UID — becomes the page's URL slug (`/admin/<schemaUid>`)
- `menuSchemaUid`: random UID for the menu item schema
- `children[0]`: a hidden tab container — always include even for non-tabbed pages
- `children[0].schemaUid`: random UID for the tab's content area (blocks go here)
- `children[0].tabSchemaName`: random UID used as the tab name

**Step 2 — Refresh routes** (ensure menu updates)

```bash
curl -X GET "${NOCOBASE_URL}/api/desktopRoutes:listAccessible" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "X-Role: root"
```

**Step 3 — Create the page schema node**

```bash
curl -X POST "${NOCOBASE_URL}/api/uiSchemas:insert" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "void",
    "x-component": "FlowRoute",
    "x-uid": "<PAGE_SCHEMA_UID>"
  }'
```

Must use `"FlowRoute"` component (NOT `"Page"` or `"Grid"`). The `x-uid` must match `schemaUid` from Step 1.

### Phase 2: Initialize Flow Models

**Step 4 — Create the RootPageModel**

```bash
curl -X POST "${NOCOBASE_URL}/api/flowModels:save" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "<ROOT_PAGE_UID>",
    "async": true,
    "parentId": "<PAGE_SCHEMA_UID>",
    "subKey": "page",
    "subType": "object",
    "use": "RootPageModel",
    "stepParams": {},
    "sortIndex": 0,
    "flowRegistry": {}
  }'
```

`parentId` = the page's `schemaUid` from Step 1.

**Step 5 — Create the BlockGridModel** (container for blocks)

```bash
curl -X POST "${NOCOBASE_URL}/api/flowModels:save" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "<BLOCK_GRID_UID>",
    "parentId": "<TAB_SCHEMA_UID>",
    "subKey": "grid",
    "async": true,
    "subType": "object",
    "use": "BlockGridModel",
    "stepParams": {},
    "sortIndex": 0,
    "flowRegistry": {},
    "filterManager": []
  }'
```

`parentId` = the tab's `schemaUid` from Step 1 children[0]. This is where blocks are placed.

### Phase 3: Add a Table Block

**Step 6 — Create the TableBlockModel**

```bash
curl -X POST "${NOCOBASE_URL}/api/flowModels:save" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "<TABLE_BLOCK_UID>",
    "use": "TableBlockModel",
    "subModels": {
      "columns": [{
        "uid": "<ACTIONS_COLUMN_UID>",
        "use": "TableActionsColumnModel",
        "parentId": "<TABLE_BLOCK_UID>",
        "subKey": "columns",
        "subType": "array",
        "stepParams": {},
        "sortIndex": 0,
        "flowRegistry": {}
      }]
    },
    "stepParams": {
      "resourceSettings": {
        "init": {
          "dataSourceKey": "main",
          "collectionName": "<COLLECTION_NAME>"
        }
      }
    },
    "parentId": "<BLOCK_GRID_UID>",
    "subKey": "items",
    "subType": "array",
    "sortIndex": 1,
    "flowRegistry": {}
  }'
```

Key:
- `use`: `"TableBlockModel"` for tables
- `subModels.columns[0]`: always include `TableActionsColumnModel` as the first column (row action buttons)
- `stepParams.resourceSettings.init.collectionName`: the data collection to display
- `parentId`: the `BlockGridModel` UID from Step 5

### Phase 4: Add Table Columns

For each field you want to display, create a `TableColumnModel`:

```bash
curl -X POST "${NOCOBASE_URL}/api/flowModels:save" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "<COLUMN_UID>",
    "use": "TableColumnModel",
    "stepParams": {
      "fieldSettings": {
        "init": {
          "dataSourceKey": "main",
          "collectionName": "<COLLECTION_NAME>",
          "fieldPath": "<FIELD_NAME>"
        }
      },
      "tableColumnSettings": {
        "model": {
          "use": "<DISPLAY_MODEL>"
        }
      }
    },
    "subModels": {
      "field": {
        "uid": "<FIELD_UID>",
        "use": "<DISPLAY_MODEL>",
        "props": null,
        "parentId": "<COLUMN_UID>",
        "subKey": "field",
        "subType": "object",
        "stepParams": {
          "popupSettings": {
            "openView": {
              "collectionName": "<COLLECTION_NAME>",
              "dataSourceKey": "main"
            }
          }
        },
        "sortIndex": 0,
        "flowRegistry": {}
      }
    },
    "parentId": "<TABLE_BLOCK_UID>",
    "subKey": "columns",
    "subType": "array",
    "sortIndex": <N>,
    "flowRegistry": {}
  }'
```

- `sortIndex`: starts at 2 (0 = actions column, 1 = block itself), increment for each column
- `parentId`: the `TableBlockModel` UID from Step 6
- `<DISPLAY_MODEL>`: must match in both `tableColumnSettings.model.use` AND `subModels.field.use`

### Display Model Mapping

Map NocoBase field interfaces to display models:

| Field Interface | Display Model |
|----------------|---------------|
| `input`, `textarea`, `url`, `email`, `phone` | `DisplayTextFieldModel` |
| `select`, `radioGroup` | `DisplayEnumFieldModel` |
| `password` | `DisplayPasswordFieldModel` |
| `richText` | `DisplayRichTextFieldModel` |
| `integer`, `number`, `percent`, `id` | `DisplayTextFieldModel` |
| `datetime`, `createdAt`, `updatedAt` | `DisplayTextFieldModel` |
| `json` | `DisplayTextFieldModel` |

When unsure, default to `DisplayTextFieldModel` — it works for any field type.

## Algorithm: Add "Add New" Button with Creation Form

The "Add new" button opens a popup with a creation form. This requires a chain of models.

**Step A — Create the AddNewActionModel** (button on the table toolbar)

```bash
curl -X POST "${NOCOBASE_URL}/api/flowModels:save" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "<ADD_NEW_ACTION_UID>",
    "use": "AddNewActionModel",
    "parentId": "<TABLE_BLOCK_UID>",
    "subKey": "actions",
    "subType": "array",
    "stepParams": {
      "popupSettings": {
        "openView": {
          "collectionName": "<COLLECTION_NAME>",
          "dataSourceKey": "main"
        }
      }
    },
    "sortIndex": 1,
    "flowRegistry": {}
  }'
```

**Step B — Create ChildPageModel** (the popup container)

```bash
curl -X POST "${NOCOBASE_URL}/api/flowModels:save" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "<CHILD_PAGE_UID>",
    "async": true,
    "parentId": "<ADD_NEW_ACTION_UID>",
    "subKey": "page",
    "subType": "object",
    "use": "ChildPageModel",
    "subModels": {
      "tabs": [{
        "uid": "<CHILD_TAB_UID>",
        "use": "ChildPageTabModel",
        "stepParams": {
          "pageTabSettings": {
            "tab": { "title": "Add new" }
          }
        },
        "parentId": "<CHILD_PAGE_UID>",
        "subKey": "tabs",
        "subType": "array",
        "sortIndex": 0,
        "flowRegistry": {}
      }]
    },
    "stepParams": {
      "pageSettings": {
        "general": { "displayTitle": false, "enableTabs": true }
      }
    },
    "sortIndex": 0,
    "flowRegistry": {}
  }'
```

**Step C — Create BlockGridModel inside the tab**

```bash
curl -X POST "${NOCOBASE_URL}/api/flowModels:save" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "<POPUP_GRID_UID>",
    "parentId": "<CHILD_TAB_UID>",
    "subKey": "grid",
    "async": true,
    "subType": "object",
    "use": "BlockGridModel",
    "stepParams": {},
    "sortIndex": 0,
    "flowRegistry": {},
    "filterManager": []
  }'
```

**Step D — Create CreateFormModel** (the actual form)

```bash
curl -X POST "${NOCOBASE_URL}/api/flowModels:save" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "<CREATE_FORM_UID>",
    "use": "CreateFormModel",
    "subModels": {
      "grid": {
        "uid": "<FORM_GRID_UID>",
        "use": "FormGridModel",
        "parentId": "<CREATE_FORM_UID>",
        "subKey": "grid",
        "subType": "object",
        "stepParams": {},
        "sortIndex": 0,
        "flowRegistry": {}
      }
    },
    "stepParams": {
      "resourceSettings": {
        "init": {
          "dataSourceKey": "main",
          "collectionName": "<COLLECTION_NAME>"
        }
      }
    },
    "parentId": "<POPUP_GRID_UID>",
    "subKey": "items",
    "subType": "array",
    "sortIndex": 1,
    "flowRegistry": {}
  }'
```

**Step E — Add form fields** (one per field)

```bash
curl -X POST "${NOCOBASE_URL}/api/flowModels:save" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "<FORM_ITEM_UID>",
    "use": "FormItemModel",
    "stepParams": {
      "fieldSettings": {
        "init": {
          "dataSourceKey": "main",
          "collectionName": "<COLLECTION_NAME>",
          "fieldPath": "<FIELD_NAME>"
        }
      }
    },
    "subModels": {
      "field": {
        "uid": "<FORM_FIELD_UID>",
        "use": "<EDIT_FIELD_MODEL>",
        "props": null,
        "parentId": "<FORM_ITEM_UID>",
        "subKey": "field",
        "subType": "object",
        "stepParams": {},
        "sortIndex": 0,
        "flowRegistry": {}
      }
    },
    "parentId": "<FORM_GRID_UID>",
    "subKey": "items",
    "subType": "array",
    "sortIndex": <N>,
    "flowRegistry": {}
  }'
```

### Edit Field Model Mapping (for forms)

| Field Interface | Edit Field Model |
|----------------|-----------------|
| `input`, `url`, `email`, `phone` | `TextFieldModel` |
| `textarea` | `TextAreaFieldModel` |
| `select`, `radioGroup` | `SelectFieldModel` |
| `datetime`, `createdAt` | `DateTimeTzFieldModel` |
| `integer`, `number` | `NumberFieldModel` |
| `richText` | `RichTextFieldModel` |
| `password` | `PasswordFieldModel` |
| `belongsTo` association | `RecordSelectFieldModel` |

## Algorithm: Add Row Actions (View/Edit/Delete)

Row actions are added to the `TableActionsColumnModel`'s parent (which has `subKey: "actions"`).

```bash
# View button
curl -X POST "${NOCOBASE_URL}/api/flowModels:save" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "<VIEW_ACTION_UID>",
    "use": "ViewActionModel",
    "parentId": "<TABLE_ACTIONS_COLUMN_UID>",
    "subKey": "actions",
    "subType": "array",
    "stepParams": {
      "popupSettings": {
        "openView": {
          "collectionName": "<COLLECTION_NAME>",
          "dataSourceKey": "main"
        }
      },
      "buttonSettings": {
        "general": { "type": "link", "icon": null }
      }
    },
    "sortIndex": 1,
    "flowRegistry": {}
  }'

# Edit button (same structure, use EditActionModel, sortIndex 2)
# Delete button (use DeleteActionModel, sortIndex 3)
```

Action models: `ViewActionModel`, `EditActionModel`, `DeleteActionModel`

## Algorithm: Add Association Column

To display a field from a related collection (e.g. show post title in calendar):

```bash
curl -X POST "${NOCOBASE_URL}/api/flowModels:save" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "<COLUMN_UID>",
    "use": "TableColumnModel",
    "stepParams": {
      "fieldSettings": {
        "init": {
          "dataSourceKey": "main",
          "collectionName": "<COLLECTION_NAME>",
          "fieldPath": "<ASSOCIATION_NAME>.<FIELD_NAME>",
          "associationPathName": "<ASSOCIATION_NAME>"
        }
      },
      "tableColumnSettings": {
        "model": { "use": "DisplayTextFieldModel" }
      }
    },
    "subModels": {
      "field": {
        "uid": "<FIELD_UID>",
        "use": "DisplayTextFieldModel",
        "parentId": "<COLUMN_UID>",
        "subKey": "field",
        "subType": "object",
        "stepParams": {
          "popupSettings": {
            "openView": {
              "collectionName": "<RELATED_COLLECTION>",
              "associationName": "<COLLECTION_NAME>.<ASSOCIATION_NAME>",
              "dataSourceKey": "main"
            }
          }
        },
        "sortIndex": 0,
        "flowRegistry": {}
      }
    },
    "parentId": "<TABLE_BLOCK_UID>",
    "subKey": "columns",
    "subType": "array",
    "sortIndex": <N>,
    "flowRegistry": {}
  }'
```

Key difference: `fieldPath` uses dot notation (`post.title`), and `associationPathName` specifies the association name.

## Editing Existing UX Components

The `flowModels:save` endpoint handles both **create** and **update**. If you pass a `uid` that already exists, it updates the existing flow model. If the `uid` is new, it creates a new one.

### Hide/Remove a Table Column

Hiding a column in the Fields toggle **deletes** the flow model entirely:

```bash
curl -X POST "${NOCOBASE_URL}/api/flowModels:destroy?filterByTk=<COLUMN_UID>" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

- No request body — the column UID is passed as `filterByTk` query parameter
- This permanently removes the `TableColumnModel` and its child `field` subModel
- To show the column again, you must create a new `TableColumnModel` (Phase 4)
- After destroying, refresh table data: `GET <COLLECTION>:list?page=1&pageSize=20&tree=false`

### Show a Hidden Column (re-add)

Toggling a field ON in the Fields dropdown creates a new `TableColumnModel` — identical to Phase 4 but with a new UID:

```bash
curl -X POST "${NOCOBASE_URL}/api/flowModels:save" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "<NEW_COLUMN_UID>",
    "use": "TableColumnModel",
    "stepParams": {
      "fieldSettings": {
        "init": {
          "dataSourceKey": "main",
          "collectionName": "<COLLECTION_NAME>",
          "fieldPath": "<FIELD_NAME>"
        }
      },
      "tableColumnSettings": {
        "model": { "use": "<DISPLAY_MODEL>" }
      }
    },
    "subModels": {
      "field": {
        "uid": "<NEW_FIELD_UID>",
        "use": "<DISPLAY_MODEL>",
        "props": null,
        "parentId": "<NEW_COLUMN_UID>",
        "subKey": "field",
        "subType": "object",
        "stepParams": {
          "popupSettings": {
            "openView": {
              "collectionName": "<COLLECTION_NAME>",
              "dataSourceKey": "main"
            }
          }
        },
        "sortIndex": 0,
        "flowRegistry": {}
      }
    },
    "parentId": "<TABLE_BLOCK_UID>",
    "subKey": "columns",
    "subType": "array",
    "sortIndex": <N>,
    "flowRegistry": {}
  }'
```

### Update Column Settings

To change column width, enable inline editing, or modify other settings, send `flowModels:save` with the **existing column UID** and only the fields you want to update. The `subModels.field` can be omitted for settings-only updates:

```bash
curl -X POST "${NOCOBASE_URL}/api/flowModels:save" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "<EXISTING_COLUMN_UID>",
    "use": "TableColumnModel",
    "stepParams": {
      "fieldSettings": {
        "init": {
          "dataSourceKey": "main",
          "collectionName": "<COLLECTION_NAME>",
          "fieldPath": "<FIELD_NAME>"
        }
      },
      "tableColumnSettings": {
        "model": { "use": "<DISPLAY_MODEL>" },
        "width": { "width": 150 },
        "quickEdit": { "editable": true }
      }
    },
    "parentId": "<TABLE_BLOCK_UID>",
    "subKey": "columns",
    "subType": "array",
    "sortIndex": <CURRENT_SORT_INDEX>,
    "flowRegistry": {}
  }'
```

### Column Settings Reference

Available keys inside `tableColumnSettings`:

| Key | Format | Description |
|-----|--------|-------------|
| `model` | `{ "use": "<DisplayModel>" }` | Display model class (required) |
| `width` | `{ "width": <pixels> }` | Fixed column width in pixels |
| `quickEdit` | `{ "editable": true }` | Enable inline editing in table cells |

### Remove a Row Action

Same as hiding a column — destroy the action's flow model:

```bash
curl -X POST "${NOCOBASE_URL}/api/flowModels:destroy?filterByTk=<ACTION_UID>" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Works for `ViewActionModel`, `EditActionModel`, `DeleteActionModel`, `AddNewActionModel`.

## Known Block Model Types

| Model | Purpose |
|-------|---------|
| `RootPageModel` | Page root (one per page) |
| `BlockGridModel` | Grid container for blocks |
| `TableBlockModel` | Data table |
| `CreateFormModel` | Record creation form (inside "Add new" popup) |
| `FormGridModel` | Form layout grid |
| `FormItemModel` | Single form field wrapper |
| `TableActionsColumnModel` | Row action buttons column |
| `TableColumnModel` | Single table column |
| `AddNewActionModel` | "Add new" toolbar button |
| `ViewActionModel` | Row "View" button |
| `EditActionModel` | Row "Edit" button |
| `DeleteActionModel` | Row "Delete" button |
| `ChildPageModel` | Popup/drawer page container |
| `ChildPageTabModel` | Tab inside a popup |
| `ActionBarModel` | Action button bar |
| `ReferenceBlockModel` | Template reference block |

## Common Workflows

### Create a page for each collection in the database

```
1. GET collections:list?paginate=false&appends[]=fields  → get all collections with fields
2. GET desktopRoutes:listAccessible  → find existing pages to avoid duplicates
3. For each collection without a page:
   a. Generate 6 UIDs (page, menu, tab, tabName, rootPage, blockGrid)
   b. Run Phase 1 (Steps 1-3) to create route + schema
   c. Run Phase 2 (Steps 4-5) to initialize flow models
   d. Generate UIDs for table block + actions column
   e. Run Phase 3 (Step 6) to create table block
   f. For each displayable field (skip belongsTo/hasMany/belongsToMany):
      - Generate 2 UIDs (column, field)
      - Map field interface to display model
      - Run Phase 4 to add column
```

### Add a block to an existing page

```
1. GET desktopRoutes:getAccessible?filterByTk=<routeId>  → get the route with tab schemaUid
2. GET flowModels:findOne?parentId=<tabSchemaUid>&subKey=grid  → find BlockGridModel
3. If no BlockGridModel exists, create one (Step 5)
4. POST flowModels:save  → create the block (Step 6) with parentId = BlockGridModel uid
```

### Delete a page

```
1. POST desktopRoutes:destroy?filterByTk=<routeId>
   (automatically cascades to delete associated flowModels and uiSchemas)
```

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Page shows "Add block" but no table | Missing BlockGridModel or TableBlockModel | Check Phase 2-3 were executed |
| Table shows but no columns | Missing TableColumnModel entries | Run Phase 4 for each field |
| Page not in menu | Route created but `listAccessible` not called | Call Step 2 |
| 404 when navigating to page | Schema node missing | Ensure Step 3 created the FlowRoute schema |
| Wrong block type | Used `"page"` instead of `"flowPage"` | Route type must be `"flowPage"` for v2 |

For the complete backend API reference with all endpoint signatures, request/response formats, and edge cases, see `references/ux-api-reference.md`. It covers every API used by the visual constructor: uiSchemas, flowModels, desktopRoutes, flowModelTemplates, collections, fields, and more.
