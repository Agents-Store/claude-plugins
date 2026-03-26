---
name: troubleshoot
description: This skill should be used when the user encounters "trigger.dev errors", "trigger.dev not working", "trigger.dev connection issues", "debug trigger.dev", "task keeps failing", "runs stuck", "deploy failed", "self-hosted issues", or needs to diagnose and fix common problems with Trigger.dev v4.
---

# Trigger.dev Troubleshooting

Diagnostic steps and fixes for common Trigger.dev v4 problems.

## Quick Diagnostics

Run these checks first:

1. **MCP connection**: `tds-list_orgs()` — should return organizations
2. **Worker status**: `tds-get_current_worker(environment="dev")` — should return tasks
3. **Recent failures**: `tds-list_runs(status="FAILED", period="1d")`
4. **Deploy status**: `tds-list_deploys(environment="prod", limit=1)`

## Connection Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ECONNREFUSED` | Instance not running | Start: `docker compose up -d` in webapp/ and worker/ |
| `ETIMEDOUT` | Network/firewall | Check DNS, firewall rules, proxy config |
| `ENOTFOUND` | Wrong URL | Verify `TRIGGER_API_URL` |
| `SSL_ERROR` | Invalid certificate | Check reverse proxy SSL; set `NODE_EXTRA_CA_CERTS` if needed |
| MCP timeout | Instance unreachable | Ping instance URL, check Docker health |
| Redirected to cloud | Missing API URL | Use `login -a <url>` or set `TRIGGER_API_URL` env var |

## Authentication Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid secret key | Check format: `tr_dev_xxx` (dev), `tr_prod_xxx` (prod) |
| `403 Forbidden` | Wrong environment key | Use dev key for dev, prod key for prod |
| Token expired | Key rotated | Generate new key in dashboard → Settings → API Keys |
| CI auth fails | Missing `TRIGGER_ACCESS_TOKEN` | Set PAT: `tr_pat_xxx` in CI env vars |

## Task Errors

| Status | Cause | Fix |
|--------|-------|-----|
| FAILED | Task threw an error | `tds-get_run_details(runId)` → read error trace |
| CRASHED | OOM or unexpected crash | Increase machine preset or fix memory leak |
| SYSTEM_FAILURE | Infrastructure issue | Check supervisor container health |
| TIMED_OUT | Exceeded maxDuration | Increase `maxDuration` or optimize task |
| EXPIRED | TTL expired before execution | Increase TTL or fix queue bottleneck |
| PENDING_VERSION | No matching worker deployed | Deploy to the correct environment |

## Deployment Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Build failed | TypeScript/compile errors | Fix errors; check `tds-list_deploys(status="FAILED")` |
| Push failed | No registry access | Login: `docker login -u <user> <registry-url>` |
| Deploy timeout | Large project or slow build | Increase Docker resources |
| "No tasks found" | Wrong `dirs` config | Check `dirs` in trigger.config.ts |
| Version mismatch | SDK/CLI versions out of sync | `npm install @trigger.dev/sdk@latest` |
| `graphile_worker` schema error | Migration failed on startup | Check webapp logs for SSL cert errors; set `NODE_EXTRA_CA_CERTS` |

## Dev Server Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `Cannot find trigger.config.ts` | Wrong directory | Run from project root or `--config` |
| Tasks not registering | File not in `dirs` | Check `dirs` in trigger.config.ts |
| Hot reload not working | File watcher issue | Restart dev server |
| Port conflict | Another process using port | Kill conflicting process or change port |

## Self-Hosted v4 Diagnostics

### Architecture Overview

v4 self-hosted uses two separate Docker Compose stacks:

- **webapp/** — Dashboard, API, PostgreSQL, Redis, registry, MinIO (object storage)
- **worker/** — Supervisor that manages task execution containers

The v3 coordinator+provider are replaced by a single **supervisor**. Docker Socket Proxy is used instead of direct socket access (security improvement).

### Check Instance Health

```bash
# Webapp services
cd trigger.dev/hosting/docker/webapp
docker compose ps
docker compose logs -f webapp

# Worker/Supervisor services
cd trigger.dev/hosting/docker/worker
docker compose ps
docker compose logs -f supervisor
```

### Common Self-Hosted v4 Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| All runs CRASHED | Supervisor OOM | Increase Docker memory limits |
| Runs stuck QUEUED | Supervisor disconnected | Check worker token; `docker compose restart supervisor` |
| Dashboard 502 | Webapp crashed | `docker compose restart webapp` in webapp/ |
| Worker token missing | Separate machines, token not set | Check webapp logs for token on first start; set `TRIGGER_WORKER_TOKEN` |
| Registry auth fails | Wrong credentials | Check `auth.htpasswd` in hosting/docker/registry/ |
| Object storage error | MinIO bucket missing | Create `packets` bucket via MinIO UI at :9001 |
| Slow performance | DB not optimized | Run VACUUM, check connection count |
| Disk full | Old runs not cleaned | Configure retention, clean old data |
| ClickHouse schema missing | Goose migration tracker out of sync | Exec into webapp, run `goose reset && goose up` (WARNING: destructive) |

### Worker Token Setup (v4)

When running webapp and worker on separate machines:

1. First start of webapp prints the worker token:
   ```
   TRIGGER_WORKER_TOKEN=tr_wgt_xxxxxxxxxxxxx
   ```
2. Set this in worker's `.env` file
3. Restart worker: `docker compose down && docker compose up -d`

### Creating Additional Worker Groups

```bash
api_url=http://localhost:8030
wg_name=my-worker
admin_pat=tr_pat_...

curl -X POST \
  "$api_url/admin/api/v1/workers" \
  -H "Authorization: Bearer $admin_pat" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"$wg_name\"}"
```

Requires admin privileges (set `ADMIN_EMAILS` env var or `admin=true` in user table).

### Self-Hosted Log Analysis

```bash
# Find errors in webapp
docker compose logs webapp 2>&1 | grep -i error | tail -20

# Find OOM kills in supervisor
docker compose logs supervisor 2>&1 | grep -i "out of memory\|oom\|killed" | tail -10

# Check registry health
curl -s http://localhost:5000/v2/ | jq .

# Check MinIO health
curl -s http://localhost:9000/minio/health/live
```

### Version Locking

Lock Docker image versions in `.env`:

```bash
TRIGGER_IMAGE_TAG=v4.0.0
```

### Telemetry Opt-Out

```yaml
services:
  webapp:
    environment:
      TRIGGER_TELEMETRY_DISABLED: 1
```

## MCP-Specific Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `tds-*` tools not found | MCP server not configured | Run `npx trigger.dev@latest mcp` to install |
| MCP returns empty | Wrong project or environment | Pass correct `projectRef` and `environment` |
| MCP slow | Network latency | Check network route to self-hosted URL |
| MCP accesses prod | No dev-only restriction | Add `--dev-only` flag to MCP args |

## Useful Documentation Searches

```
tds-search_docs(query="troubleshooting common errors")
tds-search_docs(query="self-hosting v4 docker setup")
tds-search_docs(query="worker token supervisor configuration")
tds-search_docs(query="registry setup container deployment")
```
