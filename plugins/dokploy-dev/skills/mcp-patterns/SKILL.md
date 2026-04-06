---
name: mcp-patterns
description: "This skill should be used when deploying applications, managing projects, provisioning databases, configuring domains, working with Docker Compose, or performing any Dokploy operation via MCP tools. Triggers: \"deploy app\", \"create project\", \"add domain\", \"provision database\", \"dokploy compose\", \"manage dokploy\"."
---

# Dokploy MCP Tool Patterns

All 67 MCP tools for Dokploy, organized by category. Each tool is prefixed with `mcp__dokploy__`. Use these tools to manage projects, deploy applications, provision databases, configure domains, and operate Docker Compose stacks.

---

## Project Management (6 tools)

Projects are the top-level container. Every application, database, and compose stack belongs to a project. Always create or identify a project before creating resources.

| Tool | Description | Parameters |
|---|---|---|
| `mcp__dokploy__project-all` | List all projects | None |
| `mcp__dokploy__project-one` | Get a single project by ID | `projectId` (string, required) |
| `mcp__dokploy__project-create` | Create a new project | `name` (string, required), `description` (string, optional) |
| `mcp__dokploy__project-update` | Update project metadata | `projectId` (string, required), `name` (string), `description` (string) |
| `mcp__dokploy__project-duplicate` | Duplicate a project and its resources | `projectId` (string, required) |
| `mcp__dokploy__project-remove` | Delete a project and all its resources | `projectId` (string, required) |

### Usage notes

- `project-all` returns an array of project objects, each containing `projectId`, `name`, `description`, and nested arrays of applications, databases, and compose stacks.
- `project-remove` is destructive — it deletes all applications, databases, and compose stacks within the project. Confirm with the user before calling.
- `project-duplicate` creates a full copy including all nested resources. Use it for staging/production environment cloning.

---

## Application Management (26 tools)

Applications are the primary deployment unit. They support multiple source types (GitHub, GitLab, Bitbucket, Gitea, generic Git, Docker image) and build types (Nixpacks, Dockerfile, Buildpacks, Docker image).

### Core CRUD (4 tools)

| Tool | Description | Key Parameters |
|---|---|---|
| `mcp__dokploy__application-one` | Get application details | `applicationId` |
| `mcp__dokploy__application-create` | Create a new application | `projectId`, `name`, `appName` (unique slug) |
| `mcp__dokploy__application-update` | Update application settings | `applicationId`, plus any updatable fields |
| `mcp__dokploy__application-delete` | Delete an application | `applicationId` |

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
| `mcp__dokploy__application-saveGithubProvider` | Connect to GitHub | `applicationId`, `repository`, `branch`, `owner` |
| `mcp__dokploy__application-saveGitlabProvider` | Connect to GitLab | `applicationId`, `repository`, `branch`, `gitlabProjectId` |
| `mcp__dokploy__application-saveBitbucketProvider` | Connect to Bitbucket | `applicationId`, `repository`, `branch`, `owner` |
| `mcp__dokploy__application-saveGiteaProvider` | Connect to Gitea | `applicationId`, `repository`, `branch`, `owner` |
| `mcp__dokploy__application-saveGitProvider` | Connect to any Git URL | `applicationId`, `repositoryURL`, `branch` |
| `mcp__dokploy__application-disconnectGitProvider` | Remove Git connection | `applicationId` |

### Build & Environment Configuration (3 tools)

| Tool | Description | Key Parameters |
|---|---|---|
| `mcp__dokploy__application-saveBuildType` | Set build method | `applicationId`, `buildType` (`nixpacks`, `dockerfile`, `docker`, `buildpacks`) |
| `mcp__dokploy__application-saveEnvironment` | Set environment variables | `applicationId`, `env` (newline-separated KEY=VALUE string) |
| `mcp__dokploy__application-saveDockerProvider` | Set Docker image source | `applicationId`, `dockerImage`, `dockerTag` |

### Monitoring & Config (3 tools)

| Tool | Description | Parameters |
|---|---|---|
| `mcp__dokploy__application-readAppMonitoring` | Read monitoring metrics (CPU, memory, network) | `applicationId` |
| `mcp__dokploy__application-readTraefikConfig` | Read current Traefik routing config | `applicationId` |
| `mcp__dokploy__application-updateTraefikConfig` | Update Traefik routing rules | `applicationId`, `traefikConfig` (YAML string) |

