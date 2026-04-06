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

3. **Pre-deploy checks:**
   - **Environment variables:** Check if `env` is set on the application. If empty, read the project's local `.env.local` or `.env` file and set runtime env vars via `application-saveEnvironment`. Separate build-time vars (e.g. `NEXT_PUBLIC_*`) from runtime-only vars — build-time vars must also go into `buildArgs`.
   - **Build type:** Check `buildType`. If the project has a `Dockerfile`, ask the user which build type to use (`dockerfile` or `nixpacks`). Default recommendation: `dockerfile` when a Dockerfile exists. Set via `application-saveBuildType` with all required fields (`applicationId`, `buildType`, `dockerfile`, `dockerContextPath`, `dockerBuildStage`, `herokuVersion`, `railpackVersion`).

4. **Deploy** using MCP tool `application-deploy` with the applicationId.

5. **Monitor until completion:**
   - Poll `deployment.all?applicationId=<id>` every 30-60 seconds to check latest deployment status.
   - If status is `done` — report success and verify the app is reachable (check health endpoint or domain).
   - If status is `error` — read deployment logs via Beszel container logs or Dokploy log endpoints, diagnose the issue, fix it (update env vars, build type, Dockerfile, etc.), and redeploy. Repeat until deployment succeeds.
   - Show the user build logs and errors transparently.

## Example Usage
```
/dokploy-dev:deploy web-frontend --project my-saas
/dokploy-dev:deploy abc123-def456
```
