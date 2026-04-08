# plane-ops

Agile operations knowledge plugin for [Plane](https://plane.so). Full coverage of the Plane MCP surface: sprint planning, backlog management, estimation, retrospectives, daily standups, work items, labels/states/types/properties, pages (sprint reports, retros, ADRs, runbooks, specs), roadmaps, dependencies, and more.

**Current version: 1.3.0** — adds 22 new commands, `labels-states-properties` skill, extended `pages-publishing` with 5 general-purpose page templates, destructive-operation safety hooks, and 27 new evals (36 total across 9 skills, 100% pass rate).

## What this plugin does

Teaches Claude **how** to run Agile ceremonies and work with Plane entities — sprints (cycles), backlog, work items, modules, epics, initiatives, milestones, intake triage, pages, and more. It does not ship any MCP server or hardcode tool names; it works with whatever Plane integration the user already has connected.

## Design — tool-agnostic knowledge plugin

This plugin ships **no MCP server**, **no `.mcp.json`**, and **no hardcoded tool names**. It is a pure knowledge/ops plugin.

Users may have Plane connected in any of these ways:

- A Claude connector
- A user-level `.mcp.json` pointing at a remote MCP server
- A project-level `.mcp.json` pointing at a self-hosted or cloud Plane instance
- A Cowork/remote MCP bridge
- Multiple Plane workspaces connected simultaneously

The plugin handles all of these through a dedicated `connector-bootstrap` skill that discovers Plane tools via `ToolSearch` at the start of any Plane-related request, matches tools by action suffix (never by prefix), and supports multi-instance environments by asking the user which Plane workspace to operate on when multiple are detected.

Every other skill in the plugin references action names only (`list_projects`, `create_cycle`, `add_work_items_to_module`, etc.) and delegates tool resolution to `connector-bootstrap`. The plugin content never mentions any specific MCP server name or tool prefix.

## Components

### Skills

- **connector-bootstrap** — forcer skill that runs before any Plane operation; probes `ToolSearch` to discover tools and handles multi-instance setups
- **agile-fundamentals** — single source of truth for formulas (capacity, WSJF, WIP), Definition of Ready/Done, MoSCoW mapping, Fibonacci scale, sprint buffer policy
- **sprint-planning** — full planning ceremony: capacity, velocity, selection, cycle creation
- **work-items** — CRUD, relations, comments, links, work logs, custom types and properties; includes schema caveats for common field-name variations across Plane deployments
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

- `SessionStart` — reminds Claude to consult `connector-bootstrap` if the session will involve Plane
- `PreToolUse` — intercepts destructive Plane operations (delete, archive-forced, bulk-update >50 items) and requires explicit user confirmation before the call proceeds

## Prerequisites

A working Plane integration in your Claude environment. Any of:

- A Plane connector registered with Claude
- A `.mcp.json` entry that connects to a Plane MCP server (remote or local)
- A Cowork-provided Plane bridge

If you do not have Plane connected, the `connector-bootstrap` skill will tell you which `ToolSearch` probes it ran and suggest how to connect Plane. It will not silently refuse.

## Multi-instance support

If you have more than one Plane workspace connected (for example, a cloud workspace for work and a self-hosted workspace for personal projects), the plugin detects this during bootstrap and asks you which instance to operate on. Tell it once per session and it remembers the choice until you ask to switch.

## Cleanup limitations you should know

- **Pages are write-once via the API on most Plane deployments.** Once you publish a sprint report, retro, or roadmap page, you cannot update or delete it through the MCP tools — you must open it in the Plane web UI. The plugin documents this in the `pages-publishing` skill and warns you before running loops that would create duplicate pages.
- **Active cycles and modules cannot be archived.** Complete them first, or use delete directly.
- **Views CRUD is not exposed** by any Plane MCP implementation I have tested — views are a UI-only concept on every instance so far.

## License

MIT
