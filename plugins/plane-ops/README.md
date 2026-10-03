# plane-ops

Agile operations knowledge plugin for [Plane](https://plane.so). Agile workflows on top of the Plane MCP server: sprint planning, backlog management, estimation, retrospectives, daily standups, work items, labels/states/types/properties, pages (sprint reports, retros, ADRs, runbooks, specs), roadmaps, dependencies, and more.

**Compatibility:** written for Plane MCP 0.3.0 and later — one tool per resource with an `action` parameter, for example `cycle(action="list")`. Servers older than 0.3.0 and other per-operation connectors (`list_cycles`, `create_work_item`, ...) still work through the fallback table in the `connector-bootstrap` skill, which translates each resource call into the connector's own tool names.

**Current version: 2.0.0** — a native rewrite: every skill, command and agent speaks the resource tools (`workitem`, `cycle`, `module`, `milestone`, `initiative`, `intake`, `page`, ...) instead of the per-operation names of earlier versions, which is a breaking change for anyone who relied on the old wording. It uses **PQL** (Plane Query Language) filters and `workitem(action=count, group_by=...)` aggregates instead of client-side filtering, writes epics as work items of the type "Epic" (the server has no epic tools), builds release notes from **Plane releases** (`release`, `get_changelog`), reads and writes estimate scales with `project_estimate`, and uses the real intake statuses (accept, decline, snooze, duplicate). 1.4.0 added the compatibility layer, the `connector-bootstrap` probes for the resource tools and the destructive-operation hook; 1.3.0 added 22 commands, the `labels-states-properties` skill, 5 page templates and the safety hooks.

## What this plugin does

Teaches Claude **how** to run Agile ceremonies and work with Plane entities — sprints (cycles), backlog, work items, modules, epics, initiatives, milestones, intake triage, pages, and more. It does not ship any MCP server; it works with whatever Plane integration the user already has connected.

## Design — tool-agnostic knowledge plugin

This plugin ships **no MCP server**, **no `.mcp.json`**, and **no hardcoded server name or tool prefix**. It is a pure knowledge/ops plugin.

Users may have Plane connected in any of these ways:

- A Claude connector
- A user-level `.mcp.json` pointing at a remote MCP server
- A project-level `.mcp.json` pointing at a self-hosted or cloud Plane instance
- A Cowork/remote MCP bridge
- Multiple Plane workspaces connected simultaneously

The plugin handles all of these through a dedicated `connector-bootstrap` skill that discovers Plane tools via `ToolSearch` at the start of any Plane-related request, matches resource tools (`workitem`, `cycle`, ...) by name and legacy tools by action suffix (never by server prefix), and supports multi-instance environments by asking the user which Plane workspace to operate on when multiple are detected.

Every other skill and command writes operations as resource calls (`project(action=list)`, `cycle(action=manage_workitems, add_ids=[...])`, `workitem(action=list, pql='...')`) and delegates tool resolution to `connector-bootstrap`. The plugin content never mentions any specific MCP server name or tool prefix.

## Components

### Skills

- **connector-bootstrap** — forcer skill that runs before any Plane operation; probes `ToolSearch` for the resource tools of Plane MCP 0.3+ (and, as fallback, for per-operation tools of older servers, which it translates with a table), explains the calling conventions (scope, declared parameters, pagination, PQL), and handles multi-instance setups
- **agile-fundamentals** — single source of truth for formulas (capacity, WSJF, WIP), Definition of Ready/Done, MoSCoW mapping, Fibonacci scale, sprint buffer policy
- **sprint-planning** — full planning ceremony: capacity, velocity, selection, cycle creation
- **work-items** — CRUD, PQL filters and counts, relations, comments, links, work logs, custom types and property values; the fixed field names of the official server
- **modules** — feature/workstream grouping that spans multiple sprints
- **epics-initiatives-milestones** — long-horizon planning above sprints (epics are work items of the type "Epic"; initiatives and milestones have their own tools)
- **backlog-management** — MoSCoW, WSJF scoring, grooming, backlog health with server-side PQL filters and counts
- **task-decomposition** — INVEST criteria, vertical slicing, epic → story breakdown
- **estimation** — story points, planning poker, Fibonacci, t-shirt sizing, and the project estimate system (`project_estimate`)
- **velocity-metrics** — velocity, burndown, WIP limits, cycle time, throughput (aggregates with `workitem(action=count, group_by=...)`)
- **daily-standup** — progress summary, blocker detection, async standups
- **sprint-review-retro** — review, retrospective formats, action item tracking
- **project-setup** — bootstrapping a new Agile-ready project
- **intake-triage** — triaging incoming requests into the backlog
- **labels-states-properties** — taxonomy design: when to use labels vs work item types vs custom properties, state group rules, naming conventions, quarterly audit workflow
- **pages-publishing** — publishing sprint reports, retros, release notes (from Plane releases and their changelog), ADRs, runbooks, specs, meeting notes, roadmap pages; includes HTML templates, list-rendering gotchas, and verified workarounds for Plane editor quirks
- **examples** — end-to-end workflow references, tool-call patterns, everyday command scenarios

### Commands (44 total)

**Sprint lifecycle:** `/plan-sprint`, `/create-sprint`, `/sprint-status`, `/close-sprint`, `/burndown`, `/standup`, `/retro`, `/velocity`, `/cycles`

**Work items:** `/work-item`, `/find`, `/my-work`, `/assign`, `/comment`, `/link`, `/log-time`, `/relate`, `/history`, `/bulk-update`

**Backlog & grooming:** `/groom-backlog`, `/backlog-health`, `/wsjf-prioritize`, `/estimate`, `/decompose`, `/dependencies`, `/triage-intake`

**Long-horizon planning:** `/create-module`, `/module`, `/create-epic`, `/epic`, `/create-milestone` (via `/milestone`), `/milestone`, `/milestone-status`, `/initiative`, `/roadmap`

**Taxonomy & config:** `/label`, `/state`, `/work-item-type`, `/property`

**Publishing & pages:** `/publish-report`, `/page`

**Project & workspace:** `/setup-project`, `/projects`, `/members`, `/whoami`

### Agents

- **plane-agile-coach** — general Agile guidance across all ceremonies
- **plane-sprint-planner** — specialized sprint creation and capacity planning

### Hooks

- `SessionStart` — a `command` hook that prints `hooks/session-start.txt`, a silent reminder to consult `connector-bootstrap` if the session will involve Plane (a `prompt` hook cannot run on `SessionStart`, so it is a command hook)
- `PreToolUse` — a `command` hook (`hooks/plane_guard.py`, Python standard library only) for Plane tools: the resource tools of Plane MCP 0.3+ (`mcp__<server containing "plane">__cycle`, `__workitem`, `__page`, ...) and that server's per-operation `delete_*` / `remove_*` / `detach_*` / `archive_*` tools. It reads the `action` of the call. Delete-type actions (`delete`, `remove_projects`, `remove_page`, `remove_member`, `detach`, `detach_from_workitem`, `delete_point`, `delete_option`, `delete_value`, `delete_definition`) and `manage_workitems` calls that carry `remove_ids` (taking work items out of a cycle, module, milestone, initiative or release) prompt for confirmation through Claude Code's permission dialog, which names the resource, the ids and what is lost; `archive` adds a warning to Claude's context (and how to restore) without a prompt; every other action, and every tool of a server whose name does not contain `plane`, passes silently. The guard fails open on malformed input and does not watch for bulk updates. It guards servers whose name contains `plane` (rename your connection accordingly, or edit the matcher in `hooks/hooks.json`). Run its tests with `python3 -m unittest discover -s hooks -v` from the plugin directory.

## Prerequisites

A working Plane integration in your Claude environment. Recommended connection methods for the official Plane MCP server (0.3.0 and later):

| Method | Command or setting |
|---|---|
| Hosted, OAuth | `claude mcp add --transport http plane https://mcp.plane.so/http/mcp`, then `/mcp` in a session to authenticate |
| Hosted, personal access token (CI, headless) | URL `https://mcp.plane.so/http/api-key/mcp` with headers `Authorization: Bearer ${PLANE_PAT}` and `x-workspace-slug: <workspace-slug>` (the older `x-api-key` header no longer works) |
| Self-hosted Plane (stdio) | `uvx plane-mcp-server stdio` with `PLANE_API_KEY`, `PLANE_WORKSPACE_SLUG` and `PLANE_BASE_URL` |

The hosted server cannot reach private self-hosted instances, and OAuth is not available on Plane Community Edition: use stdio there. The SSE endpoint and the npm package `@makeplane/plane-mcp-server` are deprecated. A Plane connector registered with Claude, another `.mcp.json` entry, or a Cowork-provided Plane bridge also work; per-operation connectors from before 0.3.0 work through the fallback table in `connector-bootstrap` (without PQL, counts or releases).

If you do not have Plane connected, the `connector-bootstrap` skill will tell you which `ToolSearch` probes it ran and suggest how to connect Plane. It will not silently refuse.

## Multi-instance support

If you have more than one Plane workspace connected (for example, a cloud workspace for work and a self-hosted workspace for personal projects), the plugin detects this during bootstrap and asks you which instance to operate on. Tell it once per session and it remembers the choice until you ask to switch.

## Cleanup limitations you should know

- **Pages can be updated, archived and deleted.** `page(action=update)` replaces the whole `description_html` body (retrieve the page first), `archive` hides it, and `delete` works only on an archived page. Per-operation connectors from before 0.3.0 often expose only create and retrieve for pages; there, edits happen in the Plane web UI. The `pages-publishing` skill covers both cases and prefers updating a page over creating a duplicate.
- **Archiving a cycle ends it first.** `cycle(action=archive)` ends a still-running cycle before archiving it, so close the sprint properly (`complete`, then `transfer_workitems`, then `archive`) — see `/close-sprint`. For modules, check the behavior on your instance.
- **PQL has limits.** At most 5 conditions per filter; no field for story points or description text (estimates and descriptions are read from the listed items); no history queries (`wasEver`, `changedTo`: use `workitem_activity`); `state__group` is a `group_by` key for counts, the filter field is `stateGroup`. `workitem(action=count)` counts items, not points.
- **Customers, collections and templates** (`customer*`, `collection`, `template`) exist in the Plane MCP server but are outside this plugin's scope.
- **Views CRUD is not exposed** by any Plane MCP implementation I have tested — views are a UI-only concept on every instance so far.

## License

MIT
