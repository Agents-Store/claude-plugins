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

2. **Get application details** using MCP tool `application-one`. Show:
   - Application status (running/stopped/error)
   - Build type
   - Git repository and branch (if connected)
   - Environment variables count
   - Domains attached

3. **Get recent deployments** using MCP tool `deployment-all` filtered by application. Show last 5 deployments:
   - Deployment ID, status, trigger type, start time, duration

4. **Get monitoring data** using MCP tool `application-readAppMonitoring` if available. Show CPU/memory usage.

## Example Usage
```
/dokploy-dev:status web-frontend --project my-saas
/dokploy-dev:status abc123-def456
```
