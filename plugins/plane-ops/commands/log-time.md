---
description: Log work time on a Plane work item (create a work log entry)
argument-hint: <project> <item> <duration> [description]
---

# Log Time

Create a work log entry against a Plane work item. Time is stored as **integer minutes** in the API — convert human input.

## Arguments

Format: `<project> <item> <duration> [description]`

- `project`: project name or identifier
- `item`: work item identifier (e.g. `PROJ-42`) or UUID
- `duration`: human form (`2h`, `2h30m`, `45m`, `1.5h`, `PT2H30M`) — convert to integer minutes
- `description` (optional): free text — what was done

Parse from `"$ARGUMENTS"`.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for `create_work_log`, `list_work_logs`, `get_project_worklog_summary`.
2. **Verify time tracking is enabled** — check `get_project_features` or fetch project; if `is_time_tracking_enabled` is false, tell the user how to enable it (project settings → features) and stop.
3. **Resolve project** → `project_id`. **Resolve work item** → if identifier like `PROJ-42`, use `retrieve_work_item_by_identifier`; if UUID, skip.
4. **Convert duration to minutes**:
   - `2h` → 120, `2h30m` → 150, `45m` → 45, `1.5h` → 90, `PT2H30M` → 150
   - Reject if result < 1 or > 24h in a single entry (likely a typo); ask user to confirm.
5. **Create the log** — `create_work_log({ project_id, work_item_id, duration: <minutes>, description })`.
6. **Confirm** — print: total logged today on this item, total logged this sprint by this user (use `list_work_logs` filtered).

## Subcommands

The base form logs time. Additional verbs (parse `<verb> ...` if first arg is one of these):

- `summary <project>` → `get_project_worklog_summary` — total logged per user / per item
- `list <project> <item>` → `list_work_logs` for that item
- `delete <project> <log_id>` → `delete_work_log` (confirm first)
- `update <project> <log_id> <duration>` → `update_work_log`

## Examples

```
/log-time "TaskFlow" PROJ-148 2h "Debug Safari login bug + fix"
/log-time "TaskFlow" PROJ-148 45m
/log-time summary "TaskFlow"
/log-time list "TaskFlow" PROJ-148
/log-time delete "TaskFlow" 9f2c-...
```

## Best Practices

- Log time **at the end of each work session**, not in batch at week's end — accuracy drops sharply after 24h.
- One entry per session per item. Don't merge a whole day into one log.
- Use `/log-time summary` before estimation sessions — actual minutes per story point is the most honest velocity input (see `velocity-metrics` skill).
