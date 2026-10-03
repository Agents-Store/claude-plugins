# LEARNINGS.md

Accumulated fixes and discoveries for the `plane-ops` plugin. Append entries chronologically (newest first). Format:

```
## [DATE] — [skill-name]: Brief description

**Problem:** What went wrong
**Fix:** What was changed
**Root cause:** Why the original was wrong
**Severity:** Critical / Major / Minor
```

## 2026-10-03 — all skills, commands, agents, hooks: 2.0.0 speaks the Plane MCP resource tools natively (breaking)

**Problem:** Plane MCP 0.3.0 replaced 177 per-operation tools (`list_cycles`, `create_work_item`, `add_work_items_to_cycle`, `create_epic`, ...) with 30 resource tools that take an `action` parameter (`cycle(action="list")`). The plugin still wrote every call in the old names, so on a current server the connector probe reported Plane as not connected, the destructive-action guard matched only `delete_*` and silently stopped firing, and the PreToolUse `prompt` hook could only answer ok/not-ok, so a Plane delete was either denied for good or never asked about. Epics, filtering and aggregates were done client-side because the plugin did not know PQL, `workitem(action=count, group_by=...)`, releases or `project_estimate`.
**Fix:** 2.0.0 rewrites all 17 skills, 44 commands, 2 agents and the evals to `resource(action=..., params)` with the parameter names the server declares (`workitem_id`, `state`, `labels`, `add_ids`, ...); 1061 calls were checked against the `ACTIONS` declarations of plane-mcp-server 0.3.3 (0 undeclared actions or parameters). Epics are work items of the type "Epic" (`workitem_type(action=resolve, name="Epic")`, then `workitem(action=create, type_id=...)`); PQL replaces client-side filtering in backlog, find, my-work, standup, health and velocity; `workitem(action=count, group_by=...)` gives burndown, velocity, WIP, throughput and taxonomy aggregates (counts are items, not points, so every `fields=` list that sums points also fetches `estimate_point`); release notes come from `release` / `get_changelog`. `connector-bootstrap` probes the resource tools first and keeps the legacy names only as a fallback table for servers older than 0.3.0. The guard is now a stdlib `command` hook (`hooks/plane_guard.py`) that answers `permissionDecision: "ask"` for delete, `remove_projects`, detach and for `manage_workitems` calls that take work items out of a container (`remove_ids` for cycle, module, milestone, initiative and release, `unlink_ids` for customer), with a test suite (`hooks/test_plane_guard.py`, 24 tests) that also pins its table of destructive actions to the server's. Behaviours the plugin could not verify (intake `status=1` becoming a backlog item, the `snoozed_till` / `duplicate_to` formats, `blocks()` direction, `isEpic()`, "deleting an epic keeps its children") are labelled "per the tool description, confirm on your instance". Breaking: the per-operation names are gone from the text, so older connectors work through the fallback table only.
**Root cause:** The plugin followed a server surface that changed shape underneath it, and nothing tied its text to the server's tool declarations. The first guard fix tested a customer removal with `remove_ids`, a parameter `customer(action=manage_workitems)` rejects (it declares `link_ids` / `unlink_ids`), so the test passed against an input the real server never accepts.
**Severity:** Critical
