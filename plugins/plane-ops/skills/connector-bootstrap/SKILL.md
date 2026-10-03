---
name: connector-bootstrap
description: MUST be consulted at the start of ANY Plane-related request before answering the user or declaring tools unavailable. Discovers Plane tools across any MCP server, connector, or instance naming convention - the resource tools of Plane MCP 0.3.0 and later (one tool per resource with an `action` parameter) as well as legacy per-operation tools - and translates the legacy action names the other skills use into resource calls. Use when the user mentions sprint, backlog, work item, cycle, epic, module, milestone, initiative, project, issue, ticket, task, standup, retro, estimate, roadmap, board, Plane, or any work-management operation, even if Plane tools are not visible yet. Also use before saying "I don't have access to Plane tools" or "tool not available".
---

# Plane Connector Bootstrap

This skill ensures Plane tools are reliably discovered in any environment: cowork mode, remote MCP, local MCP, Claude connectors, custom proxies, or self-hosted instances. Tool names vary by environment and by server version - **never assume tools are missing without probing first**.

## Two Tool Surfaces

| Surface | Where you meet it | Tool shape |
|---------|-------------------|------------|
| **Resource tools** (current) | Official Plane MCP server 0.3.0 and later (hosted or `uvx plane-mcp-server`) | One tool per resource - `workitem`, `cycle`, `module`, `page`, ... - and an `action` parameter selects the operation: `cycle(action="list", project_id=...)` |
| **Per-operation tools** (legacy) | Servers before 0.3.0 and other connectors | One tool per operation: `list_cycles`, `create_work_item`, ... |

The marker of the resource surface is a tool named `workitem` (or `cycle`) whose schema has an `action` enum. On the official server the old per-operation names are still callable as hidden aliases, but they are **not advertised**: a probe for `create_cycle` or `list_work_items` returns nothing there, and an agent that only probes legacy names wrongly concludes that Plane is not connected.

The other plane-ops skills and commands still describe operations with legacy action names (`create_cycle`, `add_work_items_to_cycle`, ...). Resolve every one of them through the translation table below.

## Why This Skill Exists

In cowork mode and certain remote setups, MCP/connector tools are **deferred**: Claude only sees their names in a system reminder until `ToolSearch` loads their schemas. A user request mentioning "sprint" or "work item" may arrive before the Plane tools are materialized into the tool set. **You must probe before refusing.**

Symptoms this skill prevents:
- Responding "I don't have access to Plane tools" when they are in fact available as deferred tools.
- Probing only legacy names and missing the resource tools of Plane MCP 0.3+.
- Missing tools because the server name differs (`mcp__plane__*`, `mcp__<any>__plane-i-*`, `plane_*`, `connector-plane-*`, or fully custom).
- Only finding tools for one instance when multiple Plane workspaces are connected.

## Mandatory Bootstrap Protocol

Execute these steps **before** answering any Plane-related user request.

### Step 1 - Probe with ToolSearch

Start with the probes that find the resource surface, and do not stop at the first empty result:

```
ToolSearch(query="plane", max_results=20)
ToolSearch(query="workitem cycle module", max_results=20)
```

If either returns tools named `...__workitem`, `...__cycle`, `...__project`, you are on the resource surface: note the server segment of the name, then load the schemas you need with the `select:` form:

```
ToolSearch(query="select:mcp__<server>__workitem,mcp__<server>__cycle,mcp__<server>__project", max_results=10)
```

Fallback for older servers and other connectors - probe the legacy per-operation names:

```
ToolSearch(query="work_item cycle project", max_results=20)
ToolSearch(query="list_projects create_work_item", max_results=20)
ToolSearch(query="sprint backlog issue", max_results=20)
```

If the user mentioned a specific concept, add a targeted query:

```
ToolSearch(query="+module", max_results=10)
ToolSearch(query="+milestone", max_results=10)
ToolSearch(query="+initiative", max_results=10)
ToolSearch(query="+intake", max_results=10)
ToolSearch(query="+page", max_results=10)
```

There is no epic tool on any surface of the official server: an epic is a `workitem` whose type is named "Epic" (see the table).

### Step 2 - Match by Resource Name, Then by Action Suffix

**Resource surface.** The tool name is `mcp__<server>__<resource>`; the operation goes into the `action` parameter. The server segment is whatever the user named their connection (`plane`, `plane-cloud`, `mcp__plugin_...`): never hardcode it. Resource names:

`workitem`, `cycle`, `module`, `milestone`, `initiative`, `intake`, `state`, `label`, `member`, `page`, `project`, `workspace`, `work_log`, `workitem_type`, `workitem_property`, `workitem_relation`, `workitem_comment`, `workitem_link`, `workitem_activity`, `workitem_attachment`, `project_estimate`, `release`, `release_tag`, `release_label`, `customer`, `customer_property`, `customer_request`, `collection`, `template`, and `get_pql_reference` (no `action`).

Every tool's own description lists its actions with their required and optional parameters. That generated description is the authoritative reference at call time - read it before the first call on a resource.

