---
description: Show the current Plane user, workspace, and connector status
argument-hint: (no arguments)
---

# Who Am I

Print the identity and context Plane is currently operating with. Useful for verifying the right account/instance is connected before destructive operations.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for `get_me`, `get_workspace_features`, `list_projects`.
2. **Identity** — `get_me`. Print: display name, email, user_id, role, avatar URL.
3. **Workspace** — workspace name and slug from `get_me` response or `get_workspace_features`. Print enabled features.
4. **Projects** — `list_projects`, count by archived/active. Print top 5 by recent activity.
5. **Connector** — print which MCP server / instance the tools were resolved against (from `connector-bootstrap` result). If multiple Plane instances are connected, list them and indicate the active one.
6. **Suggest** — if no projects, suggest `/setup-project`. If multiple instances, show how to switch.

## Examples

```
/whoami
```

## Why this exists

Before running anything destructive (`/cycles delete`, `/projects delete`, `/state delete`), run `/whoami` to make sure you are not accidentally connected to a production workspace when you meant the staging one. Cheap insurance.
