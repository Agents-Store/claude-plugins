# Scenario 5 — MCP-First Page Authoring

Build a complete Customers page with a table block and a filter-form block in a single `flow_surfaces_apply_blueprint` call. This is the modern NocoBase UI authoring path — declarative, idempotent, MCP-first.

## Prerequisites

- `nc-mcp` connected in this session
- `customers` collection exists with fields `name`, `email`, `status`, `createdAt` (or adjust the blueprint below)
- Role has `create` permission on `desktopRoutes`, `flowModels`, and `customers`

## Step 1 — Bulk-load MCP schemas

```
ToolSearch(query: "nc-mcp", max_results: 30)
```

Loads all ~146 `*` tool schemas in one call.

## Step 2 — Introspect the collection

```
collections_list_meta()
```

Confirm `customers` exists and its field list matches. You need the exact field names for the blueprint's `fields[]` arrays.

## Step 3 — Apply the blueprint

```
flow_surfaces_apply_blueprint({
  page: {
    pageTitle: "Customers",
    menuGroupTitle: "CRM"
  },
  navigation: {
    group: { title: "CRM", icon: "TeamOutlined" },
    item: { title: "Customers", icon: "UserOutlined" }
  },
  tabs: [{
    title: "All",
    layout: { cols: 24 },
    blocks: [
      {
        use: "filterForm",
        resource: "customers",
        fields: ["status", "name"],
        fieldsLayout: { cols: 12 },
        actions: ["submit", "reset"]
      },
      {
        use: "table",
        resource: "customers",
        fields: ["name", "email", "status", "createdAt"],
        recordActions: ["edit", "delete"]
      }
    ]
  }]
})
```

Returns:

```json
{
  "data": {
    "page": { "pageSchemaUid": "<uid>", "pageTitle": "Customers" },
    "navigation": { "group": { "routeId": "<id>" }, "item": { "routeId": "<id>" } },
    "desktopRoute": { "id": "<id>" }
  }
}
```

## Step 4 — Verify

```
# Read the page back
flow_surfaces_get({ target: { uid: "<pageSchemaUid from step 3>" } })
```

Confirm two blocks exist (one `filterForm`, one `table`) with the expected `fields[]`.

Or navigate to `${NOCOBASE_URL}/admin/<pageSchemaUid>` in a browser.

## Step 5 — Iterate

If a block needs changes (e.g., adding a column):

```
flow_surfaces_add_field({
  target: { uid: "<tableBlockUid>" },
  spec: { fieldName: "priority", renderer: "tag" }
})
```

Or for larger changes, re-apply the blueprint with the updated shape — it's idempotent against the same `pageSchemaUid`.

## Contrast with HTTP fallback

The same page via HTTP requires the phase-by-phase verified algorithm in `ux-constructor/references/verified-classic-algorithm.md`:
1. `desktopRoutes:create` (route + hidden-tab children)
2. `uiSchemas:insert` (FlowRoute schema)
3. `flowModels:save` × 5+ (RootPageModel → BlockGridModel → TableBlockModel → columns × N)
4. Another `flowModels:save` chain for the filter form

MCP blueprint collapses all of that into one declarative call with server-side UID generation. Prefer MCP when available.

## See also

- `ux-constructor` — full blueprint spec and hard rules
- `mcp-patterns` — transport conventions
- `collections-and-fields` — introspection via `collections_list_meta`
