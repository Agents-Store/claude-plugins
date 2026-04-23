---
name: troubleshoot
description: "This skill should be used when diagnosing Dokploy deployment failures, domain issues, database connection problems, or Docker/Traefik errors. Use when a deployment fails, domain is not resolving, database cannot connect, app returns 502, or MCP tools return errors. Triggers: \"dokploy error\", \"deployment failed\", \"domain not working\", \"502 bad gateway\", \"database connection refused\", \"dokploy debug\"."
---

# Dokploy Troubleshooting

Diagnose and resolve common Dokploy problems. Work through the relevant section based on the symptom reported.

---

## Quick Diagnostics Checklist

Run these checks first to understand the current state:

1. **Check Dokploy health:**
   ```bash
   curl -s "$DOKPLOY_URL/api/settings.health" \
     -H "x-api-key: $DOKPLOY_API_KEY"
   ```

2. **Check Dokploy version:** Call `mcp__dokploy__settings-getDokployVersion`

3. **List recent deployments:** Call `mcp__dokploy__deployment-allCentralized`

4. **Check Docker containers:** Call `mcp__dokploy__docker-getContainers`

If the health check fails, the server itself is down. Fix the server before investigating application-level issues.

---

## Domain Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Domain not resolving | DNS not pointed to server | Add an A record pointing to the server IP. Use `mcp__dokploy__server-publicIp` to get the IP |
| Domain resolves but returns 404 | Wrong port in domain config | Check the app's listening port (Next.js: 3000, Laravel: 8000). Update the domain config with the correct port |
| SSL certificate error | Domain added before DNS propagation | Delete the domain, wait for DNS propagation (up to 10 minutes), then re-add with HTTPS enabled |
| 502 Bad Gateway | App crashed or not listening on 0.0.0.0 | Check app logs. The app MUST listen on `0.0.0.0`, NOT `127.0.0.1`. This is the most common cause of 502s |
| traefik.me not working | Server blocks traefik.me DNS | Call `mcp__dokploy__domain-canGenerateTraefikMeDomains` to check support. If blocked, use a real domain instead |
| Mixed content errors | App serves HTTP behind HTTPS proxy | Set the app's `FORCE_SSL` or equivalent env var, or configure Traefik to handle HTTPS termination |

### Domain debugging steps

1. Verify DNS resolves to the correct IP:
   ```bash
   dig +short example.com
   ```

2. Check if Traefik is receiving the request:
   ```bash
   curl -vk https://example.com 2>&1 | head -30
   ```

3. Verify the domain configuration in Dokploy:
   Call `mcp__dokploy__application-one` with the applicationId and inspect the `domains` array.

4. Validate the domain:
   Call `mcp__dokploy__domain-validateDomain` with the domainId.

---

## Deployment Failures

| Symptom | Cause | Fix |
|---------|-------|-----|
| Build fails | Wrong build type | Check the build type matches the source. Use Nixpacks for auto-detect, Dockerfile if a Dockerfile exists in the repo |
| Build succeeds but app crashes | Missing environment variables | Check the environment config with `mcp__dokploy__application-one` and verify all required env vars are set |
| Deployment stuck in queue | Previous deployment blocking | Call `mcp__dokploy__application-cleanQueues` to clear the queue, or `mcp__dokploy__application-cancelDeployment` to cancel the blocking deployment |
| Git clone fails | Wrong repo URL or credentials | Verify the git provider config. Re-authenticate with the per-provider update tool: `mcp__dokploy__github-update`, `mcp__dokploy__gitlab-update`, `mcp__dokploy__bitbucket-update`, or `mcp__dokploy__gitea-update` |
| Nixpacks build fails | Unsupported language/framework | Check Nixpacks docs for supported runtimes. Alternatively, switch to Dockerfile build type |
| Build timeout | Large image or slow network | Increase build timeout or optimize the Dockerfile (use multi-stage builds, reduce layers) |

### Deployment debugging steps

1. **List deployments and find the latest:**
   ```bash
   curl -s -H "x-api-key: $DOKPLOY_API_KEY" \
     "$DOKPLOY_URL/api/deployment.all?applicationId=<id>" | python3 -m json.tool
   ```
   Or call `mcp__dokploy__deployment-all` with `applicationId` as the filter.

2. **Read deployment build logs:**
   Call `mcp__dokploy__application-readLogs` with the applicationId to stream container logs directly. For historical build logs, Dokploy stores files at `/etc/dokploy/logs/<appName>/<appName>-<timestamp>.log` on the server. If Beszel is available, use `beszel-getContainerLogs` on the Dokploy container to see recent build output including error traces. The Dokploy container ID can be found via `beszel-get_collections_containers_records` on the dokploy-server system.

3. **Check application status:**
   Call `mcp__dokploy__application-one` with the applicationId. Look at the `applicationStatus` field.

4. **Check the container is running:**
   Call `mcp__dokploy__docker-getContainers` and find the container matching the app name.

---

## Database Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Cannot connect externally | No external port set | Call `mcp__dokploy__postgres-saveExternalPort` (or the mysql/mariadb/mongo/redis equivalent) to expose a port |
| Connection refused | Database not deployed | Call `mcp__dokploy__postgres-deploy` (or equivalent for other database types) to start the container |
| Authentication failed | Wrong credentials | Check the database password in Dokploy. Call `mcp__dokploy__postgres-one` to inspect the config |
| Connection string wrong | Missing host or port | The internal hostname is the container name. The external host is the server IP with the external port |
| Database too slow | No resource limits set | Set memory and CPU limits via the database advanced settings |