**Legacy surface.** Tools may appear under **any** of these shapes (non-exhaustive):

- `mcp__<provider>__<prefix>-<action>`
- `mcp__<instance-slug>__<action>`
- `plane_<action>`, `connector_plane_<action>`, `<workspace>-plane-<action>`
- A fully custom name chosen by the connector author

**Match legacy tools by the action suffix** (e.g., `create_cycle`, `list_work_items`). The prefix is environment-dependent and MUST NOT be hardcoded in this plugin or in your responses.

### Step 3 - Handle Multiple Instances

If the user has multiple Plane workspaces/instances connected, `ToolSearch` will return several tools with the same resource or action name but different server segments. In that case:

1. List the discovered instances to the user by their server segment/slug.
2. Ask which instance to operate on (use `AskUserQuestion` if available).
3. Remember the chosen instance for the rest of the conversation.
4. If only one instance matches, proceed without asking.

### Step 4 - Cache Discovered Names for the Session

Once you have resolved the actual tool names, keep them in working memory for the remainder of the conversation. Do **not** re-probe for every call in the same session unless the user switches instances or a call fails with "tool not found".

### Step 5 - Only Then Decide Whether Tools Are Missing

You may conclude "Plane tools are not connected" **only after** Steps 1-3 return no matches across all query variants. When reporting this to the user, say what you probed and suggest how to connect Plane (see "How to Connect Plane" below).

## Translation Table - Legacy Action Names to Resource Calls

The first column holds the action names that the other plane-ops skills and commands use. On the resource surface call the second column. Names marked with an asterisk were never part of the official 177 per-operation tools, so they do not work even as hidden aliases: always translate them.

| Legacy name used in this plugin | Resource call |
|---|---|
| `list_projects` / `retrieve_project` / `create_project` / `update_project` / `delete_project` | `project(action=list\|retrieve\|create\|update\|delete)`; `list` is paginated: `per_page` in, `next_cursor` out - follow it |
| `get_project_features`\* / `update_project_features` | `project(action=get_features\|update_features)` |
| `get_workspace_features`\* / `update_workspace_features` | `workspace(action=get_features\|update_features)` |
| `get_me` / `get_workspace_members` / `get_project_members` | `member(action=me\|list_workspace\|list_project)` |
| `get_project_worklog_summary` | `project(action=worklog_summary)` |
| `list_work_items` / `search_work_items` / `retrieve_work_item` / `retrieve_work_item_by_identifier` / `create_work_item` / `update_work_item` / `delete_work_item` | `workitem(action=list\|search\|retrieve\|retrieve_by_identifier\|create\|update\|delete)`; the id parameter is `workitem_id` (not `work_item_id`); filter with `pql` (call `get_pql_reference` for the syntax); also `count`, `list_archived`, `archive`, `manage_assignee`, `manage_label` |
| `list_cycles` / `retrieve_cycle` / `create_cycle` / `update_cycle` / `delete_cycle` | `cycle(action=list\|retrieve\|create\|update\|delete)`; `create` needs `owned_by` (a member id) |
| `list_cycle_work_items` / `transfer_cycle_work_items` | `cycle(action=list_workitems\|transfer_workitems, new_cycle_id=...)` |
| `add_work_items_to_cycle`\* / `remove_work_item_from_cycle`\* | `cycle(action=manage_workitems, add_ids=[...] \| remove_ids=[...])` |
| `list_archived_{cycles,modules}`\*, `archive_cycle`\*, `unarchive_cycle`\* | `cycle(action=list, archived=true)`; `cycle(action=archive\|unarchive)`; plus `cycle(action=complete)` which sets the end date to today |
| `list_modules` / `retrieve_module` / `create_module` / `update_module` / `delete_module` | `module(action=list\|retrieve\|create\|update\|delete)` |
| `add_work_items_to_module`\* / `remove_work_item_from_module`\* / `list_module_work_items` | `module(action=manage_workitems, add_ids\|remove_ids)` / `module(action=list_workitems)` |
| `archive_module`\* / `unarchive_module`\* | `module(action=archive\|unarchive)`; list archived with `module(action=list, archived=true)` |
| `list_milestones`, `create_milestone`, ..., `add_work_items_to_milestone`\*, `remove_work_items_from_milestone`\*, `list_milestone_work_items` | `milestone(action=list\|retrieve\|create\|update\|delete\|list_workitems\|manage_workitems)` |
| `list_initiatives`, `create_initiative`, ..., `add_epic_to_initiative`\* | `initiative(action=list\|retrieve\|create\|update\|delete\|list_projects\|add_projects\|remove_projects\|list_workitems\|manage_workitems)`; attach an epic with `manage_workitems, add_ids=[<epic work item id>]` |
| `list_epics`\* / `create_epic`\* / `update_epic`\* / `retrieve_epic`\* / `delete_epic`\* | No epic tools. `workitem_type(action=resolve, project_id, name="Epic")` returns the `type_id`; `workitem(action=create, ..., type_id=<id>)` creates the epic; list with `workitem(action=list, pql='type = "<type-id>"')`; children use the `parent` field; update, retrieve and delete use the plain `workitem` actions |
| `list_states` / `create_state` / `update_state` / `delete_state` / `retrieve_state` | `state(action=...)` |
| `list_labels` / `create_label` / `update_label` / `delete_label` / `retrieve_label` | `label(action=...)` |
| `list_work_item_relations` / `create_work_item_relation` / `remove_work_item_relation` | `workitem_relation(action=list\|create\|delete)`; also `list_definitions`, `create_definition`, `update_definition`, `delete_definition` |
| `list_work_item_comments` / `create_...` / `update_...` / `delete_...` / `retrieve_...` | `workitem_comment(action=...)` |
| `list_work_item_links` / `create_...` / `update_...` / `delete_...` / `retrieve_...` | `workitem_link(action=...)` |
| `list_work_logs` / `create_work_log` / `update_work_log` / `delete_work_log` | `work_log(action=...)` |
| `list_work_item_types` / `create_...` / `update_...` / `retrieve_...` / `delete_...` | `workitem_type(action=list\|create\|update\|retrieve\|delete\|resolve\|import_to_project)` |
| `list_work_item_properties` / `create_...` / `update_...` / `retrieve_...` / `delete_...` | `workitem_property(action=...)`; options and values via `list_options`, `create_option`, `get_value`, `set_value`, ... |
| `list_work_item_activities` / `retrieve_work_item_activity` | `workitem_activity(action=list\|retrieve)` |
| `list_intake_work_items` / `create_...` / `retrieve_...` / `update_...` / `delete_...` | `intake(action=...)`; `update` takes `status` for the triage decision |
| `create_project_page`\* / `create_workspace_page`\* / `retrieve_project_page`\* / `retrieve_workspace_page`\* | `page(action=create\|retrieve, ...)`; omit `project_id` for a workspace page; `page` also has `list`, `update`, `archive`, `delete`, `set_collection`, `attach_to_workitem` |

