# NocoBase Field Types

Complete reference for all field types available when creating or modifying collection fields through the NocoBase API.

Every field requires three properties:
- **`type`** -- the database storage type
- **`interface`** -- the UI input component type
- **`uiSchema`** -- Formily schema controlling rendering (`x-component`, `x-component-props`, `enum`, `required`)

---

## Primitive Types

| Type | Interface Options | Database Column | Description |
|------|------------------|-----------------|-------------|
| `boolean` | `checkbox`, `switch` | BOOLEAN | True/false value |
| `integer` | `integer`, `number` | INTEGER | Whole number (32-bit) |
| `bigInt` | `integer`, `number` | BIGINT | Large whole number (64-bit) |
| `float` | `number` | FLOAT | Floating-point number (single precision) |
| `double` | `number` | DOUBLE | Floating-point number (double precision) |
| `decimal` | `number` | DECIMAL | Fixed-precision decimal (ideal for currency) |
| `string` | `input`, `email`, `url`, `phone`, `color` | VARCHAR(255) | Short text string |
| `text` | `textarea`, `richText`, `markdown` | TEXT | Long text content |
| `date` | `datetime`, `createdAt`, `updatedAt` | TIMESTAMP WITH TZ | Date and time with timezone |
| `dateOnly` | `date` | DATE | Date without time component |
| `time` | `time` | TIME | Time without date component |
| `uuid` | `input` | UUID | UUID v4 auto-generated identifier |
| `uid` | `input` | VARCHAR | Short unique identifier |
| `json` | `json` | JSON | Arbitrary JSON data |
| `jsonb` | `json` | JSONB | Binary JSON (PostgreSQL, faster queries) |

### Common uiSchema for Primitives

**String/Input:**
```json
{
  "title": "Name",
  "type": "string",
  "x-component": "Input",
  "required": true,
  "x-component-props": {
    "placeholder": "Enter name..."
  }
}
```

**Number/Decimal:**
```json
{
  "title": "Price",
  "type": "number",
  "x-component": "InputNumber",
  "x-component-props": {
    "precision": 2,
    "min": 0,
    "step": 0.01,
    "addonBefore": "$"
  }
}
```

**Boolean/Checkbox:**
```json
{
  "title": "Active",
  "type": "boolean",
  "x-component": "Checkbox"
}
```

**DateTime:**
```json
{
  "title": "Created",
  "type": "string",
  "x-component": "DatePicker",
  "x-component-props": {
    "showTime": true,
    "dateFormat": "YYYY-MM-DD",
    "timeFormat": "HH:mm:ss"
  }
}
```

**Textarea/RichText:**
```json
{
  "title": "Description",
  "type": "string",
  "x-component": "Input.TextArea",
  "x-component-props": {
    "rows": 4
  }
}
```

---

## NocoBase Extension Types

| Type | Interface | Description |
|------|-----------|-------------|
| `password` | `password` | Hashed password field, write-only in API responses |
| `sequence` | `sequence` | Auto-generated sequence number (e.g., `ORD-0001`) |
| `formula` | `formula` | Computed value from an expression referencing other fields |
| `radioGroup` | `radioGroup` | Single-select rendered as radio buttons |
| `sort` | `sort` | Integer field for manual record ordering |
| `virtual` | varies | Computed field not stored in the database |
| `array` | `multipleSelect`, `checkboxGroup` | Array of values stored as JSON |

### Sequence Field

Auto-increment field with a configurable pattern.

```json
{
  "name": "orderNumber",
  "type": "sequence",
  "interface": "sequence",
  "patterns": [
    { "type": "string", "options": { "value": "ORD-" } },
    { "type": "integer", "options": { "digits": 5, "start": 1, "key": 1 } }
  ],
  "uiSchema": {
    "title": "Order Number",
    "type": "string",
    "x-component": "Input",
    "x-read-pretty": true
  }
}
```

### Formula Field

Computed from other fields in the same record.

```json
{
  "name": "total",
  "type": "formula",
  "interface": "formula",
  "expression": "{{price}} * {{quantity}}",
  "dataType": "double",
  "uiSchema": {
    "title": "Total",
    "type": "number",
    "x-component": "Formula.Result",
    "x-read-pretty": true
  }
}
```

### Select/Enum Field

```json
{
  "name": "priority",
  "type": "string",
  "interface": "select",
  "uiSchema": {
    "title": "Priority",
    "type": "string",
    "x-component": "Select",
    "enum": [
      { "value": "low", "label": "Low", "color": "green" },
      { "value": "medium", "label": "Medium", "color": "orange" },
      { "value": "high", "label": "High", "color": "red" },
      { "value": "critical", "label": "Critical", "color": "magenta" }
    ]
  }
}
```

### Multi-Select/Array Field

```json
{
  "name": "tags",
  "type": "array",
  "interface": "multipleSelect",
  "uiSchema": {
    "title": "Tags",
    "type": "array",
    "x-component": "Select",
    "x-component-props": { "mode": "multiple" },
    "enum": [
      { "value": "urgent", "label": "Urgent" },
      { "value": "featured", "label": "Featured" },
      { "value": "new", "label": "New" }
    ]
  }
}
```

---

## Association Types

| Type | Interface | Cardinality | Description |
|------|-----------|-------------|-------------|
| `belongsTo` | `m2o` | Many-to-One | Child references parent (e.g., order.customer) |
| `hasOne` | `o2o` | One-to-One | Parent has one child (e.g., user.profile) |
| `hasMany` | `o2m` | One-to-Many | Parent has many children (e.g., customer.orders) |
| `belongsToMany` | `m2m` | Many-to-Many | Both sides have many (e.g., posts <-> tags) |

### Association Configuration Properties

| Property | Used By | Description |
|----------|---------|-------------|
| `target` | All | Target collection name |
| `foreignKey` | belongsTo, hasOne, hasMany | Foreign key column name |
| `sourceKey` | hasOne, hasMany | Source collection's key (usually `id`) |
| `targetKey` | belongsTo, belongsToMany | Target collection's key (usually `id`) |
| `through` | belongsToMany | Junction/pivot table name |
| `otherKey` | belongsToMany | Foreign key in junction table pointing to target |

### Association uiSchema

```json
{
  "title": "Customer",
  "x-component": "AssociationField",
  "x-component-props": {
    "fieldNames": {
      "label": "name",
      "value": "id"
    },
    "multiple": false
  }
}
```

Set `"multiple": true` for hasMany and belongsToMany interfaces.

---

## System/Auto-Generated Fields

These fields are automatically created by NocoBase for every collection:

| Field | Type | Description |
|-------|------|-------------|
| `id` | `bigInt` | Auto-increment primary key |
| `createdAt` | `date` | Record creation timestamp (auto-set) |
| `updatedAt` | `date` | Last update timestamp (auto-set) |
| `createdBy` | `belongsTo` | User who created the record (auto-set) |
| `updatedBy` | `belongsTo` | User who last updated the record (auto-set) |

These fields are present on all collections by default. They cannot be removed but can be hidden from the UI by modifying their uiSchema.
