---
name: ui-builder-index
description: |
  Router for NocoBase UI authoring skills — picks between `ux-constructor` (Modern v2, MCP-first), `flow-models` (low-level block engine), and `ui-schemas` (legacy v1) based on the task. Use when:
  - "build a UI in NocoBase"
  - "which skill for NocoBase UI"
  - "create a page in NocoBase"
  - "add a block to NocoBase"
  - "NocoBase UI authoring"
  - "which NocoBase UI skill"
  - "where do I start for a page"
  - "NocoBase page / block / form / popup"
---

# UI Builder Index

NocoBase has three UI authoring surfaces across its version history. This skill routes you to the right one.

## Decision table

| Your task | Skill to use | Transport |
|-----------|--------------|-----------|
| Create a new page, popup, tab, or multi-block layout (v2) | **`ux-constructor`** | MCP `flow_surfaces_apply_blueprint` → CLI → HTTP |
| Add a single block or edit an existing surface (v2) | **`ux-constructor`** | MCP `flow_surfaces_add_*` / `flow_surfaces_apply` |
| Configure reactions (linkage rules, field-value rules) (v2) | **`ux-constructor`** | MCP `flow_surfaces_set_*_linkage_rules` / `_set_field_value_rules` |
| Get low-level control over a Flow Model or its settings (v2) | **`flow-models`** | MCP `flow_surfaces_{get,configure,compose,mutate}` + HTTP `flowModels:*` |
| Work with `flowSql` or `variables:resolve` (v2) | **`flow-models`** | HTTP `flowSql:*` / `variables:resolve` |
| Maintain or debug a **legacy v1** page with `uiSchemas` | **`ui-schemas`** | HTTP `uiSchemas:*` only (no MCP v1 path) |
| Add or edit a route/menu entry | **`routes-and-menus`** | MCP `flow_surfaces_create_menu` + HTTP `desktopRoutes:*` |

## Choose `ux-constructor` when

You are authoring a Modern (v2) page, block, popup, tab, action, reaction, or blueprint. This is the default for all new NocoBase UI work. 42 MCP tools live here (`flow_surfaces_*`). Start with `flow_surfaces_apply_blueprint` for whole-page creation; use `flow_surfaces_apply` for subtree replacement; use the low-level adders/removers only for localized edits.

## Choose `flow-models` when

You need direct control over the flow model tree — reading/writing individual models, using `flowSql` for dynamic queries with Liquid templates, or resolving template variables. `flow-models` is the layer **below** `ux-constructor` — you call it when `flow_surfaces_*` can't express what you need, or you're integrating with a plugin that manipulates flow models directly.

## Choose `ui-schemas` when

You are maintaining a legacy Classic (v1) page — `type: "page"`, `x-component: "Page"`, built with `uiSchemas:insertAdjacent`. New work should use `ux-constructor` (v2) instead.

## Quick start by intent

| Intent | First call |
|--------|-----------|
| "Create a Customers page with a table and filter form" | `flow_surfaces_apply_blueprint` (see `ux-constructor`) |
| "Hide this column" | `flow_surfaces_remove_node` (see `ux-constructor`) |
| "When priority >= 3, mark status urgent" | `flow_surfaces_set_field_value_rules` (see `ux-constructor`) |
| "Add a row-level Edit button" | `flow_surfaces_add_record_action` (see `ux-constructor`) |
| "Run this SQL with a date parameter" | `flowSql:runById` (see `flow-models`) |
| "Fix this broken v1 page" | `uiSchemas:patch` (see `ui-schemas`) |

## See also

- `ux-constructor` — Modern v2 UI authoring (primary)
- `flow-models` — low-level v2 block engine
- `ui-schemas` — legacy v1 UI schemas
- `routes-and-menus` — routes, menus, role access
- `mcp-patterns` — transport conventions and full tool catalog
