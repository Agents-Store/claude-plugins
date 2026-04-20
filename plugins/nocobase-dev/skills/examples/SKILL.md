---
name: examples
description: This skill should be used when the user asks for "NocoBase examples", "NocoBase tutorial", "NocoBase walkthrough", "how to build with NocoBase", "NocoBase use case", or needs end-to-end scenario demonstrations for NocoBase API customization.
---

# NocoBase Examples

End-to-end scenario walkthroughs demonstrating how to build real-world solutions using the NocoBase HTTP API. Each scenario covers multiple skills and provides complete curl examples you can run against your instance.

## Available Scenarios

### 1. Building a CRM with Collections and Relationships

**File:** `references/scenarios/crm-collections.md`

Build a complete CRM data model from scratch using the NocoBase API. Covers creating collections, defining fields with various types, setting up belongsTo and hasMany relationships, organizing collections into categories, creating sample records, and querying data with association appends.

**Skills used:** collections-and-fields, record-operations, api-patterns

**Complexity:** Intermediate

### 2. Automating Business Processes with Workflows

**File:** `references/scenarios/workflow-automation.md`

Automate a deal-to-task pipeline where high-value deals automatically generate follow-up tasks. Covers creating a workflow with a collection trigger, adding condition and create nodes, enabling the workflow, testing with real data, and monitoring execution results.

**Skills used:** workflow-automation, record-operations, collections-and-fields

**Complexity:** Intermediate

### 3. Building a Project Management Application

**File:** `references/scenarios/project-management.md`

Build a project management app with tasks, milestones, assignments, and kanban boards. Covers creating collections with self-referencing trees (subtasks), many-to-many assignments via through tables, sequence fields for task numbers, scheduled workflows for overdue alerts, auto-completing milestones, and chart queries for dashboards.

**Skills used:** collections-and-fields, record-operations, workflow-automation, data-visualization, api-patterns

**Complexity:** Advanced

### 4. Setting Up Multi-Language Support

**File:** `references/scenarios/multi-language-setup.md`

Configure NocoBase for multilingual use, adding Ukrainian translations for collection names, field labels, and UI elements. Covers checking current language settings, syncing translatable texts, listing available strings, creating translations, and publishing them.

**Skills used:** localization, system-admin

**Complexity:** Beginner

### 5. MCP-First Page Authoring

**File:** `references/scenarios/mcp-page-authoring.md`

Build a complete Customers page with table and filter-form blocks using `flow_surfaces_apply_blueprint` — a single MCP call instead of a multi-step HTTP algorithm. Covers introspecting schema with `collections_list_meta`, assembling a blueprint, applying it, and verifying the result.

**Skills used:** ux-constructor, mcp-patterns, collections-and-fields

**Complexity:** Intermediate (but fast — one blueprint call replaces a dozen HTTP calls)

### 6. MCP-Driven Workflow Build

**File:** `references/scenarios/mcp-workflow-build.md`

Create a collection-triggered workflow with condition + create + mailer nodes using `workflows_create` + `workflows_nodes_create` + `flow_nodes_update` — all MCP. Covers versioning via `workflows_revision`, manual execution via `workflows_execute`, and execution inspection via `executions_get`.

**Skills used:** workflow-automation, mcp-patterns, record-operations

**Complexity:** Intermediate

## Scenario Reference Matrix

| Scenario | Primary Domain | Skills Covered | Complexity | Key API Resources |
|----------|---------------|----------------|------------|-------------------|
| CRM Collections | Data modeling | collections-and-fields, record-operations, api-patterns | Intermediate | collections, fields, collectionCategories, records |
| Workflow Automation | Business logic | workflow-automation, record-operations, collections-and-fields | Intermediate | workflows, flow_nodes, executions, records |
| Project Management | Full application | collections-and-fields, record-operations, workflow-automation, data-visualization | Advanced | collections, fields, workflows, charts, records |
| Multi-Language Setup | Localization | localization, system-admin | Beginner | localization, localizationTexts, localizationTranslations, app |

## How to Use These Scenarios

1. **Ensure your setup is verified** -- Run the **setup** skill checks first to confirm API connectivity and authentication.
2. **Follow steps in order** -- Each scenario builds on previous steps. Do not skip ahead.
3. **Replace placeholder values** -- All examples use `${NOCOBASE_URL}` and `${NOCOBASE_API_KEY}`. These are populated from your plugin configuration.
4. **Check responses** -- Each step includes expected response patterns. If you see errors, consult the **troubleshoot** skill.
5. **Clean up after testing** -- The scenarios create real data. Use the destroy endpoints to clean up test collections and records when done.

## Combining Scenarios

For a comprehensive NocoBase setup, work through the scenarios in this order:

1. **Multi-Language Setup** -- Configure languages before creating collections so names are translatable from the start.
2. **CRM Collections** -- Build the data model with collections, fields, and relationships.
3. **Workflow Automation** -- Add business logic on top of the data model.

After completing all three, you will have a multilingual CRM with automated task creation -- a foundation for many business applications.