Resources without a legacy name in this plugin: `release`, `release_tag`, `release_label` (release notes), `project_estimate` (estimate points), `workitem_attachment`, `customer*`, `collection`, `template`.

### Calling Conventions of the Resource Surface

- **Scope.** Supply `project_id` for a project's own set; omit it to address the workspace (`workitem list`, `workitem count`, `page`, `state`, `workitem_type`). A wrong scope still succeeds against the other scope, so check which one you meant.
- **Declared parameters only.** Parameters are validated against the action's declared set; an extra or misspelled parameter is an error, not a silent drop. When a call is rejected, re-read the tool description rather than guessing.
- **Plural actions.** `manage_workitems` takes `add_ids` and/or `remove_ids`, returns nothing, and is read back with `list_workitems`.
- **Archive and delete.** `archive` is an action (not a flag); `delete` is permanent. The plugin's PreToolUse hook asks for confirmation on delete-type actions.

## How to Connect Plane

The plugin ships no MCP server; the user connects Plane one of these ways:

| Way | Command or setting |
|---|---|
| Hosted, OAuth (recommended for interactive use) | `claude mcp add --transport http plane https://mcp.plane.so/http/mcp`, then run `/mcp` in a session and authenticate |
| Hosted, personal access token (CI, headless, shared setups) | URL `https://mcp.plane.so/http/api-key/mcp` with headers `Authorization: Bearer ${PLANE_PAT}` and `x-workspace-slug: <workspace-slug>`; the older `x-api-key` header no longer works |
| Self-hosted Plane or offline (stdio) | `uvx plane-mcp-server stdio` with `PLANE_API_KEY`, `PLANE_WORKSPACE_SLUG`, and `PLANE_BASE_URL` for the self-hosted URL |

The hosted server cannot reach private self-hosted instances, and its OAuth flow is not available on Plane Community Edition; use stdio there. The SSE endpoint and the npm package `@makeplane/plane-mcp-server` are deprecated.

## Refusal Policy (Hard Rule)

Before you output any message that says or implies "I don't have Plane tools", "I can't access Plane", "tool not available", or "Plane is not connected":

1. You MUST have run at least **four** distinct `ToolSearch` queries, including `plane` and `workitem cycle module`, and covering the domains relevant to the user's request.
2. You MUST have attempted the `select:` form at least once - for the resource tools (`mcp__<server>__workitem`) if a server segment is known, otherwise for a legacy name such as `select:list_projects`.
3. You MUST have tried at least one legacy per-operation probe (`list_projects create_work_item`) in addition to the resource probes.
4. If the user's request involves multiple domains (e.g., sprint + backlog + work items), you MUST probe each.

Only then is a refusal justified - and it should include the list of probes you ran and the connection options above.

## Integration with Other Skills

All other plane-ops skills reference legacy action names (e.g., `create_cycle`). Resolve those through this bootstrap protocol once per session: find the tools, then translate each legacy name with the table above when the connected server is on the resource surface. Every skill assumes that, by the time its logic runs, the actual tool names for the current instance have been discovered.
