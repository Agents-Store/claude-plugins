# `nc-mcp` Tool Catalog

Complete enumeration of every `*` tool on the live NocoBase MCP server. Grouped by prefix, annotated by purpose. Use with `ToolSearch(query: "nc-mcp", max_results: 30)` to bulk-load schemas before invoking.

Total: ~146 tools across 20 prefix groups.

## `auth_*` — session lifecycle (5)

| Tool | Purpose |
|------|---------|
| `auth_sign_in` | Sign in with credentials or SSO payload. Returns session token. |
| `auth_sign_up` | Create a new user account (if open registration is enabled). |
| `auth_sign_out` | End the current session. |
| `auth_check` | Verify session validity; returns current user and roles. |
| `auth_change_password` | Change password for the current session user. |

## `authenticators_*` — auth provider registry (7)

| Tool | Purpose |
|------|---------|
| `authenticators_list` | List configured auth providers (local, OIDC, SAML, LDAP, etc.) |
| `authenticators_get` | Get one auth provider config |
| `authenticators_create` | Register a new auth provider |
| `authenticators_update` | Update provider config |
| `authenticators_destroy` | Remove a provider |
| `authenticators_list_types` | Enumerate supported provider types (OIDC, SAML, etc.) |
| `authenticators_public_list` | Public-facing list (used on sign-in page) |

## `available_actions_list` — ACL action registry (1)

| Tool | Purpose |
|------|---------|
| `available_actions_list` | Lists canonical ACL action names: `view` (with aliases `get`, `list`, `query`), `create` (`firstOrCreate`, `updateOrCreate`), `update` (`move`), `destroy`, `export` (`exportAttachments`), `importXlsx`. Call this before writing role resource scopes. |

## `collection_categories_*` — sidebar grouping (6)

| Tool | Purpose |
|------|---------|
| `collection_categories_list` | List all categories (the left-sidebar groups in Collection Manager) |
| `collection_categories_get` | Get one category |
| `collection_categories_create` | Create a category |
| `collection_categories_update` | Rename or restyle |
| `collection_categories_destroy` | Remove |
| `collection_categories_move` | Reorder |

## `collections_*` — collection CRUD + meta (9)

| Tool | Purpose |
|------|---------|
| `collections_list` | List all collections (paginated) |
| `collections_list_meta` | **One-shot full schema dump** — every collection with fields, options, `filterTargetKey`. Use before any schema edit. |
| `collections_get` | Get one collection with its fields |
| `collections_create` | Create a collection |
| `collections_update` | Update collection options |
| `collections_destroy` | Delete a collection |
| `collections_move` | Reorder collection within category |
| `collections_set_fields` | Replace the entire fields array |
| `collections_apply` | **Declarative upsert** — `{ name, title, template?, fields[], settings? }`. Creates if missing, updates in place. |

## `collections_fields_*` — field CRUD (6)

| Tool | Purpose |
|------|---------|
| `collections_fields_list` | List fields in a collection |
| `collections_fields_get` | Get one field with its full `uiSchema` |
| `collections_fields_create` | Create a field |
| `collections_fields_update` | Update field (type, interface, uiSchema, validators) |
| `collections_fields_destroy` | Delete a field |
| `collections_fields_move` | Reorder fields |

## `fields_apply` — declarative field upsert (1)

| Tool | Purpose |
|------|---------|
| `fields_apply` | Upsert a list of fields in one call. Param: `{ collectionName, fields: [ { name, type, interface, uiSchema, ... } ] }`. Preferred over multiple `collections_fields_create/update` calls. |

## `resource_*` — generic record CRUD (6)

| Tool | Purpose |
|------|---------|
| `resource_list` | Paginated list. `{ resource, filter?, fields?, page?, pageSize?, sort?, appends?, dataSource? }` |
| `resource_query` | Aggregated server-side query. `{ resource, measures?, dimensions?, filter?, dataSource? }` |
| `resource_get` | One record by PK. `{ resource, filterByTk, appends?, fields? }` |
| `resource_create` | Insert one record. `{ resource, values, sourceId?, dataSource? }` |
| `resource_update` | Update by PK or filter. `{ resource, filterByTk?/filter?, values }` |
| `resource_destroy` | Delete by PK or filter. `{ resource, filterByTk?/filter? }` |

**`resource` is the collection name.** Works against any collection including multi-DB via `dataSource`.

## `db_views_*` — raw database view inspection (3)

| Tool | Purpose |
|------|---------|
| `db_views_list` | List raw DB views available to NocoBase |
| `db_views_get` | Get a view's columns and SQL |
| `db_views_query` | Query rows from a view. `{ filterByTk, schema?, page?, pageSize? }` |

Read-only. Useful for reporting and analytics against non-NocoBase-managed DB objects.

## `workflows_*` — workflow definitions (9)

