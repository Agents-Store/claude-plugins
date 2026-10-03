# plane-ops

Agile operations knowledge plugin for [Plane](https://plane.so). Agile workflows on top of the Plane MCP server: sprint planning, backlog management, estimation, retrospectives, daily standups, work items, labels/states/types/properties, pages (sprint reports, retros, ADRs, runbooks, specs), roadmaps, dependencies, and more.

**Compatibility:** works with Plane MCP 0.3.0 and later (one tool per resource with an `action` parameter, for example `cycle(action="list")`) and with legacy per-operation connectors (`list_cycles`, `create_work_item`, ...). The `connector-bootstrap` skill finds either surface and translates the legacy action names used by the other skills into resource calls.

**Current version: 1.4.0** — compatibility layer for Plane MCP 0.3.0+: `connector-bootstrap` finds the resource tools and translates legacy action names, and the destructive-operation hook matches them and checks the `action`. 1.3.0 added 22 commands, the `labels-states-properties` skill, 5 page templates and the safety hooks.

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

Most other skills and commands still describe operations with legacy action names (`list_projects`, `create_cycle`, `add_work_items_to_module`, etc.) and delegate tool resolution to `connector-bootstrap`, whose translation table maps each of them to a resource call such as `cycle(action=manage_workitems, add_ids=[...])`. A native rewrite of those skills for the resource tools is planned for 2.0.0. The plugin content never mentions any specific MCP server name or tool prefix.

## Components

### Skills

- **connector-bootstrap** — forcer skill that runs before any Plane operation; probes `ToolSearch` for the resource tools of Plane MCP 0.3+ and for legacy per-operation tools, translates legacy action names into resource calls, and handles multi-instance setups
- **agile-fundamentals** — single source of truth for formulas (capacity, WSJF, WIP), Definition of Ready/Done, MoSCoW mapping, Fibonacci scale, sprint buffer policy
- **sprint-planning** — full planning ceremony: capacity, velocity, selection, cycle creation
- **work-items** — CRUD, relations, comments, links, work logs, custom types and properties; includes the field names of the official server and caveats for legacy connectors
- **modules** — feature/workstream grouping that spans multiple sprints
- **epics-initiatives-milestones** — long-horizon planning above sprints
- **backlog-management** — MoSCoW, WSJF scoring, grooming, backlog health
- **task-decomposition** — INVEST criteria, vertical slicing, epic → story breakdown
- **estimation** — story points, planning poker, Fibonacci, t-shirt sizing
- **velocity-metrics** — velocity, burndown, WIP limits, cycle time, throughput
- **daily-standup** — progress summary, blocker detection, async standups
- **sprint-review-retro** — review, retrospective formats, action item tracking
- **project-setup** — bootstrapping a new Agile-ready project
- **intake-triage** — triaging incoming requests into the backlog
- **labels-states-properties** — taxonomy design: when to use labels vs work item types vs custom properties, state group rules, naming conventions, quarterly audit workflow
- **pages-publishing** — publishing sprint reports, retros, release notes, ADRs, runbooks, specs, meeting notes, roadmap pages; includes HTML templates, list-rendering gotchas, and verified workarounds for Plane editor quirks
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
- `PreToolUse` — a `prompt` hook that fires on Plane resource tools (`mcp__<server containing "plane">__cycle`, `__workitem`, `__page`, ...) and on legacy `delete_*` tools. It reads the `action` of the call: `delete`, `remove_projects`, `detach_from_workitem`, `delete_point`, `delete_option`, `delete_value` and `delete_definition` (and a few other destructive actions) require explicit user confirmation; `archive` only produces a warning; every other action passes without questions. It does **not** watch for bulk updates, and it matches servers whose name contains `plane` (rename your connection accordingly, or edit the matcher in `hooks/hooks.json`).

## Prerequisites

A working Plane integration in your Claude environment. Recommended connection methods for the official Plane MCP server (0.3.0 and later):

| Method | Command or setting |
|---|---|
| Hosted, OAuth | `claude mcp add --transport http plane https://mcp.plane.so/http/mcp`, then `/mcp` in a session to authenticate |
| Hosted, personal access token (CI, headless) | URL `https://mcp.plane.so/http/api-key/mcp` with headers `Authorization: Bearer ${PLANE_PAT}` and `x-workspace-slug: <workspace-slug>` (the older `x-api-key` header no longer works) |
| Self-hosted Plane (stdio) | `uvx plane-mcp-server stdio` with `PLANE_API_KEY`, `PLANE_WORKSPACE_SLUG` and `PLANE_BASE_URL` |

The hosted server cannot reach private self-hosted instances, and OAuth is not available on Plane Community Edition: use stdio there. The SSE endpoint and the npm package `@makeplane/plane-mcp-server` are deprecated. A Plane connector registered with Claude, another `.mcp.json` entry, or a Cowork-provided Plane bridge also work, including legacy per-operation connectors.

If you do not have Plane connected, the `connector-bootstrap` skill will tell you which `ToolSearch` probes it ran and suggest how to connect Plane. It will not silently refuse.

## Multi-instance support

If you have more than one Plane workspace connected (for example, a cloud workspace for work and a self-hosted workspace for personal projects), the plugin detects this during bootstrap and asks you which instance to operate on. Tell it once per session and it remembers the choice until you ask to switch.

## Cleanup limitations you should know

- **Pages on Plane MCP 0.3+ can be updated, archived and deleted.** `page(action=update)` replaces the whole `description_html` body (retrieve the page first), `archive` hides it, and `delete` works only on an archived page. Legacy connectors often expose only create and retrieve for pages; there, edits happen in the Plane web UI. The `pages-publishing` skill covers both cases and warns you before running loops that would create duplicate pages.
- **Archiving a cycle ends it first.** On Plane MCP 0.3+, `cycle(action=archive)` ends a still-running cycle before archiving it, so close the sprint properly (`complete`, then `transfer_workitems`, then `archive`) — see `/close-sprint`. For modules, check the behavior on your instance.
- **Views CRUD is not exposed** by any Plane MCP implementation I have tested — views are a UI-only concept on every instance so far.

## License

MIT
