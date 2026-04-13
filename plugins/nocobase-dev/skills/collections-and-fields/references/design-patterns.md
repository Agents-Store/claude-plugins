# Collection Design Patterns & Advanced Fields

## Collection Design Process

### Step 1: Identify Entities

List all data entities the application needs:
- **Core entities:** Main business objects (Contacts, Orders, Products)
- **Supporting entities:** Reference data (Categories, Statuses, Tags)
- **Junction entities:** Many-to-many bridges (OrderItems, UserRoles)

### Step 2: Define Fields per Entity

For each entity, list fields with types:
```
contacts:
  - name: string (required)
  - email: email (unique)
  - phone: phone
  - status: singleSelect (Lead, Active, Inactive)
  - avatar: attachment
  - notes: richText
```

### Step 3: Map Relations

Draw entity relationships:
```
companies ──< contacts (one company has many contacts)
contacts ──< deals    (one contact has many deals)
deals >──< products   (many-to-many via deal_products)
```

### Step 4: Create in Dependency Order

```
1. Independent collections (no foreign keys): companies, products, categories
2. Dependent collections: contacts (needs companies), deals (needs contacts)
3. Junction collections: deal_products (needs deals + products)
4. Set up relation fields between collections
5. Add computed/formula fields last
```

## Collection Architecture Patterns

### Master-Detail

```
orders (master)
  ├── order_items (detail, hasMany)
  └── order_notes (detail, hasMany)
```

```bash
# Create master
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections:create" \
  -d '{"name": "orders", "title": "Orders", "fields": [...]}'

# Create detail with foreign key
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections:create" \
  -d '{
    "name": "order_items",
    "title": "Order Items",
    "fields": [
      {"name": "order", "type": "belongsTo", "target": "orders", "foreignKey": "orderId"},
      {"name": "product", "type": "string", "interface": "input"},
      {"name": "quantity", "type": "integer", "interface": "number"},
      {"name": "price", "type": "decimal", "interface": "number"}
    ]
  }'
```

### Self-Referencing (Tree)

```
categories
  └── parent (belongsTo → categories, self-reference)
  └── children (hasMany → categories)
```

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections:create" \
  -d '{
    "name": "categories",
    "title": "Categories",
    "tree": "adjacencyList",
    "fields": [
      {"name": "title", "type": "string", "interface": "input"},
      {"name": "parent", "type": "belongsTo", "target": "categories", "foreignKey": "parentId"},
      {"name": "children", "type": "hasMany", "target": "categories", "foreignKey": "parentId"}
    ]
  }'
```

Query tree structure with `tree=true`:

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/categories:list?tree=true"
```

### Soft Delete

Add a `deletedAt` field instead of permanently deleting records:

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections/orders/fields:create" \
  -d '{
    "name": "deletedAt",
    "type": "date",
    "interface": "datetime",
    "uiSchema": {"title": "Deleted At", "x-component": "DatePicker"}
  }'
```

Filter active records: `filter={"deletedAt":{"$empty":true}}`

### Polymorphic

```
comments
  - commentableType: string (posts, products, orders)
  - commentableId: bigInt
  → Can belong to different collection types
```

Useful when multiple collections need the same child entity.

## Collection Inheritance

NocoBase supports collection inheritance — child collections share base fields and add their own:

```
base: people
  - name, email, phone

child: employees (inherits people)
  - department, salary, hireDate

child: customers (inherits people)
  - company, tier, lastPurchase
```

Create an inheriting collection:

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections:create" \
  -d '{
    "name": "employees",
    "title": "Employees",
    "inherits": ["people"],
    "fields": [
      {"name": "department", "type": "string", "interface": "input"},
      {"name": "salary", "type": "decimal", "interface": "number"},
      {"name": "hireDate", "type": "date", "interface": "datetime"}
    ]
  }'
```

## Advanced Field Types

Beyond the basic types in `field-types.md`, NocoBase supports:

| Type | Description | Use Case |
|------|-------------|----------|
| `formula` | Calculated field | `{{price}} * {{quantity}}` |
| `sequence` | Auto-incrementing | `ORD-{YYYYMMDD}-{0000}` |
| `snapshot` | Point-in-time copy | Order snapshot of product price |
| `nanoid` | Short unique ID | Public-facing identifiers |
| `uuid` | Universal unique ID | API identifiers |
| `sort` | Drag-and-drop ordering | List ordering |

### Formula Field

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections/order_items/fields:create" \
  -d '{
    "name": "lineTotal",
    "type": "formula",
    "interface": "formula",
    "expression": "{{price}} * {{quantity}} * (1 - {{discount}} / 100)",
    "uiSchema": {"title": "Line Total", "x-component": "Formula.Result"}
  }'
```

### Sequence Field

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections/orders/fields:create" \
  -d '{
    "name": "orderNumber",
    "type": "sequence",
    "interface": "sequence",
    "patterns": [
      {"type": "string", "options": {"value": "ORD-"}},
      {"type": "date", "options": {"format": "YYYYMMDD"}},
      {"type": "string", "options": {"value": "-"}},
      {"type": "integer", "options": {"digits": 4, "start": 1, "key": "order_seq"}}
    ],
    "uiSchema": {"title": "Order Number", "x-component": "Input", "x-read-pretty": true}
  }'
```

## Field Validation

| Validation | Description | Example |
|-----------|-------------|---------|
| `required` | Must have value | Name field |
| `unique` | No duplicates | Email, SKU |
| `min` / `max` | Number range | Age: 0-150 |
| `minLength` / `maxLength` | Text length | Title: 1-200 |
| `pattern` | Regex match | SKU format |
| `enum` | From predefined list | Status values |

Set validation in the `uiSchema`:

```json
{
  "uiSchema": {
    "title": "Email",
    "x-component": "Input",
    "required": true,
    "x-validator": [
      {"required": true, "message": "Email is required"},
      {"format": "email", "message": "Must be a valid email"}
    ]
  }
}
```
