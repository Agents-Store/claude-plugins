---
description: Create, list, get, or update a Plane page (project or workspace scope)
argument-hint: <action> [scope] [project] [args...]
---

# Page

Manage Plane Pages — long-form documents attached to a project or to the workspace. Delegates rendering rules to the `pages-publishing` skill and tool resolution to `connector-bootstrap`.

## Arguments

Format: `<action> [scope] [project] [args...]`

- `action`: `create` | `list` | `get` | `update`
- `scope`: `project` (default) | `workspace`
- `project`: project name or identifier (required when `scope=project`)
- Remaining: title, content source (`--from-file`, `--from-template`, inline body), `--page-id` for `get`/`update`

Parse from `"$ARGUMENTS"`.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe `ToolSearch` for: `create_project_page`, `retrieve_project_page`, `create_workspace_page`, `retrieve_workspace_page`. Note: list and update endpoints may not exist on every Plane build — fall back gracefully and tell the user.
2. **Resolve scope**:
   - `project` → `list_projects` → `project_id`
   - `workspace` → no project lookup; uses workspace-level call
3. **Route by action**:
   - `create` → gather `name` and `description_html`. Sources of body, in order of preference:
     - `--from-file <path>` → read file, convert markdown→HTML if needed
     - `--from-template <name>` → use a template from `pages-publishing` skill (`sprint-report`, `retro`, `release-notes`, `roadmap`, `milestone-update`, `meeting-notes`, `decision-log`, `spec`, `runbook`, `blank`)
     - inline body in arguments → wrap in `<p>` paragraphs
     - none → ask the user once for the body
     Call `create_project_page` or `create_workspace_page`.
   - `list` → if a list tool is exposed by the connector, use it; otherwise tell the user pages must be opened from the Plane UI sidebar and offer to retrieve a known page by ID.
   - `get` → `retrieve_*_page({ page_id })`. Render the HTML back as readable markdown for the terminal.
   - `update` → not all Plane builds expose update; if unavailable, instruct the user to recreate the page or edit in UI. If available, patch `description_html`.
4. **Confirm** — print the page name, ID, and URL. Suggest where to link it (cycle description, Slack, README).

## Examples

```
/page create project "TaskFlow" "Q2 Engineering Plan" --from-file ./plan.md
/page create project "TaskFlow" "Sprint 14 Report" --from-template sprint-report
/page create workspace "Team Handbook"
/page get project "TaskFlow" --page-id 7c8e...
/page update project "TaskFlow" --page-id 7c8e... --from-file ./plan-v2.md
/page list project "TaskFlow"
```

## Best Practices

- Project pages live with the project they document — use them for sprint reports, retros, decision logs, runbooks.
- Workspace pages are for cross-project content — handbooks, OKRs, hiring loops.
- Always include a "Last updated" line at the top — Plane does not surface freshness in the sidebar.
- Prefer **editing** an existing page (e.g. roadmap) over recreating it; recreating breaks links.
