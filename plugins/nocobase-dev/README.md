# nocobase-dev

NocoBase V2 development plugin for the Agents Store. Complete API reference and patterns for customizing NocoBase through its HTTP API.

## What This Plugin Covers

- **Collections & Fields** -- Create, modify, and manage data collections and their fields
- **Record Operations** -- CRUD operations, filtering, pagination, associations, import/export, firstOrCreate, updateOrCreate
- **Workflow Automation** -- Create workflows, configure nodes, monitor executions
- **UI Schemas** -- Customize pages, forms, tables, themes, and block templates via API
- **Flow Models** -- V2.x block engine: model CRUD, tree operations, Flow SQL, template variables
- **Routes & Menus** -- Desktop and mobile page/menu structure, tabs, role-based route access
- **Data Sources** -- External database connections, table import, data-source-scoped collections
- **Data Visualization** -- Chart queries with aggregation, grouping, and caching
- **Authentication & Users** -- Manage users, roles, permissions, API keys, SSO
- **Localization** -- Multi-language support and translation management
- **Plugin Development** -- Scaffold plugins, lifecycle hooks, server/client classes, migrations, custom actions
- **System Administration** -- Settings, storage, plugins, app management

## Skills

| Skill | Description |
|-------|-------------|
| `setup` | Verify NocoBase API connection |
| `api-patterns` | NocoBase API conventions (Resource:Action model, filtering, pagination) |
| `collections-and-fields` | Collection and field management via API |
| `record-operations` | Data CRUD, associations, import/export |
| `workflow-automation` | Workflow creation, nodes, execution monitoring |
| `ui-schemas` | UI schema management, themes, and block templates |
| `flow-models` | V2.x block engine — flow model CRUD, SQL queries, variables |
| `ux-constructor` | Modern Page (v2) creation — verified algorithm for pages, table/form blocks, columns |
| `routes-and-menus` | Desktop and mobile page routing, menus, role-based access |
| `data-sources` | External database connections, multi-DB collections and fields |
| `data-visualization` | Chart queries, aggregations, dashboard data |
| `auth-and-users` | Authentication, users, roles, API keys |
| `localization` | Multi-language support |
| `plugin-development` | NocoBase plugin scaffolding, lifecycle, migrations, custom actions |
| `system-admin` | System settings, storage, plugins |
| `api-reference` | Complete HTTP endpoint reference |
| `troubleshoot` | Error diagnosis and fixes |
| `examples` | End-to-end scenario walkthroughs (CRM, workflows, project management, i18n) |

## Agent

- **nocobase-developer** -- NocoBase API specialist for collection design, workflow building, UI customization, and debugging

## Prerequisites

- A running NocoBase V2 instance
- An API key with appropriate permissions

## Configuration

When enabling this plugin, you'll be prompted for:
- **nocobase_url** -- Your NocoBase instance URL (e.g., `https://your-nocobase.com`)
- **nocobase_api_key** -- Your NocoBase API key

These values are used in curl examples throughout the skills as `${NOCOBASE_URL}` and `${NOCOBASE_API_KEY}`.

## Environment Variables

For your project code, set these environment variables:
- `NOCOBASE_URL` -- NocoBase instance URL
- `NOCOBASE_API_KEY` -- NocoBase API authentication key
