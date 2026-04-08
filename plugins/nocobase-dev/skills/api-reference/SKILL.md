---
name: api-reference
description: This skill should be used when the user asks for "NocoBase API endpoints", "NocoBase REST API", "NocoBase curl examples", "NocoBase API documentation", "NocoBase HTTP API reference", or needs specific HTTP endpoint details for NocoBase.
disable-model-invocation: true
---

# NocoBase API Reference

Complete HTTP API endpoint reference for NocoBase. All endpoints use the Resource & Action model at `/api/{resource}:{action}`.

## Authentication

Every request requires a Bearer token:

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/{resource}:{action}"
```

## Resource Overview

| Domain | Resource | Key Actions | Reference File |
|--------|----------|-------------|----------------|
| **Collections** | `collections` | list, get, create, update, destroy, move, setFields | `references/endpoints-collections.md` |
| **Fields** | `collections/{name}/fields` | list, get, create, update, destroy, move | `references/endpoints-collections.md` |
| **Collection Categories** | `collectionCategories` | list, get, create, update, destroy, move | `references/endpoints-collections.md` |
| **Database Views** | `dbViews` | list, get, query | `references/endpoints-collections.md` |
| **Records** | `{collection}` | list, get, create, update, destroy, move, export, import | `references/endpoints-records.md` |
| **Associations** | `{collection}/{id}/{assoc}` | get, create, update, destroy, set, remove, add, toggle, list | `references/endpoints-records.md` |
| **Workflows** | `workflows` | list, get, create, update, destroy, execute, revision, sync | `references/endpoints-workflows.md` |
| **Workflow Nodes** | `flow_nodes` | get, create, update, destroy, duplicate, move, test | `references/endpoints-workflows.md` |
| **Executions** | `executions` | list, get, cancel, destroy | `references/endpoints-workflows.md` |
| **Jobs** | `jobs` | list, get, resume | `references/endpoints-workflows.md` |
| **UI Schemas** | `uiSchemas` | getJsonSchema, getProperties, getParentJsonSchema, getParentProperty, insert, insertNewSchema, remove, patch, batchPatch, insertAdjacent, insertBeforeBegin, insertAfterBegin, insertBeforeEnd, insertAfterEnd, initializeActionContext, saveAsTemplate, clearAncestor | `references/endpoints-ui-auth.md` |
| **Schema Templates (Legacy)** | `uiSchemaTemplates` | list, get | `references/endpoints-ui-auth.md` |
| **Flow Model Templates** | `flowModelTemplates` | list, get, create, update, destroy | `references/endpoints-ui-auth.md` |
| **Desktop Routes** | `desktopRoutes` | listAccessible, getAccessible, create, update, move, destroy | `references/endpoints-routes.md` |
| **Mobile Routes** | `mobileRoutes` | listAccessible, create, update, move, destroy | `references/endpoints-routes.md` |
| **Role Routes** | `roles/{name}/desktopRoutes` | set | `references/endpoints-routes.md` |
| **Data Sources** | `dataSources` | listEnabled, testConnection, refresh, readTables, loadTables | `references/endpoints-data-sources.md` |
| **DS Collections** | `dataSources/{key}/collections` | list, update | `references/endpoints-data-sources.md` |
| **DS Fields** | `dataSourcesCollections/{key}.{coll}/fields` | list, get, create, update, destroy | `references/endpoints-data-sources.md` |
| **Charts** | `charts` | query | `references/endpoints-charts.md` |
| **Flow Models** | `flowModels` | findOne, save, duplicate, attach, move, destroy + 16 inherited schema actions | `references/endpoints-flow-models.md` |
| **Flow SQL** | `flowSql` | save, runById, getBind | `references/endpoints-flow-models.md` |
| **Variables** | `variables` | resolve | `references/endpoints-flow-models.md` |
| **Auth** | `auth` | check, signIn, signUp, signOut, changePassword | `references/endpoints-ui-auth.md` |
| **Users** | `users` | list, get, create, update, destroy | `references/endpoints-ui-auth.md` |
| **Roles** | `roles` | list, get, create, update, destroy, check, setDefaultRole | `references/endpoints-ui-auth.md` |
| **API Keys** | `apiKeys` | list, create, destroy | `references/endpoints-ui-auth.md` |
| **Authenticators** | `authenticators` | list, get, create, update, destroy, listTypes, publicList | `references/endpoints-ui-auth.md` |
| **System Settings** | `systemSettings` | get, update | `references/endpoints-system.md` |
| **Storage** | `storages` | list, get, create, update, destroy | `references/endpoints-system.md` |
| **Plugins** | `pm` | enable, disable, remove | `references/endpoints-system.md` |
| **App** | `app` | getInfo, getLang, getPlugins, restart, clearCache | `references/endpoints-system.md` |
| **Localization** | `localization` | sync, publish | `references/endpoints-system.md` |

## Quick Example — List Collections

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/collections:list?page=1&pageSize=50"
```

## Full OpenAPI Spec

The complete machine-readable OpenAPI 3.0 specification is available at `references/nocobase-openapi.json`. Use it for programmatic endpoint discovery or code generation.

## Reference Files

- `references/endpoints-collections.md` — Collections, fields, categories, database views
- `references/endpoints-records.md` — Record CRUD, file uploads, associations (38 endpoints)
- `references/endpoints-workflows.md` — Workflows, nodes, executions, jobs
- `references/endpoints-ui-auth.md` — UI schemas, auth, users, roles, API keys, authenticators, SSO
- `references/endpoints-system.md` — System settings, storage, plugins, localization, themes, utilities
- `references/endpoints-routes.md` — Desktop routes, mobile routes, role route access
- `references/endpoints-data-sources.md` — Data sources, data-source-scoped collections and fields
- `references/endpoints-charts.md` — Data visualization / chart queries
- `references/endpoints-flow-models.md` — Flow models (v2.x block engine), Flow SQL, template variables
- `references/nocobase-openapi.json` — Full OpenAPI 3.0 specification
