---
description: Create and deploy a database in a Dokploy project
argument-hint: <name> --project <project> --type <postgres|mysql|mariadb|mongo|redis> [--password <pass>]
---

# Create Database

Create and deploy a database instance in a Dokploy project.

## Arguments
Format: `<name> --project <project> --type <postgres|mysql|mariadb|mongo|redis> [--password <pass>]`
- name: Database name (required)
- --project: Project name or ID (required)
- --type: Database type — postgres, mysql, mariadb, mongo, redis (required)
- --password: Database password (optional, auto-generated if omitted)

Parse from "$ARGUMENTS".

## Process

1. **Resolve project** (same as create-app command).

2. **Create database** using the type-specific MCP tool:
   - postgres: `postgres-create`
   - mysql: `mysql-create`
   - mariadb: `mariadb-create`
   - mongo: `mongo-create`
   - redis: `redis-create`

   Pass: name, projectId, databasePassword (if provided).

3. **Deploy database** using `{type}-deploy` with the created database ID.

4. **Display result:**
   Show database ID, name, type, status. Include internal connection details (host, port, credentials) and suggest using `{type}-saveExternalPort` if external access is needed.

## Example Usage
```
/dokploy-dev:create-db "main-db" --project my-saas --type postgres
/dokploy-dev:create-db "cache" --project my-saas --type redis
/dokploy-dev:create-db "analytics" --project data --type mongo --password "secure123"
```