| Tool | Purpose |
|------|---------|
| `workflows_list` | List workflows |
| `workflows_get` | Get one workflow + its nodes |
| `workflows_create` | Create a workflow (starts disabled) |
| `workflows_update` | Update workflow options |
| `workflows_destroy` | Delete |
| `workflows_execute` | Manually fire a workflow with a trigger-input body. `{ filterByTk, values, autoRevision? }` → returns `{ execution: { id, status }, newVersionId? }` |
| `workflows_sync` | Synchronize workflow definitions across envs |
| `workflows_revision` | Create a new version (revision) of a workflow |
| `workflows_nodes_create` | Create a node inside a workflow |

## `flow_nodes_*` — workflow node editing (7)

| Tool | Purpose |
|------|---------|
| `flow_nodes_get` | Get one node |
| `flow_nodes_update` | Update node config |
| `flow_nodes_destroy` | Delete node (severs only this node) |
| `flow_nodes_destroy_branch` | Delete node + its downstream branch |
| `flow_nodes_duplicate` | Clone a node |
| `flow_nodes_move` | Reorder within a parent |
| `flow_nodes_test` | Test a node with sample input |

## `executions_*` — workflow runs (4)

| Tool | Purpose |
|------|---------|
| `executions_list` | List executions (paginated, filter by workflow, status) |
| `executions_get` | Get one execution with its job tree |
| `executions_cancel` | Cancel a running execution |
| `executions_destroy` | Delete execution history |

## `jobs_*` — background jobs (3)

| Tool | Purpose |
|------|---------|
| `jobs_list` | List background jobs (imports, exports, long-running tasks) |
| `jobs_get` | Get one job's status |
| `jobs_resume` | Resume a paused job |

## `user_workflow_tasks_list_mine` — approval inbox (1)

| Tool | Purpose |
|------|---------|
| `user_workflow_tasks_list_mine` | List workflow manual-node tasks assigned to the current user |

## `flow_surfaces_*` — UI composition (42)

The big surface. Builds pages, menus, tabs, popups, blocks, fields, actions, linkage rules, blueprints, and templates.

### Structural create / destroy

| Tool | Purpose |
|------|---------|
| `flow_surfaces_create_page` | Create a blank Modern (v2) page |
| `flow_surfaces_destroy_page` | Remove a page |
| `flow_surfaces_create_menu` | Create a menu entry (group or item) |
| `flow_surfaces_update_menu` | Rename/re-icon a menu entry |

### Tabs

| Tool | Purpose |
|------|---------|
| `flow_surfaces_add_tab` | Add a new tab to a page |
| `flow_surfaces_update_tab` | Rename or update tab props |
| `flow_surfaces_move_tab` | Reorder tabs |
| `flow_surfaces_remove_tab` | Remove a tab |
| `flow_surfaces_add_popup_tab` | Add a tab inside a popup |
| `flow_surfaces_update_popup_tab` | Update popup tab |
| `flow_surfaces_move_popup_tab` | Reorder popup tabs |
| `flow_surfaces_remove_popup_tab` | Remove popup tab |

### Blocks / fields / actions — low-level adders

| Tool | Purpose |
|------|---------|
| `flow_surfaces_add_block` | Add a single block to a target |
| `flow_surfaces_add_blocks` | Add multiple blocks in one call |
| `flow_surfaces_add_field` | Add a single field to a form/details/createForm/editForm/filterForm |
| `flow_surfaces_add_fields` | Add multiple fields |
| `flow_surfaces_add_action` | Add a single action button/menu item |
| `flow_surfaces_add_actions` | Add multiple actions |
| `flow_surfaces_add_record_action` | Add a per-row action to a table/list |
| `flow_surfaces_add_record_actions` | Add multiple per-row actions |
| `flow_surfaces_move_node` | Move any node within its parent |
| `flow_surfaces_remove_node` | Remove any node |

### Declarative apply family

| Tool | Purpose |
|------|---------|
| `flow_surfaces_apply` | **Replace a subtree** by `target.uid` with a full `spec: { use, props, subModels, popup?, ... }` |
| `flow_surfaces_apply_blueprint` | **Whole-page blueprint** — create/replace a page + menu from a declarative spec (`page`, `navigation`, `tabs`, `blocks`, `reaction`) |
| `flow_surfaces_apply_approval_blueprint` | Variant for approval-flow pages |

### Linkage / value / layout rules

| Tool | Purpose |
|------|---------|
| `flow_surfaces_set_block_linkage_rules` | When X, show/hide block Y |
| `flow_surfaces_set_action_linkage_rules` | When X, enable/disable action Y |
| `flow_surfaces_set_field_linkage_rules` | When X, show/hide/disable/require field Y |
| `flow_surfaces_set_field_value_rules` | Compute field value from other fields (formulajs) |
| `flow_surfaces_set_layout` | Set tab/popup inner grid layout |
| `flow_surfaces_set_event_flows` | Wire event-flow reactions |

### Meta / discovery

