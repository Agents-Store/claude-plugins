---
name: routes-and-menus
description: |
  Desktop and mobile page routing, menu structure, tabs, and role-based route access. Use when:
  - "create a NocoBase page"
  - "add a menu item"
  - "configure desktop routes"
  - "set up mobile navigation"
  - "manage page tabs"
  - "role desktop route access"
  - "reorder menu items"
  - "hide menu entries"
  - "NocoBase page structure"
---

# Routes and Menus

Manage the page/menu structure of NocoBase applications across MCP, CLI, and HTTP. Routes define the navigation tree — pages, menu groups, links, and tabbed layouts. Each route can point to a UI schema (via `schemaUid`) that holds the page content.

## MCP tools

| Task | MCP tool | Notes |
|------|----------|-------|
| Create a menu entry (group or item) | `flow_surfaces_create_menu` | For v2 — pick over HTTP `desktopRoutes:create` when creating the navigation node |
| Update a menu (rename, re-icon) | `flow_surfaces_update_menu` | |
| Create a Modern page | `flow_surfaces_create_page` | Shortcut for a blank page + route; for a full page with blocks, use `flow_surfaces_apply_blueprint` in `ux-constructor` |
| Delete a page | `flow_surfaces_destroy_page` | Cascades to flow models and routes |
| Add a tab to a page | `flow_surfaces_add_tab` | |
| Rename / reorder / remove tab | `flow_surfaces_{update,move,remove}_tab` | |
| Add tab inside a popup | `flow_surfaces_add_popup_tab` | |
| Update / reorder / remove popup tab | `flow_surfaces_{update,move,remove}_popup_tab` | |
| List routes for current user | `desktop_routes_list_accessible` | Respects role ACL |

For role-based route access, see `auth-and-users` — `roles_desktop_routes_{list,add,remove,set}` tools.

**When to pick MCP vs HTTP:** If you are creating a NEW page with content, prefer `flow_surfaces_apply_blueprint` (from `ux-constructor`) — it creates the route, menu, schema, and blocks in one call. Drop to `flow_surfaces_create_page` / `flow_surfaces_create_menu` only for bare-bones route/menu work. Fall back to `desktopRoutes:create` via HTTP only for legacy v1 pages (`type: "page"`, not `"flowPage"`).

## Authentication (HTTP path)

All HTTP requests require the API key header:

```
Authorization: Bearer ${NOCOBASE_API_KEY}
```

Base URL for all endpoints: `${NOCOBASE_URL}/api/`

All requests require the API key header:

```
Authorization: Bearer ${NOCOBASE_API_KEY}
```

Base URL for all endpoints: `${NOCOBASE_URL}/api/`

## Desktop Routes

**Resource name:** `desktopRoutes`

Desktop routes define the main application's page and menu structure. They are stored as an adjacency-list tree with `parentId` linking children to parents.

### Route Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | snowflakeId | Primary key (auto-generated) |
| `parentId` | bigInt | Parent route ID (null for root) |
| `title` | string | Menu/page display title |
| `tooltip` | string | Tooltip text |
| `icon` | string | Icon identifier (e.g. `DashboardOutlined`, `FileOutlined`) |
| `schemaUid` | string | Associated UI schema `x-uid` for the page body |
| `menuSchemaUid` | string | Associated UI schema `x-uid` for the menu item |
| `tabSchemaName` | string | Tab schema name (for tabbed pages) |
| `type` | string | Route type: `page`, `link`, `group`, `tabs` |
| `options` | json | Additional route options |
| `sort` | sort | Sort order (scoped by `parentId`) |
| `hideInMenu` | boolean | Whether to hide in menu navigation |
| `enableTabs` | boolean | Whether to enable tab sub-pages |
| `enableHeader` | boolean | Whether to show page header |
| `displayTitle` | boolean | Whether to display title in header |
| `hidden` | boolean | Whether completely hidden (used for tab children) |

### Route Types

- **`page`** — Classic page (v1) with a UI schema body
- **`flowPage`** — Modern page (v2) using the Flow Models block engine. **Use this for all new pages.** See the **ux-constructor** skill for the verified creation workflow.
- **`link`** — External URL link in the menu
- **`group`** — Menu group/folder containing child routes
- **`tabs`** — Tabbed page with tab children

### List Accessible Desktop Routes

Lists all routes accessible to the current user based on their roles. Returns a tree structure with nested `children`.

```bash
curl -X GET "${NOCOBASE_URL}/api/desktopRoutes:listAccessible" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "X-Role: admin"
```

