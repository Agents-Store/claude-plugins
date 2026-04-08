# Route Operations Reference

Detailed endpoint reference for desktop and mobile route management.

## Desktop Routes — Endpoint Summary

| Method | Endpoint | Description | ACL |
|--------|----------|-------------|-----|
| GET | `/api/desktopRoutes:listAccessible` | List all accessible routes (tree) | `loggedIn` |
| GET | `/api/desktopRoutes:getAccessible?filterByTk={id}` | Get single route with children | `loggedIn` |
| POST | `/api/desktopRoutes:create` | Create a new route | `ui.desktopRoutes` |
| POST | `/api/desktopRoutes:update?filterByTk={id}` | Update route properties | `ui.desktopRoutes` |
| POST | `/api/desktopRoutes:move` | Reposition route in tree | `ui.desktopRoutes` |
| POST | `/api/desktopRoutes:destroy?filterByTk={id}` | Delete route (cascading) | `ui.desktopRoutes` |
| POST | `/api/roles/{role}/desktopRoutes:set` | Set role route access | `pm.desktopRoutes` |

## Mobile Routes — Endpoint Summary

| Method | Endpoint | Description | ACL |
|--------|----------|-------------|-----|
| GET | `/api/mobileRoutes:listAccessible` | List all accessible mobile routes (tree) | `loggedIn` |
| POST | `/api/mobileRoutes:create` | Create a new mobile route | `ui.mobile` |
| POST | `/api/mobileRoutes:update?filterByTk={id}` | Update mobile route | `ui.mobile` |
| POST | `/api/mobileRoutes:move` | Reposition mobile route | `ui.mobile` |
| POST | `/api/mobileRoutes:destroy?filterByTk={id}` | Delete mobile route | `ui.mobile` |

## Desktop Route Fields

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `id` | snowflakeId | No | Primary key (auto-generated) |
| `parentId` | bigInt | Yes | Parent route ID (null = root) |
| `title` | string | Yes | Menu/page display title |
| `tooltip` | string | Yes | Tooltip text |
| `icon` | string | Yes | Ant Design icon name |
| `schemaUid` | string | Yes | Page body UI schema `x-uid` |
| `menuSchemaUid` | string | Yes | Menu item UI schema `x-uid` |
| `tabSchemaName` | string | Yes | Tab schema name (tabbed pages) |
| `type` | string | Yes | `page`, `link`, `group`, `tabs` |
| `options` | json | Yes | Additional route options |
| `sort` | sort | No | Sort order (scoped by parentId) |
| `hideInMenu` | boolean | No | Hide in menu navigation |
| `enableTabs` | boolean | No | Enable tab sub-pages |
| `enableHeader` | boolean | No | Show page header |
| `displayTitle` | boolean | No | Display title in header |
| `hidden` | boolean | No | Completely hidden (tab children) |

## Mobile Route Fields

Same as desktop minus `enableHeader`, `displayTitle`, and `menuSchemaUid`.

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `id` | snowflakeId | No | Primary key |
| `parentId` | bigInt | Yes | Parent route ID |
| `title` | string | Yes | Display title |
| `icon` | string | Yes | Icon identifier |
| `schemaUid` | string | Yes | UI schema `x-uid` |
| `type` | string | Yes | Route type |
| `options` | json | Yes | Additional options |
| `sort` | sort | No | Sort order (scoped by parentId) |
| `hideInMenu` | boolean | No | Hide from mobile menu |
| `enableTabs` | boolean | No | Enable tab sub-pages |
| `hidden` | boolean | No | Completely hidden |

## Move Operation Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sourceId` | number | Yes | ID of route being moved |
| `targetId` | number | Yes | ID of reference route |
| `sortField` | string | No | Sort field (default: `sort`) |
| `targetScope` | object | No | Scope for sort, e.g. `{ "parentId": 1 }` |
| `method` | string | No | `insertAfter`, `insertBefore`, or `prepend` |

## Side Effects

| Operation | Side Effect |
|-----------|-------------|
| `create` (desktop) | Roles with `allowNewMenu=true` auto-get access |
| `update` (enableTabs change) | All child routes' `hidden` field is updated |
| `destroy` | Cascades to child routes; destroys associated `flowModels` |
| `set` (role routes) | Auto-includes child tab routes for any parent in the list |

## Example: Create Tabbed Page

```bash
# 1. Create parent page with tabs enabled
curl -X POST "${NOCOBASE_URL}/api/desktopRoutes:create" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Customer Management",
    "icon": "TeamOutlined",
    "type": "page",
    "enableTabs": true,
    "enableHeader": true,
    "displayTitle": true
  }'
# Response: { "data": { "id": 10, ... } }

# 2. Create first tab
curl -X POST "${NOCOBASE_URL}/api/desktopRoutes:create" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Active Customers",
    "type": "tabs",
    "parentId": 10,
    "schemaUid": "tab-active-schema-uid"
  }'

# 3. Create second tab
curl -X POST "${NOCOBASE_URL}/api/desktopRoutes:create" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Archived Customers",
    "type": "tabs",
    "parentId": 10,
    "schemaUid": "tab-archived-schema-uid"
  }'
```

## Example: Restrict Routes for a Role

```bash
# 1. List all routes
curl -X GET "${NOCOBASE_URL}/api/desktopRoutes:listAccessible" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "X-Role: admin"
# Pick route IDs: [1, 3, 5]

# 2. Assign routes to "viewer" role
curl -X POST "${NOCOBASE_URL}/api/roles/viewer/desktopRoutes:set" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '[1, 3, 5]'
```
