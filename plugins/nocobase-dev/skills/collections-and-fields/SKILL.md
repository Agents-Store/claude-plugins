---
name: collections-and-fields
description: |
  Manage NocoBase collections, fields, database views, and collection categories via the API. Use when:
  - "create a NocoBase collection"
  - "add fields to a collection"
  - "list NocoBase collections"
  - "NocoBase field types"
  - "manage collection schema"
  - "NocoBase database views"
  - "collection categories"
---

# Collections and Fields

Manage the NocoBase data model through the API. Collections are the equivalent of database tables, and fields define the columns within them. This skill covers creating, reading, updating, and deleting collections and their fields, plus database views and collection categories.

> **Note:** The paths in this skill (e.g. `collections/products/fields:list`) work for the default `main` data source. For external data sources, use the data-source-scoped paths documented in the **data-sources** skill (e.g. `dataSources/<key>/collections:list` and `dataSourcesCollections/<key>.<name>/fields:list`).

## Collection Management

### List All Collections

Retrieve all collections with their field definitions.

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/collections:list?page=1&pageSize=50"
```

For non-paginated results, add `paginate=false`:

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/collections:list?paginate=false"
```

Response includes each collection's `name`, `title`, `fields`, and configuration.

### Get a Single Collection

Retrieve a specific collection by its name (the `name` field is the primary key for collections).

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/collections:get?filterByTk=orders"
```

Append related data to see the full field list:

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/collections:get?filterByTk=orders&appends=[fields]"
```

### Create a Collection

Create a new collection with inline field definitions.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections:create" \
  -d '{
    "name": "products",
    "title": "Products",
    "fields": [
      {
        "name": "name",
        "type": "string",
        "interface": "input",
        "uiSchema": {
          "title": "Product Name",
          "type": "string",
          "x-component": "Input",
          "required": true
        }
      },
      {
        "name": "price",
        "type": "decimal",
        "interface": "number",
        "uiSchema": {
          "title": "Price",
          "type": "number",
          "x-component": "InputNumber",
          "x-component-props": { "precision": 2 }
        }
      },
      {
        "name": "status",
        "type": "string",
        "interface": "select",
        "uiSchema": {
          "title": "Status",
          "type": "string",
          "x-component": "Select",
          "enum": [
            { "value": "draft", "label": "Draft" },
            { "value": "active", "label": "Active" },
            { "value": "archived", "label": "Archived" }
          ]
        }
      },
      {
        "name": "description",
        "type": "text",
        "interface": "textarea",
        "uiSchema": {
          "title": "Description",
          "type": "string",
          "x-component": "Input.TextArea"
        }
      }
    ]
  }'
```

### Update a Collection

Update collection metadata (title, sort settings, etc.).

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections:update?filterByTk=products" \
  -d '{
    "title": "Product Catalog",
    "sortable": true
  }'
```

### Destroy a Collection

Delete a collection and all its data permanently.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/collections:destroy?filterByTk=products"
```

**Warning:** This deletes the underlying database table and all records. This action is irreversible.

### Move a Collection

Reorder a collection in the list.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections:move" \
  -d '{
    "sourceId": "products",
    "targetId": "orders",
    "method": "insertAfter"
  }'
```

The `method` field accepts `insertAfter` or `insertBefore`.

### Set Fields on a Collection

Replace or set the complete field configuration for a collection in one call.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections:setFields?filterByTk=products" \
  -d '{
    "fields": [
      { "name": "name", "type": "string", "interface": "input" },
      { "name": "sku", "type": "string", "interface": "input" },
      { "name": "price", "type": "decimal", "interface": "number" }
    ]
  }'
```

## Field Management

Fields are an association resource of collections. Access them through the nested URL pattern.

### List Fields

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/collections/products/fields:list"
```

### Get a Single Field

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/collections/products/fields:get?filterByTk=name"
```

### Create a Field

Add a new field to an existing collection. Every field requires `name`, `type`, and `interface`. The `uiSchema` object controls how the field renders in the NocoBase UI.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections/products/fields:create" \
  -d '{
    "name": "category",
    "type": "string",
    "interface": "select",
    "uiSchema": {
      "title": "Category",
      "type": "string",
      "x-component": "Select",
      "enum": [
        { "value": "electronics", "label": "Electronics" },
        { "value": "clothing", "label": "Clothing" },
        { "value": "food", "label": "Food" }
      ]
    }
  }'
```

### Update a Field

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections/products/fields:update?filterByTk=category" \
  -d '{
    "uiSchema": {
      "title": "Product Category",
      "type": "string",
      "x-component": "Select",
      "enum": [
        { "value": "electronics", "label": "Electronics" },
        { "value": "clothing", "label": "Clothing" },
        { "value": "food", "label": "Food & Beverage" },
        { "value": "other", "label": "Other" }
      ]
    }
  }'
```

### Destroy a Field

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/collections/products/fields:destroy?filterByTk=category"
```

### Move a Field

Reorder a field within the collection.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections/products/fields:move" \
  -d '{
    "sourceId": "category",
    "targetId": "name",
    "method": "insertAfter"
  }'
```

## Field Structure

Every field has three key parts:

1. **`type`** -- the database column type (e.g., `string`, `integer`, `boolean`, `belongsTo`).
2. **`interface`** -- the UI input type (e.g., `input`, `select`, `number`, `datetime`).
3. **`uiSchema`** -- the rendering configuration using Formily schema properties (`x-component`, `x-component-props`, `enum`, `required`).

See `references/field-types.md` for the complete list of all field types, interface options, and common uiSchema properties.

## Creating Association Fields

Association fields define relationships between collections.

### belongsTo (Many-to-One)

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections/orders/fields:create" \
  -d '{
    "name": "customer",
    "type": "belongsTo",
    "interface": "m2o",
    "target": "customers",
    "foreignKey": "customerId",
    "targetKey": "id",
    "uiSchema": {
      "title": "Customer",
      "x-component": "AssociationField",
      "x-component-props": { "fieldNames": { "label": "name", "value": "id" } }
    }
  }'
```

### hasMany (One-to-Many)

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections/customers/fields:create" \
  -d '{
    "name": "orders",
    "type": "hasMany",
    "interface": "o2m",
    "target": "orders",
    "foreignKey": "customerId",
    "sourceKey": "id",
    "uiSchema": {
      "title": "Orders",
      "x-component": "AssociationField",
      "x-component-props": { "fieldNames": { "label": "title", "value": "id" } }
    }
  }'
```

### belongsToMany (Many-to-Many)

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections/posts/fields:create" \
  -d '{
    "name": "tags",
    "type": "belongsToMany",
    "interface": "m2m",
    "target": "tags",
    "through": "postsTags",
    "foreignKey": "postId",
    "otherKey": "tagId",
    "sourceKey": "id",
    "targetKey": "id",
    "uiSchema": {
      "title": "Tags",
      "x-component": "AssociationField",
      "x-component-props": { "fieldNames": { "label": "name", "value": "id" } }
    }
  }'
```

## Database Views

NocoBase can connect to existing database views (read-only).

### List Database Views

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/dbViews:list"
```

### Get a Database View

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/dbViews:get?filterByTk=v_order_summary"
```

### Query a Database View

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/dbViews:query?filterByTk=v_order_summary"
```

## Collection Categories

Organize collections into folders/groups. See `references/collection-categories.md` for the complete endpoint reference.

```bash
# List all categories
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/collectionCategories:list"

# Create a category
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collectionCategories:create" \
  -d '{"name": "E-Commerce", "color": "#1890ff"}'
```
