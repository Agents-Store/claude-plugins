# NocoBase Filter Operators

Complete reference for all filter operators available in the NocoBase API `filter` query parameter.

Filters use a JSON object format: `{"fieldName": {"$operator": "value"}}`. Nest operators inside field names, or use `$and`/`$or` at the top level for logical combinations.

---

## General Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `$eq` | Equal to | `{"status": {"$eq": "active"}}` |
| `$ne` | Not equal to | `{"status": {"$ne": "deleted"}}` |
| `$is` | Is (identical to $eq, used for null checks) | `{"deletedAt": {"$is": null}}` |
| `$not` | Is not (identical to $ne, used for null checks) | `{"deletedAt": {"$not": null}}` |
| `$in` | Value is in the given array | `{"status": {"$in": ["active", "pending"]}}` |
| `$notIn` | Value is not in the given array | `{"role": {"$notIn": ["banned", "suspended"]}}` |
| `$empty` | Field is empty (null, empty string, or empty array) | `{"description": {"$empty": true}}` |
| `$notEmpty` | Field is not empty | `{"email": {"$notEmpty": true}}` |

## Logical Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `$and` | All conditions must match | `{"$and": [{"status": {"$eq": "active"}}, {"age": {"$gte": 18}}]}` |
| `$or` | At least one condition must match | `{"$or": [{"role": {"$eq": "admin"}}, {"role": {"$eq": "editor"}}]}` |

Logical operators are placed at the top level of the filter object. They accept an array of condition objects. Nesting is supported: you can place `$or` inside `$and` and vice versa.

```json
{
  "$and": [
    { "status": { "$eq": "active" } },
    {
      "$or": [
        { "role": { "$eq": "admin" } },
        { "role": { "$eq": "editor" } }
      ]
    }
  ]
}
```

## Boolean Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `$isTruly` | Value is truthy (true, 1, "1", "true") | `{"isVerified": {"$isTruly": true}}` |
| `$isFalsy` | Value is falsy (false, 0, "0", "false", null, "") | `{"isVerified": {"$isFalsy": true}}` |

## Numeric Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `$gt` | Greater than | `{"price": {"$gt": 100}}` |
| `$gte` | Greater than or equal to | `{"quantity": {"$gte": 1}}` |
| `$lt` | Less than | `{"age": {"$lt": 65}}` |
| `$lte` | Less than or equal to | `{"priority": {"$lte": 3}}` |
| `$between` | Value is between two numbers (inclusive) | `{"price": {"$between": [10, 50]}}` |

## String Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `$includes` | String contains substring (case-sensitive) | `{"title": {"$includes": "NocoBase"}}` |
| `$notIncludes` | String does not contain substring | `{"title": {"$notIncludes": "draft"}}` |
| `$startsWith` | String starts with prefix | `{"code": {"$startsWith": "PRD-"}}` |
| `$notStartsWith` | String does not start with prefix | `{"code": {"$notStartsWith": "TEST-"}}` |
| `$endsWith` | String ends with suffix | `{"email": {"$endsWith": "@company.com"}}` |
| `$notEndsWith` | String does not end with suffix | `{"filename": {"$notEndsWith": ".tmp"}}` |
| `$like` | SQL LIKE pattern match (case-sensitive) | `{"name": {"$like": "%smith%"}}` |
| `$notLike` | SQL NOT LIKE pattern match | `{"name": {"$notLike": "%test%"}}` |
| `$iLike` | Case-insensitive LIKE pattern match | `{"name": {"$iLike": "%Smith%"}}` |
| `$notILike` | Case-insensitive NOT LIKE | `{"name": {"$notILike": "%test%"}}` |
| `$regexp` | Regular expression match | `{"code": {"$regexp": "^[A-Z]{3}-\\d+"}}` |

## Date Operators

Date values should be in ISO 8601 format (`YYYY-MM-DD` or `YYYY-MM-DDTHH:mm:ss`).

