# Plane Page Formatting Guide

Plane stores page content as **HTML** in the `description_html` field. Use semantic HTML so the rich-text editor renders the page cleanly. Markdown is **not** parsed — convert to HTML first.

## Supported HTML elements

| Element | Use for |
|---------|---------|
| `<h1>` … `<h3>` | Section headings (don't go deeper than h3 — Plane editor flattens it) |
| `<p>` | Paragraphs (always wrap plain text — bare text loses spacing) |
| `<ul>` / `<ol>` / `<li>` | Bullet and numbered lists |
| `<strong>` | Bold (do not use `<b>`) |
| `<em>` | Italic (do not use `<i>`) |
| `<code>` | Inline code |
| `<pre><code>…</code></pre>` | Code blocks |
| `<a href="…">` | Links (always include `href`) |
| `<blockquote>` | Quotes / callouts |
| `<hr>` | Horizontal divider between sections |
| `<details><summary>…</summary>…</details>` | Collapsible sections (great for long retros) |
| `<table><tr><td>` | Tables (keep simple — no colspan/rowspan) |

## Required wrapping rule

Every chunk of text needs a block element. Bare strings between tags collapse to one line.

❌ Wrong:
```html
<h2>Goal</h2>
Ship the auth flow.
<h2>Owners</h2>
```

✅ Right:
```html
<h2>Goal</h2>
<p>Ship the auth flow.</p>
<h2>Owners</h2>
```

## Page name conventions

Choose names that sort and search well:

| Page type | Name pattern | Example |
|-----------|-------------|---------|
| Sprint retro | `Retro — Sprint <N> (YYYY-MM-DD)` | `Retro — Sprint 12 (2026-03-14)` |
| Daily standup | `Standup — YYYY-MM-DD` | `Standup — 2026-04-08` |
| Sprint plan | `Sprint <N> Plan — <goal summary>` | `Sprint 12 Plan — Auth MVP` |
| Decision log | `ADR <NNN> — <topic>` | `ADR 014 — Switch to Postgres` |
| Meeting notes | `<Meeting> — YYYY-MM-DD` | `Backlog Grooming — 2026-04-05` |

Project pages live inside one project. Workspace pages are visible to the whole workspace — use those for cross-project decisions and team rituals.

## Templates

### Retrospective page

```html
<h2>Sprint Metrics</h2>
<p>Completed: 34/40 points (85%) · Velocity: 32 (3-sprint avg)</p>

<h2>What went well (Start / Continue)</h2>
<ul>
  <li>Daily async standup in #dev — fewer blockers slipped a day</li>
  <li>Pairing on the migration script caught two bugs early</li>
</ul>

<h2>What to stop</h2>
<ul>
  <li>Last-minute scope additions after Wednesday</li>
</ul>

<h2>Action items</h2>
<ol>
  <li><strong>Owner:</strong> @alice — Add a "no scope after mid-sprint" rule to the team agreement (due 2026-04-12)</li>
  <li><strong>Owner:</strong> @bob — Spike on flaky test runner (due 2026-04-15)</li>
</ol>

<details>
  <summary>Raw retro notes</summary>
  <p>…full transcript or board export…</p>
</details>
```

### Daily standup page

```html
<h2>Sprint Progress</h2>
<p>Day 4 of 10 · 12/34 points done · burn-down on track</p>

<h2>Per Person</h2>
<table>
  <tr><th>Member</th><th>Yesterday</th><th>Today</th><th>Blockers</th></tr>
  <tr><td>@alice</td><td>Finished login UI</td><td>OAuth callback</td><td>—</td></tr>
  <tr><td>@bob</td><td>DB migration</td><td>Seed data</td><td>Waiting on staging access</td></tr>
</table>

<h2>Blockers</h2>
<ul>
  <li><strong>@bob</strong> — staging access (owner: @ops, ETA today)</li>
</ul>
```

### Sprint plan page

```html
<h2>Sprint Goal</h2>
<blockquote>By end of this sprint, beta users can sign up and log in so we can start onboarding.</blockquote>

<h2>Capacity</h2>
<p>4 devs · 10-day sprint · 28 points (85% of 33-pt velocity)</p>

<h2>Committed Items</h2>
<ol>
  <li>AUTH-12 — Email signup (5 pts, @alice)</li>
  <li>AUTH-13 — Login + JWT (5 pts, @alice)</li>
  <li>AUTH-14 — Password reset (3 pts, @bob)</li>
</ol>

<h2>Stretch</h2>
<ul>
  <li>AUTH-20 — Social login (5 pts, only if AUTH-13 finishes early)</li>
</ul>
```

## Building the HTML programmatically

When generating page content from data (sprint metrics, retro notes, etc.):

1. **Escape user-supplied text** before injecting it — replace `&` `<` `>` `"` `'` with HTML entities to prevent broken markup.
2. **Build sections in order** — heading → paragraph(s) → list, then `<hr>` between major sections if the page is long.
3. **Avoid raw newlines as spacing** — they're collapsed by the editor; use `<p>` blocks instead.
4. **Keep one page per ritual** — don't append to old pages; create a new dated one each time so history stays browsable.

## Pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| Page renders as one long line | Used `\n` instead of block elements | Wrap each line in `<p>` |
| Markdown shows literally (`**bold**`) | Markdown not parsed | Use `<strong>bold</strong>` |
| Headings missing | Used `# Heading` | Use `<h2>Heading</h2>` |
| Tables look broken | Used colspan/rowspan or nested tables | Flatten to simple `<tr>/<td>` |
| Links not clickable | Used bare URL text | Wrap in `<a href="…">…</a>` |
