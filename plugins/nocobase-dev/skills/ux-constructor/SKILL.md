---
name: ux-constructor
description: |
  NocoBase Modern Page (v2) creation and editing — pages, blocks (table, form, filter-form, details, edit-form, grid-card, chart), tabs, popups, record actions, and linkage/value reactions — via `flow_surfaces_*` MCP tools (42 tools), the `nocobase-ctl flow-surfaces` CLI, or the verified HTTP algorithm. Use when:
  - "create a NocoBase page"
  - "add a modern page"
  - "build a page with a table block"
  - "add form block to page"
  - "NocoBase UX constructor"
  - "flow surfaces NocoBase"
  - "flow_surfaces_apply"
  - "flow_surfaces_apply_blueprint"
  - "applyBlueprint NocoBase"
  - "NocoBase blueprint"
  - "nocobase-ctl flow-surfaces"
  - "reactions NocoBase"
  - "linkage rules NocoBase"
  - "field value rules NocoBase"
  - "NocoBase popup tab"
  - "record actions NocoBase"
  - "modify existing page blocks"
  - "hide a column"
  - "show a column"
  - "change column width"
---

# UX Constructor — Modern Page (v2)

Build and edit NocoBase Modern pages, blocks, popups, tabs, record actions, and reactions programmatically. This skill is the primary entry point for any NocoBase v2 UI authoring work. Prefer this skill over `ui-schemas` (legacy v1) and `flow-models` (low-level block engine).

## Transport fallback chain

1. **MCP first** — the 42 `flow_surfaces_*` tools. Most UI work goes through the declarative-apply family (`flow_surfaces_apply_blueprint` for whole pages, `flow_surfaces_apply` for subtree replacement) with low-level `add_block`/`add_field`/`add_action` as granular fallback.
2. **CLI second** — `nocobase-ctl flow-surfaces <subcommand>`. Thin wrapper around the MCP tools. Good when MCP is not connected but the CLI is installed on the host.
3. **HTTP third** — the verified `desktopRoutes:create` → `uiSchemas:insert` → `flowModels:save` sequence documented in `references/verified-classic-algorithm.md`. Use only when MCP and CLI are both unavailable.

## MCP workflow — whole-page creation with `apply_blueprint`

Create a complete page + menu entry + blocks in one declarative call. This is the default path.

```
flow_surfaces_apply_blueprint({
  page: {
    pageTitle: "Customers",
    menuGroupTitle: "CRM"
  },
  navigation: {
    item: { title: "Customers", icon: "TeamOutlined" }
  },
  tabs: [{
    title: "All",
    layout: { cols: 24 },
    blocks: [
      { use: "table", resource: "customers", fields: ["name", "email", "status"] },
      { use: "filterForm", resource: "customers", fields: ["status", "name"] }
    ]
  }]
})
```

Returns normalized identifiers including `page.pageSchemaUid` (use for later `flow_surfaces_get`) and `navigation.group.routeId` / `desktopRoute.id` (navigation locators only).

**Before calling `apply_blueprint`:** read `references/ui-builder/whole-page-quick.md` for the full shape of the blueprint object and the hard rules (layout, filterForm handling, icons).

## MCP workflow — localized edits

For edits on an existing page, prefer low-level adders + reactions over another blueprint.

| Task | Tool |
|------|------|
| Add one block | `flow_surfaces_add_block` |
| Add multiple blocks atomically | `flow_surfaces_add_blocks` or `flow_surfaces_apply` with merged `subModels` |
| Add a form field | `flow_surfaces_add_field` |
| Add a toolbar action | `flow_surfaces_add_action` |
| Add a per-row action | `flow_surfaces_add_record_action` |
| Rearrange | `flow_surfaces_move_node` |
| Remove | `flow_surfaces_remove_node` |
| Edit settings on a node | `flow_surfaces_configure` / `flow_surfaces_update_settings` |

Before any localized edit: call `flow_surfaces_get({ target: { uid } })` to read current state, `flow_surfaces_describe_surface` for structural dump, and `flow_surfaces_catalog` to see what block/field/action types are valid at the target.

See `references/ui-builder/local-edit-quick.md` for the full localized-edit playbook.

## MCP workflow — reactions (linkage + value rules)

Reactions fire when a source changes and adjust a target (show/hide a block, compute a field value, enable an action).

