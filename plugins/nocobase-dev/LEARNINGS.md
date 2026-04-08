# NocoBase Dev Plugin -- Learnings

Accumulated fixes and discoveries from usage and feedback.

## 2026-04-09 — routes-and-menus, data-sources, data-visualization, ui-schemas, record-operations, api-patterns: UX API enrichment

**Feature:** Added 3 new skills (routes-and-menus, data-sources, data-visualization) and extended 4 existing skills (ui-schemas, record-operations, collections-and-fields, api-patterns) with missing UX constructor API coverage
**Implementation:** Created skills with reference files covering desktop/mobile routes, external data sources, chart queries, flow model templates, parent schema navigation, insert shorthands, initializeActionContext, firstOrCreate, updateOrCreate, tree/paginate params, association filters. Updated api-reference with 3 new endpoint reference files.
**Rationale:** Plugin v1.0.0 was missing 5 major API domains critical for UX development: page routing, mobile navigation, block templates, data visualization, and multi-database support. Coverage gap identified via comprehensive ux-api.md document.

## 2026-04-09 — flow-models: v2.x block engine coverage

**Feature:** Added flow-models skill covering the v2.x block engine (flowModels, flowSql, variables resources)
**Implementation:** New skill with reference file covering flowModels CRUD (findOne, save, duplicate, attach, move, destroy), 16 inherited schema actions with options key difference, flowSql (save, runById, getBind) for dynamic SQL with Liquid templates, and variables:resolve for template variable resolution. Added v2.x migration note to ui-schemas skill.
**Rationale:** Flow Models are the v2.x replacement for uiSchemas at the block level — a critical gap discovered when checking for flowModels:save endpoint coverage.
