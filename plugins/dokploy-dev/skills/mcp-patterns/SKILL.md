---
name: mcp-patterns
description: "This skill should be used when deploying applications, managing projects, provisioning databases, configuring domains, working with Docker Compose, or performing any Dokploy operation via MCP tools. Triggers: \"deploy app\", \"create project\", \"add domain\", \"provision database\", \"dokploy compose\", \"manage dokploy\"."
---

# Dokploy MCP Tool Patterns

The official `@dokploy/mcp` server exposes **500+ tools across 49 categories**. Each tool is prefixed with `mcp__dokploy__`. This skill covers the core categories developers use day-to-day (projects, applications, domains, compose, databases) with full tool tables and workflow recipes. For the complete category index, see the **New Capabilities** section at the end.

To reduce the exposed tool surface, set `DOKPLOY_ENABLED_TAGS` in `.mcp.json` `env` to a comma-separated list of categories (e.g. `project,application,domain,compose,postgres,settings,deployment,docker`).

---

## Project Management (8 tools)

Projects are the top-level container. Every application, database, and compose stack belongs to a project. Always create or identify a project before creating resources.

| Tool | Description | Parameters |
|---|---|---|
| `mcp__dokploy__project-all` | List all projects | None |
| `mcp__dokploy__project-allForPermissions` | List projects the current token can access | None |
| `mcp__dokploy__project-one` | Get a single project by ID | `projectId` (string, required) |
| `mcp__dokploy__project-create` | Create a new project | `name` (string, required), `description` (string, optional) |
| `mcp__dokploy__project-update` | Update project metadata | `projectId` (string, required), `name` (string), `description` (string) |
| `mcp__dokploy__project-duplicate` | Duplicate a project and its resources | `projectId` (string, required) |
| `mcp__dokploy__project-remove` | Delete a project and all its resources | `projectId` (string, required) |
| `mcp__dokploy__project-search` | Search projects by name | `query` (string) |

### Usage notes

- `project-all` returns an array of project objects, each containing `projectId`, `name`, `description`, and nested arrays of applications, databases, and compose stacks.
- `project-remove` is destructive — it deletes all applications, databases, and compose stacks within the project. Confirm with the user before calling.
- `project-duplicate` creates a full copy including all nested resources. Use it for staging/production environment cloning.

---

## Application Management (30 tools)

Applications are the primary deployment unit. They support multiple source types (GitHub, GitLab, Bitbucket, Gitea, generic Git, Docker image) and build types (Nixpacks, Dockerfile, Buildpacks, Docker image).

### Core CRUD + Search (5 tools)

| Tool | Description | Key Parameters |
|---|---|---|
| `mcp__dokploy__application-one` | Get application details | `applicationId` |
| `mcp__dokploy__application-create` | Create a new application | `projectId`, `name`, `appName` (unique slug) |
| `mcp__dokploy__application-update` | Update application settings | `applicationId`, plus any updatable fields |
| `mcp__dokploy__application-delete` | Delete an application | `applicationId` |
| `mcp__dokploy__application-search` | Search applications by name | `query` |

### Lifecycle (5 tools)

| Tool | Description | Parameters |
|---|---|---|
| `mcp__dokploy__application-deploy` | Trigger a new deployment | `applicationId` |
| `mcp__dokploy__application-redeploy` | Redeploy with latest config | `applicationId` |
| `mcp__dokploy__application-start` | Start a stopped application | `applicationId` |
| `mcp__dokploy__application-stop` | Stop a running application | `applicationId` |
| `mcp__dokploy__application-reload` | Reload application (zero-downtime) | `applicationId` |

**Key distinction:** `deploy` builds from source and deploys. `redeploy` re-runs the last deployment with current config. `reload` restarts the running container without rebuilding.

### Git Provider Configuration (6 tools)

Connect an application to a Git source. Only one provider can be active at a time.

