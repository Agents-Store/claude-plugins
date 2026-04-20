# NocoBase Dev Plugin -- Learnings

Accumulated fixes and discoveries from usage and feedback.

## 2026-04-20 — v1.5.0: MCP coverage + upstream skill content merge

**Feature:** Added full `nc-mcp` MCP tool coverage (~146 tools across 20 groups) and merged content from the official NocoBase skills repository into the existing 18-skill structure.

**Implementation:**
- New skill `mcp-patterns` documenting MCP transport conventions, tool catalog, declarative-apply family (`fields_apply`, `collections_apply`, `flow_surfaces_apply`, `flow_surfaces_apply_blueprint`), ToolSearch bulk-load recipe, and three-tier fallback chain (MCP → `nocobase-ctl` CLI → HTTP).
- New skill `data-modeling` with the upstream design playbook merged wholesale: collection types (general/tree/file/calendar/view/sql/inherit), field types, relations (o2m/m2o/m2m/o2o/mbm), model-pack archetypes, decision matrix, MCP mutation sequences, and verification playbook. Triggers disambiguated from `collections-and-fields` (which owns CRUD) via design-intent wording.
- New skill `ui-builder-index` — thin routing skill between `ux-constructor` (Modern v2), `flow-models` (low-level v2), and `ui-schemas` (legacy v1).
- New skill `publish-manage` — risk-gated cross-environment publishing with `disable-model-invocation: true`; covers backup+restore vs migration methods, publishing templates (schema_only_all, full_overwrite, etc.), precheck gates.
- Extended all 18 existing skills with MCP-first tool references, CLI fallback, and HTTP fallback sections. Added See also sections for cross-referencing.
- Split `ux-constructor/SKILL.md` from 745 LOC → 286 LOC by moving the verified classic HTTP algorithm (phase-by-phase `desktopRoutes:create` → `uiSchemas:insert` → `flowModels:save` sequence with display model tables) into `references/verified-classic-algorithm.md` (638 LOC). Added upstream ui-builder reference tree under `references/ui-builder/` (51 files: blueprints, patterns, blocks, js-models, reactions, chart, templates).
- Merged upstream content into domain skills:
  - `auth-and-users/references/acl/` — acl-manage risk-gated governance (14 refs)
  - `workflow-automation/references/workflow/` — nodes (27 node types), triggers (7 trigger types), conventions, modeling, http-api (40 refs)
  - `plugin-development/references/upstream/` — server (11 refs) + client-v2 (10 refs) playbook; `references/pm/` for pm CLI
  - `setup/references/env-bootstrap/` — install, upgrade, MCP runbook, troubleshooting (12 refs)
  - `api-patterns/references/utils/` — formulajs, mathjs, filter-syntax, UID, evaluators
- Updated `nocobase-developer` agent: added `*` to tools, MCP→CLI→HTTP fallback rule, upstream hard rules (never use `this.app.use()`, client-v2 only), and MCP example blocks.
- Bumped plugin and marketplace to 1.5.0 with expanded description and new keywords (mcp, nc-mcp, flow-surfaces, blueprints, reactions, data-modeling, acl, publish).

**Rationale:** NocoBase published an official MCP server (`nc-mcp`) and skills repository (github.com/nocobase/skills) since v1.4.0. The plugin previously covered only the HTTP API; this upgrade brings it to parity with the modern NocoBase authoring surface (blueprints, flow-surfaces, RBAC governance, publishing) and documents all three transports in one place.

**Audit trail:** Upstream content merged from github.com/nocobase/skills on 2026-04-20. Upstream has no LICENSE file at time of merge; user authorized copy-as-is per "upstream is open source" directive. Total upstream content merged: ~220 markdown reference files across 8 upstream skills (data-modeling, ui-builder, acl-manage, workflow-manage, plugin-development, plugin-manage, env-bootstrap, utils, publish-manage). `dsl-reconciler` explicitly deferred to v1.6.0 (upstream marks it opt-in / actively developed).

**Severity:** Major feature addition (4 new skills, 18 skills extended, 1 agent updated, ~220 reference files added).


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

## 2026-04-13 — plugin-wide: enrichment from nocobase ops plugin

**Feature:** Added plugin-development skill, enriched collections-and-fields (design patterns, inheritance, advanced fields, validation), enriched workflow-automation (action trigger, variable system, error handling patterns), added project-management example scenario, added evals for 7 key skills
**Implementation:** New plugin-development skill with TypeScript scaffold, lifecycle, migrations, custom actions, ACL, plugin management API. Extended collections-and-fields with system fields, 4-step design process, architecture patterns (master-detail, tree, soft delete, polymorphic), inheritance, formula/sequence fields, validation. Extended workflow-automation with action trigger type, $context/$jobsData variables, execution modes, error handling patterns. New project-management scenario with full curl examples. Created evals/evals.json for collections-and-fields, record-operations, workflow-automation, ui-schemas, ux-constructor, flow-models, plugin-development.
**Rationale:** Cross-pollination from the nocobase (ops) plugin which had strong design-pattern and plugin-development coverage absent in nocobase-dev. Selectively merged only content that adds value to a dev-oriented HTTP API plugin — excluded MCP-specific content and commands.
**Severity:** Major

## 2026-04-09 — flow-models: v2.x block engine coverage

**Feature:** Added flow-models skill covering the v2.x block engine (flowModels, flowSql, variables resources)
**Implementation:** New skill with reference file covering flowModels CRUD (findOne, save, duplicate, attach, move, destroy), 16 inherited schema actions with options key difference, flowSql (save, runById, getBind) for dynamic SQL with Liquid templates, and variables:resolve for template variable resolution. Added v2.x migration note to ui-schemas skill.
**Rationale:** Flow Models are the v2.x replacement for uiSchemas at the block level — a critical gap discovered when checking for flowModels:save endpoint coverage.
