# NocoBase Dev Plugin -- Learnings

Accumulated fixes and discoveries from usage and feedback.

## 2026-04-09 — routes-and-menus, data-sources, data-visualization, ui-schemas, record-operations, api-patterns: UX API enrichment

**Feature:** Added 3 new skills (routes-and-menus, data-sources, data-visualization) and extended 4 existing skills (ui-schemas, record-operations, collections-and-fields, api-patterns) with missing UX constructor API coverage
**Implementation:** Created skills with reference files covering desktop/mobile routes, external data sources, chart queries, flow model templates, parent schema navigation, insert shorthands, initializeActionContext, firstOrCreate, updateOrCreate, tree/paginate params, association filters. Updated api-reference with 3 new endpoint reference files.
**Rationale:** Plugin v1.0.0 was missing 5 major API domains critical for UX development: page routing, mobile navigation, block templates, data visualization, and multi-database support. Coverage gap identified via comprehensive ux-api.md document.

## 2026-04-09 — plugin audit: cross-references and ux-api reference

**Feature:** Added cross-references to ux-constructor from ui-schemas, flow-models, routes-and-menus, and api-reference skills. Added ux-api.md (2551-line complete backend API reference) as `references/ux-api-reference.md` in ux-constructor skill. Added `flowPage` route type to routes-and-menus.
**Implementation:** Updated 5 SKILL.md files with cross-references directing users to ux-constructor for Modern Page v2 workflows. Moved ux-api.md from repo root into plugin.
**Rationale:** Plugin audit found low redundancy but no interconnection — skills didn't mention each other. Users creating pages would hit ui-schemas or flow-models skills and not discover the verified ux-constructor workflow. The ux-api.md reference serves as troubleshooting fallback when the algorithm doesn't produce expected results.

## 2026-04-09 — ux-constructor: Modern Page (v2) creation algorithm

**Feature:** New skill documenting the verified algorithm for creating Modern Page (v2) pages with table blocks and columns via API
**Implementation:** Algorithm captured by intercepting browser network traffic during manual page creation. Sequence: `desktopRoutes:create` (type=flowPage) -> `uiSchemas:insert` (FlowRoute) -> `flowModels:save` (RootPageModel -> BlockGridModel -> TableBlockModel -> TableColumnModel). Includes display model mapping table and troubleshooting guide.
**Rationale:** The existing skills documented individual API endpoints but not the correct multi-step workflow. Previous attempts to create pages programmatically used the wrong algorithm (Classic v1 with uiSchemas:insertAdjacent). The key discovery: Modern pages use `type: "flowPage"`, `x-component: "FlowRoute"`, and `flowModels:save` instead of uiSchemas for block creation. Verified by successfully creating 12 pages with table blocks for all database collections.

## 2026-04-09 — flow-models: v2.x block engine coverage

**Feature:** Added flow-models skill covering the v2.x block engine (flowModels, flowSql, variables resources)
**Implementation:** New skill with reference file covering flowModels CRUD (findOne, save, duplicate, attach, move, destroy), 16 inherited schema actions with options key difference, flowSql (save, runById, getBind) for dynamic SQL with Liquid templates, and variables:resolve for template variable resolution. Added v2.x migration note to ui-schemas skill.
**Rationale:** Flow Models are the v2.x replacement for uiSchemas at the block level — a critical gap discovered when checking for flowModels:save endpoint coverage.