### Database connection string patterns

| Database | Internal connection string |
|----------|--------------------------|
| PostgreSQL | `postgresql://user:password@container-name:5432/dbname` |
| MySQL | `mysql://user:password@container-name:3306/dbname` |
| MariaDB | `mysql://user:password@container-name:3306/dbname` |
| MongoDB | `mongodb://user:password@container-name:27017/dbname` |
| Redis | `redis://default:password@container-name:6379` |

For external access, replace `container-name` with the server IP and use the external port.

---

## Docker / Compose Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Compose deploy fails | Invalid docker-compose.yml | Call `mcp__dokploy__compose-getConvertedCompose` to validate the file before deploying |
| Volume paths wrong | Relative paths incorrect | Docker Compose volumes in Dokploy use `../files/data:/var/lib/data` pattern for persistent data |
| Container keeps restarting | App crash loop | Check container logs, verify env vars, check resource limits with `mcp__dokploy__docker-getContainers` |
| Image pull fails | Wrong registry credentials | Verify registry auth with `mcp__dokploy__registry-all`. Re-add credentials if needed |
| Port conflicts | Two services on the same port | Check exposed ports across all apps. Use `mcp__dokploy__docker-getContainers` to find conflicts |
| Network issues between containers | Containers on different networks | Compose services share a network by default. Standalone apps need to be on the same Docker network |

### Compose debugging steps

1. Validate the compose file:
   Call `mcp__dokploy__compose-getConvertedCompose` with the composeId.

2. Check running services:
   Call `mcp__dokploy__compose-loadServices` with the composeId.

3. Inspect container logs for a specific service:
   Use Docker CLI on the server or check via the Dokploy dashboard.

---

## MCP Connection Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| MCP tools not found | Plugin not enabled or npx failed | Re-enable the plugin. Verify `npx -y @dokploy/mcp` works locally |
| MCP returns "Invalid URL" | `DOKPLOY_URL` env var not set or has wrong format | `DOKPLOY_URL` must be the **base URL without `/api`** (e.g. `https://dokploy.example.com`). Check `settings.local.json` `env` block. If MCP tools still fail, fall back to direct `curl` calls with `x-api-key` header (see Diagnostic Commands below) |
| MCP returns 401 | Invalid API key or wrong auth header | Dokploy API uses `x-api-key` header, NOT `Authorization: Bearer`. Regenerate the API key in the Dokploy dashboard (**Settings > API/Tokens**). Update `userConfig` |
| MCP returns connection refused | Wrong DOKPLOY_URL | The URL should be the base Dokploy URL (e.g. `https://dokploy.example.com`). API routes are at `/api/…` under it |
| Too many tools / context bloat | All 500+ tools exposed | Set `DOKPLOY_ENABLED_TAGS` in `.mcp.json` `env` to a comma-separated category list (e.g. `project,application,domain,compose,postgres,settings,deployment`) |
| MCP timeout | Server overloaded or network latency | Check server health. Increase timeout in MCP client config if the server is slow |
| MCP returns 500 | Server-side error | Check Dokploy server logs. This usually indicates a bug or corrupt state |

---

## Diagnostic Commands

### Via curl

```bash
# Check Dokploy server health
curl -s "$DOKPLOY_URL/api/settings.health" \
  -H "x-api-key: $DOKPLOY_API_KEY"

# Check Dokploy version
curl -s "$DOKPLOY_URL/api/settings.getDokployVersion" \
  -H "x-api-key: $DOKPLOY_API_KEY"

# List all Docker containers
curl -s "$DOKPLOY_URL/api/docker.getContainers" \
  -H "x-api-key: $DOKPLOY_API_KEY"

# Get server public IP
curl -s "$DOKPLOY_URL/api/server.publicIp" \
  -H "x-api-key: $DOKPLOY_API_KEY"

# List all projects with their applications
curl -s "$DOKPLOY_URL/api/project.all" \
  -H "x-api-key: $DOKPLOY_API_KEY"
```

### Via MCP tools

```
mcp__dokploy__settings-health
mcp__dokploy__settings-getDokployVersion
mcp__dokploy__docker-getContainers
mcp__dokploy__server-publicIp
mcp__dokploy__project-all
```

---

## When to Escalate

- **Traefik configuration issues** — Check the Traefik dashboard (usually at port 8080 on the server). Traefik misconfigurations are outside Dokploy's control.
- **Docker Swarm / cluster issues** — Check node status with `mcp__dokploy__cluster-getNodes`. Cluster problems require server-level debugging.
- **Persistent 502s after all checks pass** — Check server resources (CPU, memory, disk). The server may be under-provisioned.
- **Data corruption** — If database data is corrupted, restore from backups. Enumerate configured backups per resource and list backup files with `mcp__dokploy__backup-listBackupFiles` (`backup-all` was removed — backups are now resource-scoped).
- **Dokploy upgrade failures** — Check the Dokploy GitHub releases for known issues. Roll back to the previous version if needed.