| Tool | Description | Key Parameters |
|---|---|---|
| `mcp__dokploy__application-saveGithubProvider` | Connect to GitHub | `applicationId`, `repository` (repo name only — NOT full URL), `branch`, `owner`, `githubId`, `enableSubmodules` |
| `mcp__dokploy__application-saveGitlabProvider` | Connect to GitLab | `applicationId`, `repository`, `branch`, `gitlabProjectId` |
| `mcp__dokploy__application-saveBitbucketProvider` | Connect to Bitbucket | `applicationId`, `repository`, `branch`, `owner` |
| `mcp__dokploy__application-saveGiteaProvider` | Connect to Gitea | `applicationId`, `repository`, `branch`, `owner` |
| `mcp__dokploy__application-saveGitProvider` | Connect to any Git URL | `applicationId`, `customGitUrl`, `customGitBranch`, `customGitBuildPath`, `enableSubmodules`, `watchPaths` |
| `mcp__dokploy__application-disconnectGitProvider` | Remove Git connection | `applicationId` |

**GitHub provider critical note:** The `repository` parameter for `saveGithubProvider` must be the **repository name only** (e.g. `"my-repo"`), NOT the full URL. Dokploy constructs the clone URL as `github.com/{owner}/{repository}` — passing a full URL like `https://github.com/org/repo` causes a broken double-URL (`github.com/org/https://github.com/org/repo`). You also need the `githubId` — get it from `gitProvider-getAll` (then filter by type `github`). Required fields: `applicationId`, `repository`, `branch`, `owner`, `githubId`, `enableSubmodules`, `triggerType` (default `"push"`), `watchPaths` (array, use `[]` if none), `buildPath` (default `"/"`).

**Generic Git provider note:** `saveGitProvider` requires ALL of: `applicationId`, `customGitUrl` (full SSH/HTTPS URL), `customGitBranch`, `customGitBuildPath` (e.g. `"/"`), `enableSubmodules` (boolean), `watchPaths` (array). Optionally `customGitSSHKeyId` for private repos. Omitting any required field causes a 400 validation error.

### Build & Environment Configuration (3 tools)

| Tool | Description | Key Parameters |
|---|---|---|
| `mcp__dokploy__application-saveBuildType` | Set build method | `applicationId`, `buildType` (`nixpacks`, `dockerfile`, `docker`, `buildpacks`) |
| `mcp__dokploy__application-saveEnvironment` | Set environment variables | `applicationId`, `env` (newline-separated KEY=VALUE string) |
| `mcp__dokploy__application-saveDockerProvider` | Set Docker image source | `applicationId`, `dockerImage`, `dockerTag` |

### Monitoring, Logs & Config (4 tools)

| Tool | Description | Parameters |
|---|---|---|
| `mcp__dokploy__application-readAppMonitoring` | Read monitoring metrics (CPU, memory, network) | `applicationId` |
| `mcp__dokploy__application-readLogs` | Stream container logs | `applicationId` |
| `mcp__dokploy__application-readTraefikConfig` | Read current Traefik routing config | `applicationId` |
| `mcp__dokploy__application-updateTraefikConfig` | Update Traefik routing rules | `applicationId`, `traefikConfig` (YAML string) |

### Deployment & Queue Management (7 tools)

| Tool | Description | Parameters |
|---|---|---|
| `mcp__dokploy__application-move` | Move application to another project | `applicationId`, `projectId` |
| `mcp__dokploy__application-markRunning` | Force-mark application as running | `applicationId` |
| `mcp__dokploy__application-cancelDeployment` | Cancel an in-progress deployment | `applicationId` |
| `mcp__dokploy__application-killBuild` | Kill the currently-running build process | `applicationId` |
| `mcp__dokploy__application-refreshToken` | Regenerate application webhook token | `applicationId` |
| `mcp__dokploy__application-cleanQueues` | Clear stuck deployment queues | `applicationId` |
| `mcp__dokploy__application-clearDeployments` | Purge historical deployment records | `applicationId` |
| `mcp__dokploy__application-dropDeployment` | Drop a specific deployment | `deploymentId` |

### Application usage notes