### Other Operations (5 tools)

| Tool | Description | Parameters |
|---|---|---|
| `mcp__dokploy__application-move` | Move application to another project | `applicationId`, `projectId` |
| `mcp__dokploy__application-markRunning` | Force-mark application as running | `applicationId` |
| `mcp__dokploy__application-cancelDeployment` | Cancel an in-progress deployment | `applicationId` |
| `mcp__dokploy__application-refreshToken` | Regenerate application webhook token | `applicationId` |
| `mcp__dokploy__application-cleanQueues` | Clear stuck deployment queues | `applicationId` |

### Application usage notes

- `application-create` requires `projectId` and `name`. The `appName` parameter becomes the container name and must be unique across the server.
- `application-saveEnvironment` expects **all** of these parameters: `applicationId`, `env` (newline-separated KEY=VALUE string), `buildArgs` (newline-separated KEY=VALUE string for Docker build args — use empty string if none), `buildSecrets` (empty string if none), `createEnvFile` (boolean). Omitting any parameter causes a 400 validation error. Build args are critical for frameworks like Next.js where env vars (e.g. `NEXT_PUBLIC_*`) must be available during `docker build`.
- `application-saveBuildType` requires **all** of these parameters: `applicationId`, `buildType` (`nixpacks`, `dockerfile`, `docker`, `buildpacks`), `dockerfile` (filename, e.g. `"Dockerfile"`), `dockerContextPath` (e.g. `"."`), `dockerBuildStage` (empty string if none), `herokuVersion` (empty string if N/A), `railpackVersion` (empty string if N/A). Omitting any parameter causes a 400 validation error. When a project has a `Dockerfile`, default to `buildType: "dockerfile"` — ask the user to confirm.
- After calling `application-deploy`, the deployment runs asynchronously. Check deployment status via `deployment.all?applicationId=<id>` to confirm completion. On failure, read logs and iterate.
- `application-markRunning` is a manual override for stuck states. Use only when the container is running but Dokploy shows it as stopped.
- `application-cleanQueues` clears the deployment queue. Use when deployments are stuck in "queued" state.

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

---

## Compose Management (11 tools)

Docker Compose stacks allow deploying multi-container applications defined by a `docker-compose.yml` file.

| Tool | Description | Key Parameters |
|---|---|---|
| `mcp__dokploy__compose-one` | Get compose stack details | `composeId` |
| `mcp__dokploy__compose-create` | Create a compose stack | `projectId`, `name`, `appName` |
| `mcp__dokploy__compose-update` | Update compose settings | `composeId`, updatable fields |
| `mcp__dokploy__compose-delete` | Delete a compose stack | `composeId` |
| `mcp__dokploy__compose-deploy` | Deploy the compose stack | `composeId` |
| `mcp__dokploy__compose-stop` | Stop all compose services | `composeId` |
| `mcp__dokploy__compose-getDefaultCommand` | Get default docker compose command | `composeId` |
| `mcp__dokploy__compose-fetchDomains` | List domains for compose services | `composeId` |
| `mcp__dokploy__compose-randomizeCompose` | Generate random ports for services | `composeId` |
| `mcp__dokploy__compose-saveEnvironment` | Set environment variables | `composeId`, `env` |
| `mcp__dokploy__compose-saveGithubProvider` | Connect to GitHub repository | `composeId`, `repository`, `branch`, `owner` |

### Compose usage notes

- `compose-create` creates the stack container. After creation, update the compose file content via `compose-update` and then call `compose-deploy`.
- `compose-saveEnvironment` works the same as the application equivalent — newline-separated `KEY=VALUE` string.
- `compose-deploy` pulls images and starts all services defined in the compose file.
- Use `compose-fetchDomains` to see which services have domain mappings before adding new ones.

---

## Database Management (65 tools — 13 per type)

Dokploy supports five managed database types. Each type has an identical set of 13 tools following the same naming pattern.

### Tool pattern per database type

Replace `{type}` with `postgres`, `mysql`, `mariadb`, `mongo`, or `redis`:

