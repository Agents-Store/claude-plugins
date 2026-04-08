---
name: pages-publishing
description: Create and publish Plane pages — sprint reports, retro notes, release notes, roadmap pages, meeting notes, and stakeholder updates as formatted HTML. Use when the user wants to publish a report, write a sprint summary, create a retro page, generate release notes, or share a roadmap. Includes reusable HTML templates.
---

# Pages Publishing

Plane pages are rich HTML documents attached to a project or the workspace. Use them to publish durable artifacts: sprint reports, retros, release notes, roadmaps, ADRs, and stakeholder updates.

## Tool Name Resolution

Resolve real tool names via the `connector-bootstrap` skill.

## Available Actions

| Action | Purpose |
|--------|---------|
| `create_workspace_page` | Create a page at the workspace level |
| `retrieve_workspace_page` | Get a workspace page |
| `create_project_page` | Create a page inside a project |
| `retrieve_project_page` | Get a project page |

## HTML Formatting Rules

Plane pages accept a restricted HTML subset in `description_html`. The Plane editor parses HTML through a Tiptap/ProseMirror schema — anything outside the schema is **silently transformed or stripped**. What you send is not always what you get.

**Safe tags:**
- Structure: `<h1>`, `<h2>`, `<h3>`, `<p>`, `<hr>`
- Lists: `<ul>`, `<ol>`, `<li>` (see List Rendering Gotchas below)
- Ordered list start offset: `<ol start="5">` is preserved
- Emphasis: `<strong>`, `<em>`, `<code>`, `<pre>`
- Tables: `<table>`, `<thead>`, `<tbody>`, `<tr>`, `<th>`, `<td>`
- Links: `<a href="…">`
- Hard break inside text: `<br>` (becomes a `hardBreak` node inside the surrounding paragraph)

**Avoid:** inline `<style>`, `<script>`, `<iframe>`, raw markdown, any custom `data-*` attributes (see gotchas below).

## List Rendering Gotchas — Critical

Plane's editor is strict about list structure. Several "valid HTML" patterns silently produce broken, disjointed, or empty-bullet output. These were verified by roundtrip testing (submit HTML → retrieve stored ProseMirror doc → compare). Follow these rules or your published page will look wrong.

### Gotcha 1 — `<li>` must start with text, not a nested list

**Broken:** a `<li>` whose first child is `<ul>` or `<ol>` (no own text).

```html
<!-- BROKEN: produces three disjointed top-level lists -->
<ul>
  <li><ul><li>Orphan child</li></ul></li>
  <li>Normal sibling</li>
</ul>
```

Stored result: **three separate top-level `bulletList` nodes** — one empty, one with the "Orphan child", one with the "Normal sibling". The outer list is torn apart at every child-first `<li>`.

**Correct:** always put at least one text character in the parent `<li>` before the nested list.

```html
<!-- OK: one structured list with proper nesting -->
<ul>
  <li>Topic<ul><li>Sub-point</li></ul></li>
  <li>Normal sibling</li>
</ul>
```

This is the root cause of "broken lists with gaps" that most users see.

### Gotcha 2 — Task lists / checkboxes via `data-checked` are silently stripped

```html
<!-- Stripped: data-checked is dropped, renders as plain bullets -->
<ul>
  <li data-checked="true">Done action</li>
  <li data-checked="false">Pending action</li>
</ul>
```

Plane's schema does not recognize `data-checked` on `<li>` at the HTML import layer — there is no `taskList` / `taskItem` node produced. The attribute is cosmetically preserved in `description_html` but the stored ProseMirror doc is plain `bulletList`.

**Correct:** use Unicode status markers as text instead. They render identically in any viewer and do not depend on editor features.

```html
<ul>
  <li>✅ Done action</li>
  <li>⏳ In progress action</li>
  <li>⬜ Not started action</li>
</ul>
```

### Gotcha 3 — Never emit empty `<li></li>`

```html
<!-- BROKEN: produces a visible empty bullet gap -->
<ul>
  <li>Before</li>
  <li></li>
  <li>After</li>
</ul>
```

An empty `<li>` is stored as a listItem with an empty paragraph and renders as an empty bulleted line. When a template placeholder like `{{NOT_DELIVERED_ITEMS}}` has no data, **do not substitute an empty string into `<ul>…</ul>`** — either emit the whole `<ul>` block conditionally or substitute `<li><em>None</em></li>`.

### Gotcha 4 — Don't mix inline text with block elements inside `<li>`

```html
<!-- Looks odd: three stacked paragraphs inside one bullet -->
<li>Text then<p>paragraph inside</p>and more text</li>
```

Each text run and each `<p>` becomes its own paragraph inside the `listItem`, stacking them vertically under one bullet marker. If you need a paragraph, put it outside the list. If you want a single bullet with multi-line text, use `<br>` inside one text run:

```html
<li>First line<br>second line of the same bullet</li>
```

### Gotcha 5 — Two `<ul>` blocks back-to-back stay separate

This is **not** a bug, but worth knowing: if you emit two adjacent `<ul>` blocks without a heading or `<hr>` between them, they stay as two separate lists (not merged). Fine for most cases, but if you want merged output, put the items in one `<ul>`.

### Quick Checklist for Template Authors

Before publishing any generated HTML:
1. No `<li>` starts with `<ul>` or `<ol>` — every parent list item has leading text
2. No empty `<li></li>` — conditional render the whole `<ul>` block for empty data
3. No `data-checked`, `data-*`, or other custom attributes — use Unicode markers
4. No mixed text + `<p>` inside a single `<li>` — use `<br>` for multi-line items
5. Nested lists use at most 3 levels (deeper works but is hard to read)
6. `<ol start="N">` is preserved if you need numbered lists starting mid-sequence