```
# 1. Discover what reactions are available at this node
flow_surfaces_get_reaction_meta({ target: { uid: "<nodeUid>" } })

# 2. Write the rule (pick the family: block/field/action linkage, or field value)
flow_surfaces_set_field_value_rules({
  target: { uid: "<fieldUid>" },
  rules: [{
    when: { "form.priority": { $gte: 3 } },
    value: "urgent"
  }]
})
```

Families:

| Family | Tool |
|--------|------|
| Block show/hide | `flow_surfaces_set_block_linkage_rules` |
| Action enable/disable | `flow_surfaces_set_action_linkage_rules` |
| Field show/hide/require/disable | `flow_surfaces_set_field_linkage_rules` |
| Field computed value | `flow_surfaces_set_field_value_rules` |
| Event-flow wiring | `flow_surfaces_set_event_flows` |

See `references/ui-builder/reaction-quick.md` and `references/ui-builder/reaction.md` for the full model.

## MCP workflow — pages, menus, tabs, popups

| Task | Tool |
|------|------|
| Create a blank page | `flow_surfaces_create_page` |
| Delete a page | `flow_surfaces_destroy_page` |
| Create a menu entry | `flow_surfaces_create_menu` |
| Update menu (rename/icon) | `flow_surfaces_update_menu` |
| Add tab to a page | `flow_surfaces_add_tab` |
| Rename/reorder/remove tab | `flow_surfaces_{update,move,remove}_tab` |
| Add tab inside a popup | `flow_surfaces_add_popup_tab` |
| Update/reorder/remove popup tab | `flow_surfaces_{update,move,remove}_popup_tab` |

See also `routes-and-menus` for route CRUD and role-based access to pages.

## MCP workflow — templates

| Task | Tool |
|------|------|
| List saved templates | `flow_surfaces_list_templates` |
| Get one template | `flow_surfaces_get_template` |
| Save current surface as template | `flow_surfaces_save_template` |
| Update template body | `flow_surfaces_update_template` |
| Delete template | `flow_surfaces_destroy_template` |
| Detach reference → editable copy | `flow_surfaces_convert_template_to_copy` |

See `references/ui-builder/templates.md` for the template decision matrix.

## Hard rules (from upstream)

1. **Field truth comes from live collection metadata.** Never guess field names. Run `collections_list_meta` or `flow_surfaces_catalog` first.
2. **Default blueprint `fields[]` entries to simple strings.** Upgrade to an object only when `popup`, `target`, `renderer`, or a field-specific `type` is required.
3. **`layout` belongs on tabs[] or inline `popup`, never on a block object.** For form-style blocks (`createForm`, `editForm`, `details`, `filterForm`), use `fieldsLayout`.
4. **If a `filterForm` is part of the page request, include it in the first-pass blueprint** with stable filter items and `submit`/`reset` actions — don't leave it as an empty shell.
5. **One real tab.** For a single-page request, default to exactly one tab; do not pad with empty tabs or markdown banners.
6. **UIDs.** After `apply_blueprint`, normalize to `pageSchemaUid` for page-level `flow_surfaces_get`. Never pass a `desktopRoute.id` as `target.uid`.
7. **Reactions.** Call `get_reaction_meta` first to prove the source path is available in the current scene. Don't guess configure keys.
8. **Navigation icons.** Every newly created `navigation.group` and top-level `navigation.item` must have a valid Ant Design icon name.
9. **Prefer apply-family over repeated granular calls.** One `flow_surfaces_apply` with combined `spec.subModels` beats a dozen `add_block`/`add_field` calls.

## Authentication

### MCP
Auth is handled by the MCP transport. No additional headers in the tool call.

### HTTP fallback
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
| Model hierarchy | Flat schema tree | `RootPageModel` → `BlockGridModel` → `*BlockModel` |
| Tab support | Manual schema children | Built-in via `children` array in route |
| MCP path | Not recommended | All `flow_surfaces_*` tools target v2 |

**Always use Modern page (v2) for new pages.** Classic pages are legacy and only the `ui-schemas` skill should be used for them.

## UID Generation

NocoBase uses 11-character random alphanumeric strings as UIDs.

```
characters: a-z, 0-9
length: 11
example: "6s65g65nq2f"
```