| Tool | Description | Key Parameters |
|---|---|---|
| `mcp__dokploy__{type}-create` | Provision a new database | `projectId`, `name`, `appName`, `databasePassword` |
| `mcp__dokploy__{type}-one` | Get database details | `{type}Id` |
| `mcp__dokploy__{type}-update` | Update database config | `{type}Id`, updatable fields |
| `mcp__dokploy__{type}-remove` | Delete a database | `{type}Id` |
| `mcp__dokploy__{type}-move` | Move to another project | `{type}Id`, `projectId` |
| `mcp__dokploy__{type}-deploy` | Deploy/start the database container | `{type}Id` |
| `mcp__dokploy__{type}-start` | Start a stopped database | `{type}Id` |
| `mcp__dokploy__{type}-stop` | Stop a running database | `{type}Id` |
| `mcp__dokploy__{type}-reload` | Reload database container | `{type}Id` |
| `mcp__dokploy__{type}-rebuild` | Rebuild database container from scratch | `{type}Id` |
| `mcp__dokploy__{type}-changeStatus` | Force status change | `{type}Id`, `applicationStatus` |
| `mcp__dokploy__{type}-saveExternalPort` | Expose database on a host port | `{type}Id`, `externalPort` |
| `mcp__dokploy__{type}-saveEnvironment` | Set database environment variables | `{type}Id`, `env` |

### PostgreSQL tools (prefix: `postgres-`)

`mcp__dokploy__postgres-create`, `mcp__dokploy__postgres-one`, `mcp__dokploy__postgres-update`, `mcp__dokploy__postgres-remove`, `mcp__dokploy__postgres-move`, `mcp__dokploy__postgres-deploy`, `mcp__dokploy__postgres-start`, `mcp__dokploy__postgres-stop`, `mcp__dokploy__postgres-reload`, `mcp__dokploy__postgres-rebuild`, `mcp__dokploy__postgres-changeStatus`, `mcp__dokploy__postgres-saveExternalPort`, `mcp__dokploy__postgres-saveEnvironment`

### MySQL tools (prefix: `mysql-`)

`mcp__dokploy__mysql-create`, `mcp__dokploy__mysql-one`, `mcp__dokploy__mysql-update`, `mcp__dokploy__mysql-remove`, `mcp__dokploy__mysql-move`, `mcp__dokploy__mysql-deploy`, `mcp__dokploy__mysql-start`, `mcp__dokploy__mysql-stop`, `mcp__dokploy__mysql-reload`, `mcp__dokploy__mysql-rebuild`, `mcp__dokploy__mysql-changeStatus`, `mcp__dokploy__mysql-saveExternalPort`, `mcp__dokploy__mysql-saveEnvironment`

### MariaDB tools (prefix: `mariadb-`)

`mcp__dokploy__mariadb-create`, `mcp__dokploy__mariadb-one`, `mcp__dokploy__mariadb-update`, `mcp__dokploy__mariadb-remove`, `mcp__dokploy__mariadb-move`, `mcp__dokploy__mariadb-deploy`, `mcp__dokploy__mariadb-start`, `mcp__dokploy__mariadb-stop`, `mcp__dokploy__mariadb-reload`, `mcp__dokploy__mariadb-rebuild`, `mcp__dokploy__mariadb-changeStatus`, `mcp__dokploy__mariadb-saveExternalPort`, `mcp__dokploy__mariadb-saveEnvironment`

### MongoDB tools (prefix: `mongo-`)

`mcp__dokploy__mongo-create`, `mcp__dokploy__mongo-one`, `mcp__dokploy__mongo-update`, `mcp__dokploy__mongo-remove`, `mcp__dokploy__mongo-move`, `mcp__dokploy__mongo-deploy`, `mcp__dokploy__mongo-start`, `mcp__dokploy__mongo-stop`, `mcp__dokploy__mongo-reload`, `mcp__dokploy__mongo-rebuild`, `mcp__dokploy__mongo-changeStatus`, `mcp__dokploy__mongo-saveExternalPort`, `mcp__dokploy__mongo-saveEnvironment`

### Redis tools (prefix: `redis-`)

