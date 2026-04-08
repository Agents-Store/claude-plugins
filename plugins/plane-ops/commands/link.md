---
description: Add or list external links (PRs, docs, designs) on a Plane work item
argument-hint: <action> <project> <item> [url] [title]
---

# Link

Attach external URLs to a work item — pull requests, design docs, Figma boards, runbooks.

## Arguments

Format: `<action> <project> <item> [url] [title]`

- `action`: `add` (default) | `list` | `remove`
- `project`: project name or identifier
- `item`: work item identifier or UUID
- `url`: full URL (required for `add`)
- `title`: human-readable label (optional; auto-derive from URL host + path tail if omitted)
- `--id <link_id>` for `remove`

Parse from `"$ARGUMENTS"`.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for `create_work_item_link`, `list_work_item_links`, `delete_work_item_link`.
2. **Resolve project** → `project_id`. **Resolve work item** → `work_item_id`.
3. **Route**:
   - `add` → if title omitted, derive: `github.com/org/repo/pull/420` → `"PR #420"`, `figma.com/file/...` → `"Figma design"`, `docs.google.com/...` → `"Google Doc"`. Call `create_work_item_link({ url, title, ... })`.
   - `list` → `list_work_item_links`, render as `Title — URL`.
   - `remove` → with `--id`, call `delete_work_item_link`. Without, list and ask which to remove.
4. **Confirm** — print link title and the item identifier.

## Examples

```
/link add "TaskFlow" PROJ-148 https://github.com/org/repo/pull/420
/link add "TaskFlow" PROJ-148 https://figma.com/file/abc "Login flow design v3"
/link list "TaskFlow" PROJ-148
/link remove "TaskFlow" PROJ-148 --id 9f2c-...
```

## Best Practices

- Always link the **PR** to the work item — this is how reviewers find context and how release-notes generation finds the change.
- Link **design** before implementation, **runbook** before deploy.
- Avoid pasting links into the description body — use proper links so they can be enumerated.
