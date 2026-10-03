---
name: work-items
description: Work item operations in Plane — create, read, update, delete, search, assign, label, link, comment, relate, and log time on work items (issues/tasks/tickets). Use when the user wants to create a task, update an issue, add a comment, attach a label, link a PR, set a blocker, log work time, or inspect a specific item. Covers work item types, custom properties, and multi-item batch edits.
---

# Work Items

This skill covers the full life of a work item in Plane: creation, inspection, updates, relations, comments, links, labels, work logs, and custom properties.

## Tool Name Resolution

Tools below are referenced by their **legacy action name** (`create_work_item`, ...). Resolve real tool names through the `connector-bootstrap` skill. On Plane MCP 0.3.0 and later the same operation is a resource tool with an `action` parameter — `create_work_item` is `workitem(action="create", ...)`, `create_work_item_relation` is `workitem_relation(action="create", ...)` — and `connector-bootstrap` has the full translation table. Never assume a server prefix.

## Field Names — Official Server vs Legacy Connectors

On the official Plane MCP server (0.3.0 and later) the `workitem` tool has **fixed** parameter names and validates every call against the declared set (an unknown parameter is an error, not a silent drop):

| Concept | Parameter |
|---------|-----------|
| Work item id | `workitem_id` (not `work_item_id`) |
| State UUID | `state` |
| Label UUIDs | `labels` |
| Assignees | `assignees` |
| Points | `point` or `estimate_point` |
| Parent | `parent` |
| Work item type | `type_id` |
| Priority | `priority` |
| Description | `description_html` |