When using `flow_surfaces_apply_blueprint`, UIDs are auto-generated server-side and returned. For HTTP fallback, pre-generate with any alphanumeric random function.

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
1. collections_list_meta() → get all collections with fields
2. desktop_routes_list_accessible() → find existing pages to avoid duplicates
3. For each collection without a page:
   flow_surfaces_apply_blueprint({
     page: { pageTitle: <title>, menuGroupTitle: "Data" },
     navigation: { item: { title: <title>, icon: "tableoutlined" } },
     tabs: [{ title: "All", blocks: [{ use: "table", resource: <collection>, fields: [<visible-fields>] }] }]
   })
```

### Add a block to an existing page

```
1. flow_surfaces_get({ target: { uid: <pageSchemaUid> } }) → find the tab container
2. flow_surfaces_add_block({ target: { uid: <tabContainerUid> }, spec: { use: <block-type>, resource: <collection> } })
```

### Delete a page

```
flow_surfaces_destroy_page({ target: { uid: <pageSchemaUid> } })
```

(Cascades to associated flow models, ui schemas, and the desktop route.)

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Page shows "Add block" but no table | Blueprint didn't include a block, or block creation failed | Re-run `flow_surfaces_apply_blueprint` with blocks[] non-empty |
| Table shows but no columns | Default empty fields[] or invalid field names | Introspect with `collections_list_meta`, pass valid names in `fields[]` |
| Page not in menu | Missing `navigation` in blueprint | Include `navigation.item` or `navigation.group` |
| 404 when navigating to page | Returned `pageSchemaUid` not normalized | Refetch route via `desktop_routes_list_accessible` |
| `x-component` wrong | Using v1 `Page` instead of v2 `FlowRoute` | Use `flow_surfaces_*` MCP tools (v2 by default); avoid mixing v1/v2 |
| Reaction rule not firing | Source path not available at target | Call `flow_surfaces_get_reaction_meta` first to confirm sources |

For the complete HTTP fallback algorithm (phase-by-phase `desktopRoutes:create` → `uiSchemas:insert` → `flowModels:save` sequence, display model tables, edit-field model mapping, row action chain), see `references/verified-classic-algorithm.md`. It is the verified path captured from the NocoBase v2.x visual constructor's network traffic and works when MCP and CLI are unavailable.

For the full backend API reference with all endpoint signatures, request/response formats, and edge cases, see `references/ux-api-reference.md`.

## Reference index

- `references/verified-classic-algorithm.md` — HTTP fallback: full `desktopRoutes` → `uiSchemas` → `flowModels` phase-by-phase algorithm with display model table
- `references/ux-api-reference.md` — complete backend API reference (2551 lines)
- `references/ui-builder/index.md` — upstream routing map (which ref to open for which task)
- `references/ui-builder/whole-page-quick.md` — whole-page blueprint quick start
- `references/ui-builder/local-edit-quick.md` — localized edit quick start
- `references/ui-builder/reaction-quick.md` — reactions quick start
- `references/ui-builder/reaction.md` — reactions deep reference
- `references/ui-builder/templates.md` — templates decision matrix
- `references/ui-builder/blocks/{table,create-form,edit-form,details,filter-form,grid-card,chart}.md` — per-block recipes
- `references/ui-builder/patterns/{popup-openview,record-actions,clickable-relation-column,many-to-many-and-through,relation-context,table-column-rendering,tree-table}.md` — common patterns
- `references/ui-builder/js-models/` — embedded JS blocks (`jsBlock`, `jsField`, `jsColumn`, `jsItem`, `jsAction`)
- `references/ui-builder/transport-crosswalk.md` — MCP ↔ CLI ↔ HTTP tool mapping
- `references/ui-builder/verification.md` — post-mutation verification checklist
- `references/ui-builder/page-archetypes.md` — archetype patterns (list page, detail page, dashboard)

## See also

- `mcp-patterns` — transport conventions and tool catalog
- `ui-builder-index` — router between `ux-constructor`, `flow-models`, and `ui-schemas`
- `flow-models` — low-level flow model CRUD (use only when flow_surfaces_* can't express what you need)
- `ui-schemas` — legacy v1 UI schemas (avoid for new pages)
- `routes-and-menus` — route/menu CRUD and role-based access
- `data-modeling` — schema decisions that feed into block `fields[]`
