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

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for the Plane resource tool `page` and the data-gathering tools required by the chosen type (`cycle`, `workitem`, `module`, `milestone`, `release`).
2. **Resolve project** — `project(action=list)` → `project_id`.
3. **Gather data** based on `type`:
   - `sprint-report` → active or last cycle (`cycle(action=list, project_id, status=current|completed)`), its items (`cycle(action=list_workitems)`, state totals with `workitem(action=count, pql='cycle = "<id>"', group_by=state__group)`), metrics (see `velocity-metrics`)
   - `retro` → previous sprint items, previous retro page (`page(action=list, project_id)`, if one exists), attendees
   - `release-notes` → the release from `release(action=list)` (`--version` matches the release name or its `release_tag`), its items from `release(action=list_workitems, release_id)`, grouped by type or label; the stored changelog from `release(action=get_changelog, release_id)`. Without a tracked release, the items closed in the version range: `workitem(action=list, project_id, pql='stateGroup = "completed" AND updatedAt >= "<start date>"')`
   - `roadmap` → active cycles (`cycle(action=list)`), modules (`module(action=list)`), epics (`workitem(action=list, pql='type = "<epic-type-id>"')`), milestones (`milestone(action=list)`)
   - `milestone-update` → target milestone and its items (see `epics-initiatives-milestones`)
4. **Render HTML** using the matching template from the `pages-publishing` skill.
5. **Create the page** — `page(action=create, project_id, name, description_html)`. For `release-notes`, also store the same body with `release(action=update_changelog, release_id, description_html)` so the notes stay attached to the release. To refresh an existing report (roadmap, a corrected sprint report) use `page(action=retrieve)` then `page(action=update)` with the whole edited body instead of creating a duplicate.
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