The legacy-form code samples below keep the legacy id name `work_item_id`; on the resource surface write `workitem_id` and use the field names above. Legacy per-operation connectors and older bridges may use other variants (`state_id`, `label_ids`, `parent_id`, `type`, `work_item_id`); on those, inspect the actual tool schema (the MCP tool's JSON Schema) before the first mutation on a new instance and use the schema's names — the skill's logic still applies. The hidden legacy aliases of the official server keep their original parameter names (`work_item_id`), but prefer the resource tools.

## Available Actions

| Action | Purpose |
|--------|---------|
| `list_work_items` | List items in a project (filter, sort, paginate) |
| `search_work_items` | Full-text search across a project |
| `create_work_item` | Create a new work item |
| `retrieve_work_item` | Get an item by UUID |
| `retrieve_work_item_by_identifier` | Get an item by human identifier (e.g. `PROJ-42`) |
| `update_work_item` | Update any field (state, points, priority, assignees, description) |
| `delete_work_item` | Delete an item |
| `list_work_item_comments` / `create_work_item_comment` / `update_work_item_comment` / `delete_work_item_comment` | Comment operations |
| `list_work_item_links` / `create_work_item_link` / `delete_work_item_link` | External links (PRs, docs, designs) |
| `list_work_item_relations` / `create_work_item_relation` / `remove_work_item_relation` | Blocked-by / blocks / duplicates / relates-to |
| `list_work_item_activities` / `retrieve_work_item_activity` | Audit trail |
| `list_work_logs` / `create_work_log` / `update_work_log` / `delete_work_log` | Time tracking |
| `list_work_item_types` / `create_work_item_type` | Custom types (bug, story, task, spike) |
| `list_work_item_properties` / `create_work_item_property` | Custom fields |
| `list_labels` / `create_label` | Labels |
| `list_states` | Resolve state UUIDs for filtering/updating |

## Creating a Work Item

```
1. connector-bootstrap       → resolve tool names and instance
2. list_projects             → pick project_id
3. list_states({ project_id }) → map target state to UUID
4. list_labels({ project_id })  → map labels to UUIDs (optional)
5. get_project_members({ project_id }) → resolve assignee UUIDs
6. create_work_item({
     project_id,
     name,
     description_html,           // with acceptance criteria
     priority,                   // urgent | high | medium | low | none
     point,                      // Fibonacci 1..8 (see agile-fundamentals)
     state,                      // UUID from list_states (some instances: state_id)
     assignees,                  // UUID[]
     labels,                     // UUID[] (some instances: label_ids)
     type_id                     // optional custom type (some instances: type)
   })
```

### Description Template

```html
<h3>Context</h3>
<p>Why this matters, links to related work.</p>

<h3>Acceptance Criteria</h3>
<ul>
  <li>Given … when … then …</li>
  <li>Given … when … then …</li>
</ul>

<h3>Out of Scope</h3>
<ul>
  <li>Explicit exclusions</li>
</ul>

<h3>Notes</h3>
<p>Implementation hints, open questions.</p>
```

## Updating a Work Item

Always resolve IDs first. Typical updates (legacy form shown; on the resource surface use `workitem(action="update", project_id, workitem_id, ...)` with the same fields):

```
update_work_item({ project_id, work_item_id, state })        // move state (or state_id)
update_work_item({ project_id, work_item_id, point })        // estimate
update_work_item({ project_id, work_item_id, priority })     // re-prioritize
update_work_item({ project_id, work_item_id, assignees })    // reassign
update_work_item({ project_id, work_item_id, labels })       // relabel (or label_ids)
```

Batch updates: loop over items; do not call in parallel if the tool is not idempotent by default — check the tool schema.

## Relations (Blockers, Duplicates, Relates-to)

```
workitem_relation(action="create",              // legacy: create_work_item_relation
  project_id,
  workitem_id,
  workitem_ids: ["<other_uuid>"],               // list of related work item UUIDs
  relation_type: "blocking" | "blocked_by" | "start_before" | "start_after" | "finish_before" | "finish_after"
)
```

**Field name notes (official server):** the related items go in `workitem_ids` (array of UUID strings), and the relation is one of six built-in dependency types. Other relationships — duplicate, relates-to and any workspace-defined custom relation — are *definitions*: call `workitem_relation(action="list_definitions")`, match the user's wording to an entry, and pass `relation_definition_id` plus `relation_definition_label` (the matched outward or inward label, which sets the direction) instead of `relation_type`. To remove a relation use `workitem_relation(action="delete", project_id, workitem_id, related_workitem_id, is_dependency)`; `is_dependency` must match the kind that was created.

**Legacy connectors:** the parameter for the related items is usually `issues` (array, plural) with `work_item_id` as the id — not `related_issue` (singular). Some MCP bridges expose it as an array of objects `[{ id }]` instead of an array of UUID strings. If you get a validation error, check the schema and the serialization format that the bridge expects (some bridges require the array to be a JSON-encoded string rather than a native list).

Before adding an item to a sprint, always check that it has no unresolved `blocked_by` relations — see `agile-fundamentals` Definition of Ready.

## Comments and Links

- **Comments** use `comment_html` (not `description_html`) on most Plane deployments. The body accepts the same HTML subset as work item descriptions. Check your instance's schema for the exact field name.
- **Links** are external URLs (`http://` or `https://`). On the official server (0.3.0 and later) `workitem_link(action="create")` and `update` accept both **`url` and `title`**; the title is the text Plane shows in place of the URL (without one, the URL itself is shown). Some legacy connectors accept `url` only: the title is then auto-extracted from the target page's OpenGraph/`<title>` tag and stored in a server-populated `metadata` field, and a custom title is not possible.

```
workitem_link(action="create",                 // legacy: create_work_item_link
  project_id,
  workitem_id,
  url: "https://github.com/org/repo/pull/420",
  title: "PR #420: fix login redirect"          // optional; omit on legacy connectors that reject it
)
```

## Work Logs (Time Tracking)

```
create_work_log({
  project_id,
  work_item_id,
  description,
  duration      // integer — usually minutes (e.g., 150 for 2h 30m)
})
```

**Field name notes:** `duration` is typically an **integer representing minutes**, NOT an ISO 8601 string like `"PT2H30M"`. Before the first log on a new instance, check the schema — some bridges may use seconds instead of minutes, or accept ISO 8601. Convert user input accordingly:

- "2h 30m" → 150 (minutes) or 9000 (seconds)
- "PT2H30M" → parse with a duration library, then convert

The project must have `is_time_tracking_enabled: true`, otherwise the call will fail. Check via `retrieve_project({ project_id })`.

Use to compare estimated story points vs actual time (see `velocity-metrics`).

## Searching and Filtering

### Human identifier lookup

```
retrieve_work_item_by_identifier({
  project_identifier: "PROJ",   // short project slug, NOT the project_id UUID
  issue_identifier: 42           // integer sequence number, NOT the full "PROJ-42" string
})
```

The identifier is split into two arguments: the project's short slug and the integer sequence number. Do not pass "PROJ-42" as a single string — parse it first.

### Full-text search

```
search_work_items({ query: "login bug" })
```

Important: `search_work_items` is typically **workspace-scoped**, not project-scoped. The parameter name is usually `query` (not `q`). The result is a search object containing matching work items across the whole workspace — filter by project client-side if needed. Check the real tool schema for the exact parameter and response shape.

### Filtered list

```
list_work_items({ project_id, order_by, cursor, per_page, expand, fields })
```

Filtering by state/assignee/priority is often not a direct parameter — you pass `project_id` and then filter the returned list client-side, or use `expand` / `fields` to narrow the payload. Common `order_by` values: `-priority`, `-created_at`, `point`, `target_date`. Check the schema for supported filter params on your instance.

## Custom Types and Properties

If the project uses custom work item types (Bug, Story, Spike, Task, Epic-sub):

```
list_work_item_types({ project_id }) → find type_id
create_work_item({ ..., type_id })
```

Custom properties (e.g. "Customer impact", "RICE score"):

```
list_work_item_properties({ project_id, type_id }) → find property_id and allowed values
update_work_item({ project_id, work_item_id, properties: { <property_id>: <value> } })
```

Check the tool schema for the exact field name — it may be `properties`, `custom_properties`, or similar.

## Best Practices

1. Always fill acceptance criteria before estimating.
2. Never assign points > 8 — decompose instead.
3. Link the PR as soon as it opens; link the deploy as soon as it ships.
4. Log actual time on items with estimates > 3 points to calibrate future estimation.
5. When closing a blocker, also verify the downstream items it was blocking.
6. Use labels sparingly — they should reflect meaningful categories, not tags for everything.

## Known Limitations (Bridge / Environment Specific)

Some MCP bridges for Plane have issues serializing list-typed parameters. This affects:
- `create_work_item_relation` → `issues` array
- `add_work_items_to_cycle` → `issue_ids` array
- `add_work_items_to_module` → `issue_ids` array
- `add_work_items_to_milestone` → `issue_ids` array
- `create_intake_work_item` → `data` dict

Symptom: the tool rejects the call with `Input should be a valid list` or `Input should be a valid dictionary` even when you pass a correctly structured value. This is a **bridge-level bug**, not a content bug in the skill.

**Workarounds:**
1. Try passing the array as a JSON-encoded string first — some bridges decode it.
2. Try the plain native list form next.
3. If both fail, do the operation in the Plane UI or via a direct REST call, and document the limitation for the user.
4. Some bridges accept an array of objects (`[{id: "uuid"}]`) instead of an array of strings.

**Other observed limitations:**
- Legacy connectors: `archive_cycle` / `archive_module` may return HTTP 400 for active cycles/modules; archive then requires a non-active state first (typically "completed" or past `end_date`). On Plane MCP 0.3.0 and later `cycle(action="archive")` ends a still-running cycle first, so it succeeds, but it cuts the sprint short — run `complete` and `transfer_workitems` first (see `/close-sprint`). For modules, check the behavior on your instance. To remove a cycle or module entirely use the `delete` action, after confirmation.
- `update_module` often returns a stub response with null fields even when the update succeeded. Refetch via `retrieve_module` to get the post-update state.
- `update_work_item_link` on legacy connectors supports changing `url` but not arbitrary metadata; on the official server `workitem_link(action="update")` takes `url` and/or `title`.
