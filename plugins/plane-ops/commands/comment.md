---
description: Add or list comments on a Plane work item
argument-hint: <action> <project> <item> [body]
---

# Comment

Add or list comments on a Plane work item.

## Arguments

Format: `<action> <project> <item> [body]`

- `action`: `add` (default if omitted) | `list` | `update` | `delete`
- `project`: project name or identifier
- `item`: work item identifier (`PROJ-42`) or UUID
- `body`: comment text (for `add`/`update`) — supports markdown

Parse from `"$ARGUMENTS"`.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for `create_work_item_comment`, `list_work_item_comments`, `update_work_item_comment`, `delete_work_item_comment`.
2. **Resolve project** → `project_id`. **Resolve work item** → `work_item_id`.
3. **Route**:
   - `add` → convert markdown body to HTML if the API expects `comment_html`; call `create_work_item_comment`. Mention the user via `@username` only if the API supports mentions — otherwise plain text.
   - `list` → `list_work_item_comments`, render newest-first with author + timestamp.
   - `update` → resolve `comment_id` (last by current user, or explicit `--id`), patch.
   - `delete` → confirm before destructive call.
4. **Confirm** — print the comment ID and a one-line preview.

## Examples

```
/comment add "TaskFlow" PROJ-148 "Reproduced on Safari 17.2 — root cause is the cookie SameSite change"
/comment list "TaskFlow" PROJ-148
/comment update "TaskFlow" PROJ-148 --id 9f2c... "Updated: also affects Safari 16"
/comment delete "TaskFlow" PROJ-148 --id 9f2c...
```

## Best Practices

- Comments are for **decisions and findings**, not status pings ("any update?"). Use standup or DM for that.
- When closing a bug, leave a final comment with: root cause, fix summary, test added. This is gold for future debugging.
- Cross-link related items in the body using their identifier (e.g. "see PROJ-150") — Plane auto-links them.
