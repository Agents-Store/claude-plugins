# nocobase-dev

NocoBase V2 development plugin for the Agents Store. Complete API reference and patterns for customizing NocoBase through its HTTP API.

## What This Plugin Covers

- **Collections & Fields** -- Create, modify, and manage data collections and their fields
- **Record Operations** -- CRUD operations, filtering, pagination, associations, import/export
- **Workflow Automation** -- Create workflows, configure nodes, monitor executions
- **UI Schemas** -- Customize pages, forms, tables, and themes via API
- **Authentication & Users** -- Manage users, roles, permissions, API keys, SSO
- **Localization** -- Multi-language support and translation management
- **System Administration** -- Settings, storage, plugins, app management

## Skills

| Skill | Description |
|-------|-------------|
| `setup` | Verify NocoBase API connection |
| `api-patterns` | NocoBase API conventions (Resource:Action model, filtering, pagination) |
| `collections-and-fields` | Collection and field management via API |
| `record-operations` | Data CRUD, associations, import/export |
| `workflow-automation` | Workflow creation, nodes, execution monitoring |
| `ui-schemas` | UI schema management and themes |
| `auth-and-users` | Authentication, users, roles, API keys |
| `localization` | Multi-language support |
| `system-admin` | System settings, storage, plugins |
| `api-reference` | Complete HTTP endpoint reference |
| `troubleshoot` | Error diagnosis and fixes |
| `examples` | End-to-end scenario walkthroughs |

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
