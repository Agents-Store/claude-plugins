---
description: Deploy or redeploy a Dokploy application
argument-hint: <app-name-or-id> [--project <project>]
---

# Deploy Application

Trigger a deployment for an existing Dokploy application.

## Arguments
Format: `<app-name-or-id> [--project <project>]`
- app-name-or-id: Application name or ID (required)
- --project: Project name or ID (helps resolve app by name)

Parse from "$ARGUMENTS".

## Process

1. **Resolve application:**
   - If argument is a UUID, use it directly.
   - If a name, call `project-all` to list projects, then `project-one` on the matching project (or --project) to find the application by name.

2. **Check current state** using MCP tool `application-one` with the applicationId. Report current status and last deployment.

3. **Deploy** using MCP tool `application-deploy` with the applicationId.

4. **Report deployment triggered:**
   Show application name, deployment status. Note that deployment is asynchronous — use `/dokploy-dev:status` to check progress.

## Example Usage
```
/dokploy-dev:deploy web-frontend --project my-saas
/dokploy-dev:deploy abc123-def456
```