- `application-create` requires `projectId` and `name`. The `appName` parameter becomes the container name and must be unique across the server.
- `application-saveEnvironment` expects **all** of these parameters: `applicationId`, `env` (newline-separated KEY=VALUE string), `buildArgs` (newline-separated KEY=VALUE string for Docker build args — use empty string if none), `buildSecrets` (empty string if none), `createEnvFile` (boolean). Omitting any parameter causes a 400 validation error. Build args are critical for frameworks like Next.js where env vars (e.g. `NEXT_PUBLIC_*`) must be available during `docker build`.
- `application-saveBuildType` requires **all** of these parameters: `applicationId`, `buildType` (`nixpacks`, `dockerfile`, `docker`, `buildpacks`), `dockerfile` (filename, e.g. `"Dockerfile"`), `dockerContextPath` (e.g. `"."`), `dockerBuildStage` (empty string if none), `herokuVersion` (empty string if N/A), `railpackVersion` (empty string if N/A). Omitting any parameter causes a 400 validation error. When a project has a `Dockerfile`, default to `buildType: "dockerfile"` — ask the user to confirm.
- After calling `application-deploy`, the deployment runs asynchronously. Check deployment status via `deployment-all` filtered by `applicationId` to confirm completion. On failure, read logs with `application-readLogs` and iterate.
- `application-markRunning` is a manual override for stuck states. Use only when the container is running but Dokploy shows it as stopped.
- `application-cleanQueues` clears the deployment queue. Use when deployments are stuck in "queued" state. `application-killBuild` aborts a running build immediately.

---

## Domain Management (9 tools)

Domains map hostnames to applications or compose services. Dokploy uses Traefik as the reverse proxy.

| Tool | Description | Key Parameters |
|---|---|---|
| `mcp__dokploy__domain-byApplicationId` | List domains for an application | `applicationId` |
| `mcp__dokploy__domain-byComposeId` | List domains for a compose stack | `composeId` |
| `mcp__dokploy__domain-one` | Get a single domain by ID | `domainId` |
| `mcp__dokploy__domain-create` | Create a domain mapping | See below |
| `mcp__dokploy__domain-update` | Update domain settings | `domainId`, plus updatable fields |
| `mcp__dokploy__domain-delete` | Delete a domain | `domainId` |
| `mcp__dokploy__domain-validateDomain` | Check DNS resolution for a domain | `domainId` |
| `mcp__dokploy__domain-generateDomain` | Auto-generate a subdomain | `applicationId` or `composeId` |
| `mcp__dokploy__domain-canGenerateTraefikMeDomains` | Check if .traefik.me domains are available | None |

