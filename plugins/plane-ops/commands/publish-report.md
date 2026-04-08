---
description: Publish a Plane page — sprint report, retro, release notes, or roadmap
argument-hint: <type> <project> [args...]
---

# Publish Report

Generate and publish a Plane project page using a template from the `pages-publishing` skill.

## Arguments

Format: `<type> <project> [args...]`

- `type`: `sprint-report` | `retro` | `release-notes` | `roadmap` | `milestone-update`
- `project`: project name or identifier
- Remaining args depend on type

Parse from `"$ARGUMENTS"`.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for `create_project_page`, `create_workspace_page`, and the data-gathering actions required by the chosen type.
2. **Resolve project** — `list_projects` → `project_id`.
3. **Gather data** based on `type`:
   - `sprint-report` → active or last cycle, items, metrics (see `velocity-metrics`)
   - `retro` → previous sprint items, previous retro page (if exists), attendees
   - `release-notes` → items closed in a version range, grouped by label
   - `roadmap` → active cycles, modules, epics, milestones
   - `milestone-update` → target milestone and its items (see `epics-initiatives-milestones`)
4. **Render HTML** using the matching template from the `pages-publishing` skill.
5. **Create the page** — `create_project_page({ project_id, name, description_html })`.
6. **Share** — return the page URL and suggest where to link it (cycle description, Slack, etc.).

## Examples

```
/publish-report sprint-report "TaskFlow"
/publish-report retro "TaskFlow"
/publish-report release-notes "TaskFlow" --version v2.0
/publish-report roadmap "TaskFlow"
/publish-report milestone-update "TaskFlow" "v2.0 Public Beta"
```

## Best Practices

- Sprint reports: publish within 24 hours of sprint close
- Retros: publish immediately after the ceremony
- Release notes: two versions — internal (with all items) and customer-facing (curated)
- Roadmap: update weekly, do not recreate — edit the existing page