Response is a tree of route objects:

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

### Get Accessible Desktop Route

```bash
curl -X GET "${NOCOBASE_URL}/api/desktopRoutes:getAccessible?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "X-Role: admin"
```

Returns a single route object with children.

### Create Desktop Route

```bash
curl -X POST "${NOCOBASE_URL}/api/desktopRoutes:create" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
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

**Side effect:** Roles with `allowNewMenu=true` (default: `admin`, `member`) automatically get access to the new route.

**ACL:** Requires `ui.desktopRoutes` snippet permission.

### Update Desktop Route

```bash
curl -X POST "${NOCOBASE_URL}/api/desktopRoutes:update?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Renamed Page",
    "icon": "EditOutlined",
    "enableTabs": true
  }'
```

**Side effect:** If `enableTabs` changes, all child routes' `hidden` field is updated accordingly.

**ACL:** Requires `ui.desktopRoutes` snippet permission.

### Move Desktop Route

Repositions a route within the tree for drag-and-drop reordering.

```bash
curl -X POST "${NOCOBASE_URL}/api/desktopRoutes:move" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "sourceId": 5,
    "targetId": 3,
    "sortField": "sort",
    "targetScope": { "parentId": 1 },
    "method": "insertAfter"
  }'
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `sourceId` | number | ID of the route being moved |
| `targetId` | number | ID of the reference route |
| `sortField` | string | Field to use for sorting (default: `sort`) |
| `targetScope` | object | Scope for sort (e.g. `{ "parentId": 1 }`) |
| `method` | string | `insertAfter`, `insertBefore`, or `prepend` |

### Destroy Desktop Route

```bash
curl -X POST "${NOCOBASE_URL}/api/desktopRoutes:destroy?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

**Side effect:** Also destroys the associated `flowModels` record (if exists) and cascades to child routes.

### Set Role Desktop Routes

Configures which desktop routes are accessible for a specific role.

```bash
curl -X POST "${NOCOBASE_URL}/api/roles/editor/desktopRoutes:set" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '[1, 3, 5, 7]'
```

Pass an array of route IDs. Automatically includes child tab routes for any parent route in the list.

**ACL:** Requires `pm.desktopRoutes` snippet permission.

## Mobile Routes

**Resource name:** `mobileRoutes`

Mobile routes follow the same pattern as desktop routes but for the mobile interface. The field structure is similar, minus `enableHeader` and `displayTitle`.

### List Accessible Mobile Routes

```bash
curl -X GET "${NOCOBASE_URL}/api/mobileRoutes:listAccessible" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### Create Mobile Route

```bash
curl -X POST "${NOCOBASE_URL}/api/mobileRoutes:create" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Mobile Page",
    "icon": "HomeOutlined",
    "type": "page",
    "schemaUid": "mobile-schema-uid"
  }'
```

**ACL:** Requires `ui.mobile` snippet permission.

### Update Mobile Route

```bash
curl -X POST "${NOCOBASE_URL}/api/mobileRoutes:update?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Mobile Page",
    "enableTabs": true
  }'
```

### Move Mobile Route

```bash
curl -X POST "${NOCOBASE_URL}/api/mobileRoutes:move" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "sourceId": 10,
    "targetId": 8,
    "method": "insertAfter"
  }'
```

### Destroy Mobile Route

```bash
curl -X POST "${NOCOBASE_URL}/api/mobileRoutes:destroy?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

## Common Workflows

### Create a Page with Tabs

```
1. POST desktopRoutes:create → create the parent page with enableTabs=true
2. POST desktopRoutes:create → create child routes with parentId set and type="tabs"
3. Each tab child has its own schemaUid pointing to the tab content schema
```

### Create a Menu Group with Children

```
1. POST desktopRoutes:create → create a route with type="group"
2. POST desktopRoutes:create → create child pages with parentId pointing to the group
```

### Restrict Routes by Role

```
1. GET desktopRoutes:listAccessible → get all route IDs
2. POST roles/<role>/desktopRoutes:set → pass only the allowed route IDs
```

For detailed endpoint reference with full response formats, see `references/route-operations.md`.

## See also

- `ux-constructor` — primary UI authoring skill (Modern v2 via `flow_surfaces_*`); whole-page blueprint creates route+menu+blocks in one call
- `auth-and-users` — role-based route access (`roles_desktop_routes_{add,remove,set}`)
- `mcp-patterns` — transport conventions
- `ui-builder-index` — router when unsure which UI authoring skill to use
