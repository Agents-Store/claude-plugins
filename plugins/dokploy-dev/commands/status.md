---
description: Check Dokploy application or deployment status
argument-hint: <app-name-or-id> [--project <project>]
---

# Check Status

Check the current status of a Dokploy application and its recent deployments.

## Arguments
Format: `<app-name-or-id> [--project <project>]`
- app-name-or-id: Application name or ID (required)
- --project: Project name or ID (helps resolve app by name)

Parse from "$ARGUMENTS".

## Process

1. **Resolve application** (same as deploy command).

2. **Detect Docker Compose build mode:** Call `project-all` (or `project-one`) and check if the project has a compose service alongside the application. If a compose service exists, warn the user: "This project also has a Docker Compose service (`<compose-name>`) — the production site may run from compose, not the standalone app. Showing status of both."

3. **Get application details** using MCP tool `application-one`. Show:
   - Application status (running/stopped/error)
   - Build type
   - Git repository and branch (if connected)
   - Environment variables count
   - Domains attached

4. **Get compose details** (if compose service exists) using MCP tool `compose-one`. Show:
   - Compose status
   - Source type (GitHub/Git)
   - Domains attached
   - Flag if auto-deploy is connected to the application but NOT to compose — this is a common misconfiguration

5. **Get recent deployments** using MCP tool `deployment-all` filtered by application. Show last 5 deployments:
   - Deployment ID, status, trigger type, start time, duration

6. **Get monitoring data** using MCP tool `application-readAppMonitoring` if available. Show CPU/memory usage.

## Example Usage
```
/dokploy-dev:status web-frontend --project my-saas
/dokploy-dev:status abc123-def456
```