`mcp__dokploy__redis-create`, `mcp__dokploy__redis-one`, `mcp__dokploy__redis-update`, `mcp__dokploy__redis-remove`, `mcp__dokploy__redis-move`, `mcp__dokploy__redis-deploy`, `mcp__dokploy__redis-start`, `mcp__dokploy__redis-stop`, `mcp__dokploy__redis-reload`, `mcp__dokploy__redis-rebuild`, `mcp__dokploy__redis-changeStatus`, `mcp__dokploy__redis-saveExternalPort`, `mcp__dokploy__redis-saveEnvironment`

### Database usage notes

- `{type}-create` requires `projectId`, `name`, and `appName`. For PostgreSQL, MySQL, and MariaDB, also provide `databasePassword`. For Redis, the password is optional. For MongoDB, provide `databaseUser` and `databasePassword`.
- After `{type}-create`, call `{type}-deploy` to start the container. Creation only registers the resource.
- `{type}-saveExternalPort` exposes the database on the host network. Set `externalPort` to the desired port number. Set to `null` to remove external access.
- `{type}-rebuild` destroys and recreates the container. Data persists only if volumes are configured.
- `{type}-changeStatus` is a manual override. Use only when the actual container state differs from what Dokploy reports.

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

After step 7, check the application status with `application-one` to confirm the deployment succeeded.

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

4. mcp__dokploy__compose-saveEnvironment
   → { composeId: "comp789", env: "NGINX_HOST=example.com" }

5. mcp__dokploy__compose-deploy
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
- Check deployment status after calling `application-deploy` — the call is asynchronous and returns immediately.

### Domain management

- Always call `domain-validateDomain` after creating a domain. Do not assume DNS is configured.
- For HTTPS, ensure DNS is pointing to the server before creating the domain with `certificateType: "letsencrypt"`. Let's Encrypt validation will fail otherwise.
- Use `domain-generateDomain` for quick testing without DNS setup. These `.traefik.me` domains resolve to the server IP automatically.

### Database operations

- All five database types follow the same tool pattern. Learn one, and you know all five.
- Always call `{type}-deploy` after `{type}-create`. Creation only registers the resource in Dokploy.
- Use `{type}-saveExternalPort` only when external access is needed (e.g. for development tools). In production, prefer internal Docker networking.
- Never use `{type}-rebuild` in production without confirming volume persistence. Rebuild destroys the container.

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
| `"Build failed"` | Source code or Dockerfile error | Check application logs; fix source and redeploy |
| `"Deploy timeout"` | Container takes too long to start | Check health check config; increase timeout or fix startup |
| `"Port already in use"` | Another container uses the same port | Choose a different `externalPort` or stop the conflicting container |
| `"Certificate issuance failed"` | DNS not pointing to server | Verify DNS A record, then retry. Remove and recreate the domain if needed |
| `"Provider not configured"` | No Git source set on application | Call `application-saveGithubProvider` (or another provider) before deploying |
| `"Queue is full"` | Too many pending deployments | Call `application-cleanQueues` to clear stuck deployments |
| `"Database connection refused"` | Database not deployed or port not exposed | Call `{type}-deploy` first, then `{type}-saveExternalPort` if external access is needed |
| MCP timeout | Network issue or Dokploy server overloaded | Retry the call; check server health with `curl ${dokploy_url}/settings.health` |
| `"Unauthorized"` | Invalid or expired API key | Regenerate the API key in the Dokploy dashboard and update `userConfig` |

---

## Tool Count Summary

| Category | Count | Prefix |
|---|---|---|
| Project Management | 6 | `project-` |
| Application Management | 26 | `application-` |
| Domain Management | 9 | `domain-` |
| Compose Management | 11 | `compose-` |
| PostgreSQL | 13 | `postgres-` |
| MySQL | 13 | `mysql-` |
| MariaDB | 13 | `mariadb-` |
| MongoDB | 13 | `mongo-` |
| Redis | 13 | `redis-` |
| **Total** | **117** | |

> Note: The plugin description references 67 MCP tools. The actual count depends on which database types and compose tools are exposed by your Dokploy MCP server version. The table above lists all possible tools. Use `project-all` as a connectivity test — if it works, all other tools in the same category are available.
