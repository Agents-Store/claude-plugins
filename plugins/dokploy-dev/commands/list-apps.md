---
description: List all applications and services in a Dokploy project
argument-hint: <project-name-or-id>
---

# List Applications

List all applications, databases, and compose services in a Dokploy project.

## Arguments
Format: `<project-name-or-id>`
- project-name-or-id: Project name or ID (required). If a name is given, resolve it to ID via `project-all` first.

Parse from "$ARGUMENTS".

## Process

1. **Resolve project:** If argument looks like a name (not a UUID), call `project-all` and find the matching project by name.

2. **Get project details** using MCP tool `project-one` with the projectId.

3. **Display as table:**
   Show all services grouped by type:
   - **Applications:** ID, name, status, build type, git repo
   - **Databases:** ID, name, type (postgres/mysql/mariadb/mongo/redis), status
   - **Compose:** ID, name, status

## Example Usage
```
/dokploy-dev:list-apps my-saas
/dokploy-dev:list-apps abc123-def456
```