| Operator | Description | Example |
|----------|-------------|---------|
| `$dateOn` | Date is on the specified day | `{"createdAt": {"$dateOn": "2025-01-15"}}` |
| `$dateNotOn` | Date is not on the specified day | `{"createdAt": {"$dateNotOn": "2025-01-15"}}` |
| `$dateBefore` | Date is before the specified date | `{"deadline": {"$dateBefore": "2025-06-01"}}` |
| `$dateAfter` | Date is after the specified date | `{"startDate": {"$dateAfter": "2025-01-01"}}` |
| `$dateNotBefore` | Date is not before (on or after) | `{"createdAt": {"$dateNotBefore": "2025-01-01"}}` |
| `$dateNotAfter` | Date is not after (on or before) | `{"expiresAt": {"$dateNotAfter": "2025-12-31"}}` |
| `$dateBetween` | Date is between two dates (inclusive) | `{"createdAt": {"$dateBetween": ["2025-01-01", "2025-03-31"]}}` |

### Relative Date Operators

Relative date operators calculate dates relative to the current moment. They accept a numeric value and a unit.

| Operator | Description | Example |
|----------|-------------|---------|
| `$dateRelativeBefore` | Date is within N units before now | `{"createdAt": {"$dateRelativeBefore": {"value": 7, "unit": "day"}}}` |
| `$dateRelativeAfter` | Date is within N units after now | `{"deadline": {"$dateRelativeAfter": {"value": 30, "unit": "day"}}}` |
| `$dateRelativeBetween` | Date is between two relative offsets | `{"updatedAt": {"$dateRelativeBetween": {"from": {"value": -7, "unit": "day"}, "to": {"value": 0, "unit": "day"}}}}` |

Supported units: `second`, `minute`, `hour`, `day`, `week`, `month`, `quarter`, `year`.

## Array Operators

For fields that store arrays of values (multi-select, JSON arrays).

| Operator | Description | Example |
|----------|-------------|---------|
| `$match` | Array contains all specified values | `{"tags": {"$match": ["urgent", "bug"]}}` |
| `$anyOf` | Array contains at least one of the specified values | `{"tags": {"$anyOf": ["feature", "enhancement"]}}` |
| `$noneOf` | Array contains none of the specified values | `{"tags": {"$noneOf": ["spam", "duplicate"]}}` |
| `$arrayEmpty` | Array field is empty | `{"attachments": {"$arrayEmpty": true}}` |
| `$arrayNotEmpty` | Array field is not empty | `{"tags": {"$arrayNotEmpty": true}}` |

## Association/Relation Operators

For filtering based on the existence of related records.

| Operator | Description | Example |
|----------|-------------|---------|
| `$exists` | Related record(s) exist matching the given filter | `{"comments": {"$exists": {"status": {"$eq": "approved"}}}}` |
| `$notExists` | No related records match the given filter | `{"orders": {"$notExists": {"status": {"$eq": "failed"}}}}` |

Association operators accept a nested filter object that applies to the related collection:

```json
{
  "author": {
    "$exists": {
      "role": { "$eq": "admin" }
    }
  }
}
```

This filters records where the associated `author` has role "admin".

## Combining Operators on the Same Field

Apply multiple operators to a single field by listing them in the same object:

```json
{
  "price": {
    "$gte": 10,
    "$lte": 100
  }
}
```

This is equivalent to: `price >= 10 AND price <= 100`.

## Full Example

A complex filter combining multiple operator types:

```json
{
  "$and": [
    { "status": { "$in": ["active", "pending"] } },
    { "createdAt": { "$dateAfter": "2025-01-01" } },
    { "title": { "$notEmpty": true } },
    { "price": { "$between": [10, 500] } },
    {
      "$or": [
        { "category": { "$eq": "electronics" } },
        { "tags": { "$anyOf": ["featured", "sale"] } }
      ]
    },
    { "author": { "$exists": { "isVerified": { "$isTruly": true } } } }
  ]
}
```

URL-encode this JSON and pass it as the `filter` query parameter:

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/products:list?filter=<url-encoded-json>"
```
