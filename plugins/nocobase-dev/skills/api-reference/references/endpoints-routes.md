# NocoBase API — Desktop Routes, Mobile Routes & Role Route Access

All endpoints use base URL `${NOCOBASE_URL}/api/` with header `Authorization: Bearer ${NOCOBASE_API_KEY}`.

---

## Desktop Routes (7 endpoints)

| Method | Endpoint | Description | ACL |
|--------|----------|-------------|-----|
| GET | `/api/desktopRoutes:listAccessible` | List all accessible desktop routes (tree) | `loggedIn` |
| GET | `/api/desktopRoutes:getAccessible?filterByTk={id}` | Get single desktop route with children | `loggedIn` |
| POST | `/api/desktopRoutes:create` | Create a new desktop route | `ui.desktopRoutes` |
| POST | `/api/desktopRoutes:update?filterByTk={id}` | Update a desktop route | `ui.desktopRoutes` |
| POST | `/api/desktopRoutes:move` | Reposition route in tree | `ui.desktopRoutes` |
| POST | `/api/desktopRoutes:destroy?filterByTk={id}` | Delete route and descendants | `ui.desktopRoutes` |
| POST | `/api/roles/{role}/desktopRoutes:set` | Set role route access | `pm.desktopRoutes` |

### List Accessible

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "X-Role: admin" \
  "${NOCOBASE_URL}/api/desktopRoutes:listAccessible"
```

Returns tree structure with nested `children`.

### Create Desktop Route

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/desktopRoutes:create" \
  -d '{
    "title": "New Page",
    "icon": "FileOutlined",
    "type": "page",
    "schemaUid": "schema-uid",
    "parentId": null,
    "enableHeader": true,
    "displayTitle": true
  }'
```

**Body fields:** `title`, `icon`, `type` (`page`/`link`/`group`/`tabs`), `schemaUid`, `menuSchemaUid`, `tabSchemaName`, `parentId`, `options`, `hideInMenu`, `enableTabs`, `enableHeader`, `displayTitle`

### Update Desktop Route

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/desktopRoutes:update?filterByTk=5" \
  -d '{ "title": "Renamed", "enableTabs": true }'
```

### Move Desktop Route

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/desktopRoutes:move" \
  -d '{ "sourceId": 5, "targetId": 3, "method": "insertAfter", "targetScope": { "parentId": 1 } }'
```

**Body fields:** `sourceId`, `targetId`, `sortField` (default: `sort`), `targetScope`, `method` (`insertAfter`/`insertBefore`/`prepend`)

### Destroy Desktop Route

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/desktopRoutes:destroy?filterByTk=5"
```

Cascades to child routes. Destroys associated `flowModels`.

### Set Role Desktop Routes

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/roles/editor/desktopRoutes:set" \
  -d '[1, 3, 5, 7]'
```

Array of route IDs. Auto-includes child tab routes.

---

## Mobile Routes (5 endpoints)

| Method | Endpoint | Description | ACL |
|--------|----------|-------------|-----|
| GET | `/api/mobileRoutes:listAccessible` | List all accessible mobile routes (tree) | `loggedIn` |
| POST | `/api/mobileRoutes:create` | Create mobile route | `ui.mobile` |
| POST | `/api/mobileRoutes:update?filterByTk={id}` | Update mobile route | `ui.mobile` |
| POST | `/api/mobileRoutes:move` | Reposition mobile route | `ui.mobile` |
| POST | `/api/mobileRoutes:destroy?filterByTk={id}` | Delete mobile route | `ui.mobile` |

### List Accessible

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/mobileRoutes:listAccessible"
```

### Create Mobile Route

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/mobileRoutes:create" \
  -d '{ "title": "Mobile Page", "icon": "HomeOutlined", "type": "page", "schemaUid": "uid" }'
```

### Update, Move, Destroy

Same parameter patterns as desktop routes. Use `mobileRoutes` resource name instead of `desktopRoutes`.