| Tool | Purpose |
|------|---------|
| `flow_surfaces_get` | Get a surface subtree by UID |
| `flow_surfaces_catalog` | Enumerate available blocks/fields/actions at this target |
| `flow_surfaces_describe_surface` | Full structural dump of a surface |
| `flow_surfaces_context` | Get the live context (scope) at a node — useful for reactions |
| `flow_surfaces_get_reaction_meta` | Get available reaction sources/targets at a node |
| `flow_surfaces_configure` | Apply a low-level configure payload |
| `flow_surfaces_compose` | Compose a subtree from partial inputs |
| `flow_surfaces_mutate` | Lowest-level surface mutation primitive |
| `flow_surfaces_update_settings` | Update surface-level settings |

### Templates

| Tool | Purpose |
|------|---------|
| `flow_surfaces_list_templates` | List saved page/block templates |
| `flow_surfaces_get_template` | Get one template |
| `flow_surfaces_save_template` | Save current surface as template |
| `flow_surfaces_update_template` | Update template body |
| `flow_surfaces_destroy_template` | Delete template |
| `flow_surfaces_convert_template_to_copy` | Detach from template reference (make editable copy) |

## `desktop_routes_list_accessible` — routing (1)

| Tool | Purpose |
|------|---------|
| `desktop_routes_list_accessible` | List desktop routes visible to the current user (respects role ACL) |

## `roles_*` — role lifecycle + ACL (19)

### Role CRUD + defaults

| Tool | Purpose |
|------|---------|
| `roles_list` | List roles |
| `roles_get` | Get one role + its permissions |
| `roles_create` | Create a role |
| `roles_update` | Update role options |
| `roles_destroy` | Delete a role |
| `roles_check` | Check which permissions the current user has |
| `roles_set_default_role` | Mark a role as default for new users |
| `roles_set_system_role_mode` | Switch between single-role / multi-role modes |

### Role ↔ user membership

| Tool | Purpose |
|------|---------|
| `roles_users_list` | List users in a role |
| `roles_users_add` | Add users to a role |
| `roles_users_remove` | Remove users from a role |

### Role ↔ resource scopes

| Tool | Purpose |
|------|---------|
| `roles_resources_scopes_list` | List per-resource scopes for a role |
| `roles_resources_scopes_get` | Get one scope |
| `roles_data_source_resources_create` | Create a scope on a data-source resource |
| `roles_data_source_resources_get` | Get it |
| `roles_data_source_resources_update` | Update it |
| `roles_data_sources_collections_list` | List collections in a data source visible to this role |

### Role ↔ desktop-route access

| Tool | Purpose |
|------|---------|
| `roles_desktop_routes_list` | List routes a role can access |
| `roles_desktop_routes_add` | Grant route access |
| `roles_desktop_routes_remove` | Revoke route access |
| `roles_desktop_routes_set` | Replace full route-access list |

## `users_*` — user CRUD (5)

| Tool | Purpose |
|------|---------|
| `users_list` | List users |
| `users_get` | Get one user |
| `users_create` | Create a user |
| `users_update` | Update user |
| `users_destroy` | Deactivate/delete user |

## `users_roles_*` — user-role membership (3)

| Tool | Purpose |
|------|---------|
| `users_roles_list` | List a user's roles |
| `users_roles_add` | Add a role to a user |
| `users_roles_remove` | Remove a role from a user |

## `data_sources_*` — multi-datasource (8)

| Tool | Purpose |
|------|---------|
| `data_sources_list_enabled` | List enabled external datasources |
| `data_sources_roles_get` | Get role config per-datasource |
| `data_sources_roles_update` | Update role config per-datasource |
| `data_sources_roles_resources_scopes_list` | List per-resource scopes in a datasource |
| `data_sources_roles_resources_scopes_get` | Get one |
| `data_sources_roles_resources_scopes_create` | Create one |
| `data_sources_roles_resources_scopes_update` | Update |
| `data_sources_roles_resources_scopes_destroy` | Delete |

---

## ToolSearch loading pattern

```
ToolSearch(query: "nc-mcp", max_results: 30)
```

Loads schemas for the entire toolkit in one call. The query is a keyword match against server-name substring, so all ~146 tools come back together.

Individual load (rarely needed):
```
ToolSearch(query: "select:flow_surfaces_apply_blueprint,workflows_execute", max_results: 5)
```

## Domain ownership (which skill owns what)

| Group | Primary skill |
|-------|---------------|
| `auth_*`, `authenticators_*`, `users_*`, `users_roles_*`, `roles_*` | `auth-and-users` |
| `collections_*`, `collections_fields_*`, `collection_categories_*`, `fields_apply` | `collections-and-fields` (+ design decisions in `data-modeling`) |
| `resource_*`, `db_views_*` | `record-operations` |
| `workflows_*`, `flow_nodes_*`, `executions_*`, `jobs_*`, `user_workflow_tasks_*` | `workflow-automation` |
| `flow_surfaces_*` | `ux-constructor` (primary), `flow-models` (low-level meta), `routes-and-menus` (menu+tab subset) |
| `desktop_routes_list_accessible` | `routes-and-menus` |
| `data_sources_*` | `data-sources` |
| `available_actions_list` | `auth-and-users` (for ACL scope writing); shown in `system-admin` for operators |
