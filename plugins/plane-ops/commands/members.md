---
description: List Plane workspace or project members and their roles
argument-hint: [scope] [project]
---

# Members

List members of the workspace or a specific project.

## Arguments

Format: `[scope] [project]`

- `scope`: `workspace` (default) | `project`
- `project`: required when `scope=project` — project name or identifier
- `--role <admin|member|viewer|guest>`: filter
- `--active`: only active members

Parse from `"$ARGUMENTS"`.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for `get_workspace_members`, `get_project_members`, `get_me`.
2. **Route**:
   - `workspace` → `get_workspace_members`. Render: name | email | role | joined | last active.
   - `project` → resolve `project_id` → `get_project_members`. Add a column showing the workspace role for context.
3. **Apply filters** client-side.
4. **Highlight current user** (from `get_me`).
5. **Footer** — total count, count by role.

## Examples

```
/members
/members workspace --role admin
/members project "TaskFlow"
/members project "TaskFlow" --role member
```

## Best Practices

- Audit workspace admins quarterly — too many admins is a security risk.
- Project membership should be the minimum needed; use viewer for stakeholders.
- Pair with `/assign` to find the right user when names are ambiguous.