### `domain-create` parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `host` | string | Yes | Domain hostname (e.g. `app.example.com`) |
| `path` | string | No | URL path prefix (default: `/`) |
| `port` | number | No | Container port to route to (default: application's exposed port) |
| `applicationId` | string | Conditional | Application to attach to (mutually exclusive with `composeId`) |
| `composeId` | string | Conditional | Compose stack to attach to (mutually exclusive with `applicationId`) |
| `https` | boolean | No | Enable HTTPS with auto-cert (default: `false`) |
| `certificateType` | string | No | Certificate type: `letsencrypt`, `none` (default: `none`) |

### Domain usage notes

- Always call `domain-validateDomain` after creating a domain to confirm DNS is pointing to the server.
- `domain-generateDomain` creates a `.traefik.me` wildcard subdomain that resolves to the server's IP. Useful for development/testing without DNS setup.
- To enable HTTPS with Let's Encrypt, set `https: true` and `certificateType: "letsencrypt"`. The domain must have valid DNS pointing to the server for certificate issuance to succeed.
- A single application can have multiple domains. Use this for aliases or www/non-www setups.
- To list domains attached to a compose stack, use `domain-byComposeId` (the old `compose-fetchDomains` tool was removed — this is its direct replacement).

---

## Compose Management (29 tools)

Docker Compose stacks deploy multi-container applications defined by a `docker-compose.yml` file.

### Core CRUD & Lifecycle

| Tool | Description | Key Parameters |
|---|---|---|
| `mcp__dokploy__compose-one` | Get compose stack details | `composeId` |
| `mcp__dokploy__compose-create` | Create a compose stack | `projectId`, `name`, `appName` |
| `mcp__dokploy__compose-update` | Update compose settings + source (see note below) | `composeId`, updatable fields |
| `mcp__dokploy__compose-delete` | Delete a compose stack | `composeId` |
| `mcp__dokploy__compose-deploy` | Deploy the compose stack | `composeId` |
| `mcp__dokploy__compose-redeploy` | Redeploy with current config | `composeId` |
| `mcp__dokploy__compose-start` | Start compose services | `composeId` |
| `mcp__dokploy__compose-stop` | Stop all compose services | `composeId` |
| `mcp__dokploy__compose-move` | Move compose stack to another project | `composeId`, `projectId` |
| `mcp__dokploy__compose-search` | Search compose stacks by name | `query` |

### Source / Git Configuration

Unlike applications, compose git source is set **via `compose-update`**, not a separate `saveGithubProvider` call. Pass `sourceType` (`github` / `gitlab` / `bitbucket` / `gitea` / `git`), `repository`, `branch`, `owner`, `composePath`, and provider-specific IDs (`githubId`, `gitlabProjectId`, etc.) in a single update.

| Tool | Description | Key Parameters |
|---|---|---|
| `mcp__dokploy__compose-disconnectGitProvider` | Remove Git connection | `composeId` |
| `mcp__dokploy__compose-fetchSourceType` | Detect source type from repo | `composeId` |
| `mcp__dokploy__compose-import` | Import compose stack from external source | per-source fields |

### Templates

| Tool | Description | Key Parameters |
|---|---|---|
| `mcp__dokploy__compose-templates` | List available compose templates | None |
| `mcp__dokploy__compose-deployTemplate` | Deploy a compose template | `templateId`, `projectId`, `name` |
| `mcp__dokploy__compose-processTemplate` | Render a template with variables | `templateId`, variables |

### Build, Config & Logs

| Tool | Description | Key Parameters |
|---|---|---|
| `mcp__dokploy__compose-getDefaultCommand` | Get default docker compose command | `composeId` |
| `mcp__dokploy__compose-getConvertedCompose` | Validate and render the compose file | `composeId` |
| `mcp__dokploy__compose-loadServices` | List services defined in the stack | `composeId` |
| `mcp__dokploy__compose-loadMountsByService` | Inspect mounts per service | `composeId`, `serviceName` |
| `mcp__dokploy__compose-getTags` | List image tags used | `composeId` |
| `mcp__dokploy__compose-randomizeCompose` | Generate random ports for services | `composeId` |
| `mcp__dokploy__compose-saveEnvironment` | Set environment variables | `composeId`, `env` |
| `mcp__dokploy__compose-readLogs` | Stream compose service logs | `composeId` |

### Deployment Management

| Tool | Description | Key Parameters |
|---|---|---|
| `mcp__dokploy__compose-cancelDeployment` | Cancel in-progress deployment | `composeId` |
| `mcp__dokploy__compose-killBuild` | Kill the running build | `composeId` |
| `mcp__dokploy__compose-cleanQueues` | Clear stuck deployment queue | `composeId` |
| `mcp__dokploy__compose-clearDeployments` | Purge deployment history | `composeId` |
| `mcp__dokploy__compose-refreshToken` | Regenerate webhook token | `composeId` |
| `mcp__dokploy__compose-isolatedDeployment` | Toggle isolated deployment mode | `composeId`, boolean |

### Compose usage notes

- `compose-create` creates the stack record. After creation, set git source / compose file content via `compose-update`, then call `compose-deploy`.
- **Setting a git source for compose:** Use `compose-update` with `sourceType` and the matching provider fields. The old `compose-saveGithubProvider` / `compose-saveGitlabProvider` tools were consolidated into `compose-update` in the official MCP server.
- **Listing domains for a compose stack:** Use `domain-byComposeId` (not the removed `compose-fetchDomains`).
- `compose-saveEnvironment` works the same as the application equivalent — newline-separated `KEY=VALUE` string.
- `compose-getConvertedCompose` validates the compose file by rendering it with current env vars. Call this before `compose-deploy` to catch YAML errors early.

---

## Database Management (6 types × 16 tools each)

Dokploy supports six managed database types. Each type has an identical set of 16 tools following the same naming pattern (the official server adds `changePassword`, `readLogs`, and `search` on top of the 13 core tools).

### Tool pattern per database type

Replace `{type}` with `postgres`, `mysql`, `mariadb`, `mongo`, `redis`, or `libsql`:

| Tool | Description | Key Parameters |
|---|---|---|
| `mcp__dokploy__{type}-create` | Provision a new database | `projectId`, `name`, `appName`, `databasePassword` |
| `mcp__dokploy__{type}-one` | Get database details | `{type}Id` |
| `mcp__dokploy__{type}-update` | Update database config | `{type}Id`, updatable fields |
| `mcp__dokploy__{type}-remove` | Delete a database | `{type}Id` |
| `mcp__dokploy__{type}-move` | Move to another project | `{type}Id`, `projectId` |
| `mcp__dokploy__{type}-search` | Search databases by name | `query` |
| `mcp__dokploy__{type}-deploy` | Deploy/start the database container | `{type}Id` |
| `mcp__dokploy__{type}-start` | Start a stopped database | `{type}Id` |
| `mcp__dokploy__{type}-stop` | Stop a running database | `{type}Id` |
| `mcp__dokploy__{type}-reload` | Reload database container | `{type}Id` |
| `mcp__dokploy__{type}-rebuild` | Rebuild database container from scratch | `{type}Id` |
| `mcp__dokploy__{type}-changeStatus` | Force status change | `{type}Id`, `applicationStatus` |
| `mcp__dokploy__{type}-changePassword` | Rotate the database password | `{type}Id`, `newPassword` |
| `mcp__dokploy__{type}-saveExternalPort` | Expose database on a host port | `{type}Id`, `externalPort` |
| `mcp__dokploy__{type}-saveEnvironment` | Set database environment variables | `{type}Id`, `env` |
| `mcp__dokploy__{type}-readLogs` | Stream database container logs | `{type}Id` |

### Supported types

- **PostgreSQL** (`postgres-*`)
- **MySQL** (`mysql-*`)
- **MariaDB** (`mariadb-*`)
- **MongoDB** (`mongo-*`)
- **Redis** (`redis-*`)
- **LibSQL** (`libsql-*`) — new in the official server; embedded-SQL / SQLite-compatible managed service

### Database usage notes

- `{type}-create` requires `projectId`, `name`, and `appName`. For PostgreSQL, MySQL, MariaDB, MongoDB, and LibSQL, also provide `databasePassword`. For Redis, the password is optional. For MongoDB, also provide `databaseUser`.
- After `{type}-create`, call `{type}-deploy` to start the container. Creation only registers the resource.
- `{type}-saveExternalPort` exposes the database on the host network. Set `externalPort` to the desired port number. Set to `null` to remove external access.
- `{type}-rebuild` destroys and recreates the container. Data persists only if volumes are configured.
- `{type}-changeStatus` is a manual override. Use only when the actual container state differs from what Dokploy reports.
- `{type}-changePassword` rotates credentials without destroying data. Follow up by updating connection strings in dependent applications.

---

## Deployment History (5 tools)

| Tool | Description | Key Parameters |
|---|---|---|
| `mcp__dokploy__deployment-all` | List deployments, filterable by resource | `applicationId`, `composeId`, or `serverId` |
| `mcp__dokploy__deployment-allByCompose` | List deployments for a compose stack | `composeId` |
| `mcp__dokploy__deployment-allByServer` | List deployments for a server | `serverId` |
| `mcp__dokploy__deployment-allByType` | Filter by deployment type | `type` |
| `mcp__dokploy__deployment-allCentralized` | List deployments across all resources | None |
| `mcp__dokploy__deployment-queueList` | Inspect the deployment queue | None |
| `mcp__dokploy__deployment-killProcess` | Kill a running deployment process | `deploymentId` |
| `mcp__dokploy__deployment-removeDeployment` | Remove a deployment record | `deploymentId` |

To list deployments for a specific application, call `deployment-all` with the `applicationId` filter (the previous `deployment-allByApplication` tool has been consolidated into `deployment-all`).

---

## Common Workflow Patterns

### 1. Deploy a new application from GitHub

Execute these tools in sequence:

```
1. mcp__dokploy__project-create
   → { name: "my-project", description: "Production app" }
   → Returns: { projectId: "abc123" }

2. mcp__dokploy__application-create
   → { projectId: "abc123", name: "My App", appName: "my-app" }
   → Returns: { applicationId: "def456" }

3. mcp__dokploy__application-saveGithubProvider
   → { applicationId: "def456", repository: "my-repo", branch: "main", owner: "my-org" }

4. mcp__dokploy__application-saveBuildType
   → { applicationId: "def456", buildType: "dockerfile", dockerfile: "Dockerfile", dockerContextPath: ".", dockerBuildStage: "", herokuVersion: "", railpackVersion: "" }
   (Use "nixpacks" if no Dockerfile exists. Ask user which to use.)

5. mcp__dokploy__application-saveEnvironment
   → { applicationId: "def456", env: "DATABASE_URL=postgres://...\nNODE_ENV=production\nPORT=3000", buildArgs: "", buildSecrets: "", createEnvFile: false }

6. mcp__dokploy__domain-create
   → { applicationId: "def456", host: "app.example.com", https: true, certificateType: "letsencrypt", port: 3000 }

7. mcp__dokploy__application-deploy
   → { applicationId: "def456" }
```

After step 7, check the application status with `application-one` and deployment history with `deployment-all` filtered by `applicationId` to confirm the deployment succeeded. Stream logs with `application-readLogs` if it fails.

### 2. Provision a PostgreSQL database with external access

```
1. mcp__dokploy__project-create
   → { name: "databases" }
   → Returns: { projectId: "proj789" }
   (Or use project-all to find an existing project)

2. mcp__dokploy__postgres-create
   → { projectId: "proj789", name: "Main DB", appName: "main-db", databasePassword: "secure-password-here" }
   → Returns: { postgresId: "pg123" }

3. mcp__dokploy__postgres-deploy
   → { postgresId: "pg123" }

4. mcp__dokploy__postgres-saveExternalPort
   → { postgresId: "pg123", externalPort: 5432 }
```

The database is now accessible at `server-ip:5432`. Use the connection string: `postgres://postgres:secure-password-here@server-ip:5432/postgres`.

### 3. Add a domain with HTTPS to an existing application

```
1. mcp__dokploy__domain-create
   → { applicationId: "def456", host: "api.example.com", https: true, certificateType: "letsencrypt", port: 8080 }
   → Returns: { domainId: "dom789" }

2. mcp__dokploy__domain-validateDomain
   → { domainId: "dom789" }
```

If validation fails, the DNS A record for `api.example.com` is not pointing to the server's IP. Fix DNS and re-validate.

### 4. Deploy a Docker Compose stack

```
1. mcp__dokploy__project-create
   → { name: "compose-stack" }
   → Returns: { projectId: "proj456" }

2. mcp__dokploy__compose-create
   → { projectId: "proj456", name: "My Stack", appName: "my-stack" }
   → Returns: { composeId: "comp789" }

3. mcp__dokploy__compose-update
   → { composeId: "comp789", composeFile: "version: '3.8'\nservices:\n  web:\n    image: nginx:latest\n    ports:\n      - '80:80'" }

   (If sourcing compose from a git repo instead, pass sourceType/repository/branch/owner/composePath here too.)

4. mcp__dokploy__compose-saveEnvironment
   → { composeId: "comp789", env: "NGINX_HOST=example.com" }

5. mcp__dokploy__compose-getConvertedCompose
   → { composeId: "comp789" }   // validate the file before deploy

6. mcp__dokploy__compose-deploy
   → { composeId: "comp789" }
```

---

## Best Practices

### Project organization

- Create one project per logical application or environment (e.g. `production`, `staging`, `databases`).
- Use descriptive project names. Projects are the primary grouping mechanism in the Dokploy dashboard.
- Use `project-all` to find existing projects before creating new ones. Avoid duplicate projects.

### Application deployment

- Always call `application-saveBuildType` before the first deployment. The default may not match your application.
- Use `application-redeploy` for subsequent deployments after config changes. Do not delete and recreate.
- Use `application-reload` for zero-downtime restarts when only environment variables changed.
- Set environment variables with `application-saveEnvironment` before deploying. Deploying first and then setting env vars requires a redeploy.
- Check deployment status after calling `application-deploy` — the call is asynchronous and returns immediately. Use `deployment-all` with `applicationId` filter and `application-readLogs` for failure diagnosis.

### Domain management

- Always call `domain-validateDomain` after creating a domain. Do not assume DNS is configured.
- For HTTPS, ensure DNS is pointing to the server before creating the domain with `certificateType: "letsencrypt"`. Let's Encrypt validation will fail otherwise.
- Use `domain-generateDomain` for quick testing without DNS setup. These `.traefik.me` domains resolve to the server IP automatically.

### Database operations

- All six database types follow the same tool pattern. Learn one, and you know all six.
- Always call `{type}-deploy` after `{type}-create`. Creation only registers the resource in Dokploy.
- Use `{type}-saveExternalPort` only when external access is needed (e.g. for development tools). In production, prefer internal Docker networking.
- Never use `{type}-rebuild` in production without confirming volume persistence. Rebuild destroys the container.
- Rotate credentials with `{type}-changePassword` rather than recreating the database.

### General

- Use `project-all` and `application-one` to inspect current state before making changes.
- Prefer `redeploy` over `deploy` for updates — `deploy` may trigger a full rebuild from source.
- Always confirm destructive operations (`project-remove`, `application-delete`, `{type}-remove`) with the user before executing.

---

## Error Handling

| Error | Cause | Solution |
|---|---|---|
| `"Project not found"` | Invalid `projectId` | Call `project-all` to get valid IDs |
| `"Application not found"` | Invalid `applicationId` | Call `project-one` with the project ID to list its applications |
| `"appName already exists"` | Duplicate `appName` | Choose a unique `appName` — it must be unique across the entire server |
| `"Build failed"` | Source code or Dockerfile error | Check application logs with `application-readLogs`; fix source and redeploy |
| `"Deploy timeout"` | Container takes too long to start | Check health check config; increase timeout or fix startup |
| `"Port already in use"` | Another container uses the same port | Choose a different `externalPort` or stop the conflicting container |
| `"Certificate issuance failed"` | DNS not pointing to server | Verify DNS A record, then retry. Remove and recreate the domain if needed |
| `"Provider not configured"` | No Git source set on application | Call `application-saveGithubProvider` (or another provider) before deploying |
| `"Queue is full"` | Too many pending deployments | Call `application-cleanQueues` to clear stuck deployments |
| `"Database connection refused"` | Database not deployed or port not exposed | Call `{type}-deploy` first, then `{type}-saveExternalPort` if external access is needed |
| MCP timeout | Network issue or Dokploy server overloaded | Retry the call; check server health with `curl $DOKPLOY_URL/api/settings.health` |
| `"Unauthorized"` | Invalid or expired API key | Regenerate the API key in the Dokploy dashboard and update `userConfig` |
| `"UNAUTHORIZED"` from REST API | Wrong auth header format | Dokploy uses `x-api-key: <token>` header, NOT `Authorization: Bearer <token>`. This applies to both trpc endpoints and direct REST calls |

---

## Tool Count Summary

The official `@dokploy/mcp` server exposes **508 tools across 49 categories**. Core categories covered by this skill:

| Category | Approx Count | Prefix |
|---|---|---|
| Project Management | 8 | `project-` |
| Application Management | 30 | `application-` |
| Domain Management | 9 | `domain-` |
| Compose Management | 29 | `compose-` |
| PostgreSQL | 16 | `postgres-` |
| MySQL | 16 | `mysql-` |
| MariaDB | 16 | `mariadb-` |
| MongoDB | 16 | `mongo-` |
| Redis | 16 | `redis-` |
| LibSQL | 16 | `libsql-` |
| Deployment History | 8 | `deployment-` |

Use `DOKPLOY_ENABLED_TAGS` in `.mcp.json` to restrict exposure to a subset of categories. See the **New Capabilities** section below for the remaining 39 categories.

---

## New Capabilities (official server)

The following categories are available in the official `@dokploy/mcp` server beyond the core dev workflow. Tool names follow the same `mcp__dokploy__<category>-<op>` pattern.

| Category | Prefix | Purpose |
|---|---|---|
| Environments | `environment-` | Per-project environments (create, duplicate, list, update, remove) |
| Preview Deployments | `previewDeployment-` | Ephemeral per-PR / per-branch deploys |
| Rollback | `rollback-` | Roll an application back to a previous deployment |
| Schedules | `schedule-` | Cron-like scheduled tasks (runManually, list, create, update, delete) |
| Backups | `backup-` | Configure and run manual backups for each resource type (compose, postgres, mysql, mariadb, mongo, libsql, webServer) + list backup files |
| Volume Backups | `volumeBackups-` | Backup persistent volumes |
| Registries | `registry-` | Private Docker registry credentials |
| Destinations | `destination-` | S3 / R2 / remote destinations for backups |
| Mounts | `mounts-` | File/volume mounts for an application or service |
| Ports | `port-` | Exposed host ports |
| Redirects | `redirects-` | HTTP redirect rules |
| Security | `security-` | Per-app security rules / basic auth |
| Certificates | `certificates-` | Custom TLS certificates |
| Notifications | `notification-` | Discord, Slack, Telegram, Email, Gotify, Ntfy, Mattermost, Teams, Pushover, Resend, Lark, custom webhooks |
| Servers | `server-` | Managed remote servers (add, setup, metrics, security, SSH) |
| Clusters / Swarm | `cluster-` / `swarm-` | Docker Swarm cluster nodes, stats, container inspection |
| Docker | `docker-` | Raw Docker operations on managed servers (containers, stats, exec) |
| SSH Keys | `sshKey-` | Manage SSH keys used for git or server access |
| Git Providers | `gitProvider-` / `github-` / `gitlab-` / `bitbucket-` / `gitea-` | Per-provider CRUD, branches, repos, test connection |
| Organizations | `organization-` | Multi-tenant orgs, invitations, members |
| Users | `user-` | Users, API keys, permissions, invitations, bookmarks |
| Custom Roles | `customRole-` | Fine-grained role definitions |
| SSO | `sso-` | Single sign-on providers + trusted origins |
| Tags | `tag-` | Tag resources for grouping |
| Patches | `patch-` | Inject patch files into deployments |
| AI | `ai-` | Configure AI providers used by Dokploy's assistant + log analysis |
| Settings | `settings-` | Server-wide settings, Traefik config, health, version, cleanup jobs |
| Audit Log | `auditLog-` | Read audit log entries |
| License Key | `licenseKey-` | Enterprise license + feature toggles |
| Whitelabeling | `whitelabeling-` | Branding customization |
| Stripe | `stripe-` | Cloud billing integration |
| Admin | `admin-` | Admin-only operations (e.g. monitoring setup) |

For the authoritative list, see https://github.com/Dokploy/mcp.

---

## REST API Fallback

If MCP tools fail (e.g. "Resource not found" errors), use the Dokploy trpc REST API directly via `curl`. Dokploy uses **`x-api-key`** header for authentication (NOT `Authorization: Bearer`). API paths live at `/api/…` under the base `$DOKPLOY_URL`.

### Authentication

```bash
# Correct — use x-api-key header and /api path
curl -s "$DOKPLOY_URL/api/project.all" \
  -H "x-api-key: $DOKPLOY_API_KEY"

# Wrong — Bearer auth returns 401
curl -s "$DOKPLOY_URL/api/project.all" \
  -H "Authorization: Bearer $DOKPLOY_API_KEY"
```

### Read operations (GET with input)

URL-encode the JSON input as a query parameter:

```bash
curl -s "$DOKPLOY_URL/api/application.one?input=%7B%22json%22%3A%7B%22applicationId%22%3A%22abc123%22%7D%7D" \
  -H "x-api-key: $DOKPLOY_API_KEY"
```

### Write operations (POST with JSON body)

```bash
curl -s -X POST "$DOKPLOY_URL/api/application.deploy" \
  -H "x-api-key: $DOKPLOY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"json":{"applicationId":"abc123"}}'
```

### Health check (no auth required)

```bash
curl -s "$DOKPLOY_URL/api/settings.health"
```