## Cleanup Limitation — Write-Once Pages

Many Plane MCP connectors expose **only `create_*_page` and `retrieve_*_page`** — no `update_*_page`, no `delete_*_page`, no `archive_*_page`. Pages published through this plugin are effectively **write-once via the API**: to edit or delete, users must open the page in the Plane web UI and do it manually.

Consequences:
- Do not use `/publish-report` in a loop that overwrites the same target — each run creates a new page.
- Roadmap pages that the team edits weekly are best **created once** and then updated manually in the Plane UI, not regenerated every week.
- When testing publishing flows, use a throwaway project (like a "Sandbox") because the test pages will remain until manually cleaned up.

If your specific connector does expose update or delete, you can use it — but do not assume it is available.

## HTML Templates

Reusable templates live as separate files — load only the one you need:

| Type | File |
|------|------|
| Sprint report | [references/templates/sprint-report.html](references/templates/sprint-report.html) |
| Retrospective | [references/templates/retro.html](references/templates/retro.html) |
| Release notes | [references/templates/release-notes.html](references/templates/release-notes.html) |
| Roadmap | [references/templates/roadmap.html](references/templates/roadmap.html) |
| Milestone update | [references/templates/milestone-update.html](references/templates/milestone-update.html) |

Each template uses `{{PLACEHOLDER}}` tokens. Render by replacing tokens with concrete values gathered from Plane. Inlined previews follow for quick reference.

## Sprint Report Template

```html
<h1>Sprint 14 Report — Billing v2</h1>
<p><strong>Dates:</strong> 2026-03-24 → 2026-04-04 &middot; <strong>Goal:</strong> Users can see their Stripe invoices in-app</p>

<h2>Summary</h2>
<ul>
  <li>Completed: <strong>34 / 40 points</strong> (85%)</li>
  <li>Velocity vs last 3 sprints avg: 34 vs 32 (+6%)</li>
  <li>Goal achieved: <strong>Yes</strong></li>
</ul>

<h2>Delivered</h2>
<table>
  <thead><tr><th>ID</th><th>Title</th><th>Points</th><th>Owner</th></tr></thead>
  <tbody>
    <tr><td>PROJ-148</td><td>Stripe webhook receiver</td><td>5</td><td>@alice</td></tr>
  </tbody>
</table>

<h2>Not Delivered</h2>
<ul>
  <li>PROJ-152 — PDF export (3 pts) — blocked by vendor API, transferred to Sprint 15</li>
</ul>

<h2>Metrics</h2>
<ul>
  <li>Cycle time: 2.4 days avg</li>
  <li>WIP peak: 6 (limit 7)</li>
  <li>Blockers encountered: 2</li>
</ul>

<h2>Next Sprint</h2>
<p>Goal: …</p>
```

## Retrospective Template

```html
<h1>Sprint 14 Retrospective</h1>
<p><strong>Date:</strong> 2026-04-04 &middot; <strong>Attendees:</strong> @alice, @bob, @carol</p>

<h2>Previous Action Items</h2>
<ul>
  <li>✅ Enable daily standup async thread</li>
  <li>⏳ Document Stripe webhook schema — carried over</li>
</ul>

<h2>What Went Well</h2>
<ul><li>…</li></ul>

<h2>What Didn't</h2>
<ul><li>…</li></ul>

<h2>Action Items</h2>
<table>
  <thead><tr><th>Action</th><th>Owner</th><th>Due</th></tr></thead>
  <tbody>
    <tr><td>Add Stripe mock to local dev</td><td>@alice</td><td>Sprint 15</td></tr>
  </tbody>
</table>
```

## Release Notes Template

```html
<h1>Release v2.0 — 2026-04-08</h1>

<h2>Highlights</h2>
<ul>
  <li>Multi-tenant support</li>
  <li>New billing portal powered by Stripe</li>
</ul>

<h2>New Features</h2>
<ul><li>…</li></ul>

<h2>Improvements</h2>
<ul><li>…</li></ul>

<h2>Bug Fixes</h2>
<ul><li>…</li></ul>

<h2>Breaking Changes</h2>
<ul><li>…</li></ul>

<h2>Upgrade Notes</h2>
<p>…</p>
```

## Roadmap Page Template

```html
<h1>Roadmap — Q2 2026</h1>

<h2>Now (this sprint)</h2>
<ul><li><strong>Billing v2</strong> — Stripe migration, 65% complete</li></ul>

<h2>Next (next sprint)</h2>
<ul><li><strong>Multi-tenant support</strong> — design done, implementation starts Sprint 16</li></ul>

<h2>Later (this quarter)</h2>
<ul><li><strong>Enterprise SSO</strong> — scoping</li></ul>

<h2>Parked</h2>
<ul><li><strong>Mobile app</strong> — revisit Q3</li></ul>
```

## Publishing Workflow

```
1. connector-bootstrap → resolve tools
2. list_projects       → pick project_id
3. Gather data from Plane (cycle data, work items, metrics)
4. Render HTML using a template above
5. create_project_page({
     project_id,
     name: "Sprint 14 Report",
     description_html: "<...>"
   })
6. Share the page URL with stakeholders
```

## Best Practices

1. Publish the sprint report within 24 hours of sprint close — memory fades fast.
2. Link the report from the cycle's description for easy discovery.
3. Keep release notes audience-appropriate: customer-facing pages omit internal work items.
4. Roadmap pages should be updated weekly, not created from scratch.
5. Never publish PII or secrets on workspace pages — they may be broadly visible.
