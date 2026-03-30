---
name: troubleshoot
description: Diagnose and fix Trigger.dev errors, failed runs, deployment issues, and self-hosted problems. Use when the user encounters "trigger.dev not working", "task keeps failing", "deploy failed", "runs stuck", "self-hosted issues", "trigger.dev connection error", or needs to debug Trigger.dev v4.
---

# Troubleshooting

Diagnostic steps and fixes for common Trigger.dev v4 problems.

## Quick Diagnostics

Run these checks first:

1. **CLI auth**: `npx trigger.dev@latest whoami`
2. **Dev server**: `npx trigger.dev@latest dev` — starts without errors?
3. **If MCP**: `list_orgs()` — returns organizations?
4. **Recent failures**: `list_runs(status="FAILED", period="1d")`

## Task Errors

| Status | Cause | Fix |
|--------|-------|-----|
| FAILED | Task threw an error | Check run details → read error trace |
| CRASHED | OOM or unexpected crash | Increase machine preset or fix memory leak |
| SYSTEM_FAILURE | Infrastructure issue | Check supervisor container health |
| TIMED_OUT | Exceeded maxDuration | Increase `maxDuration` or optimize task |
| EXPIRED | TTL expired before execution | Increase TTL or fix queue bottleneck |
| PENDING_VERSION | No matching worker deployed | Deploy to the correct environment |

## Connection Errors

| Error | Cause | Fix |
|-------|-------|-----|
| ECONNREFUSED | Instance not running | Start: `docker compose up -d` |
| ETIMEDOUT | Network/firewall | Check DNS, firewall, proxy config |
| ENOTFOUND | Wrong URL | Verify TRIGGER_API_URL |
| SSL_ERROR | Invalid certificate | Check reverse proxy SSL config |
| Redirected to cloud | Missing API URL | Use `login -a <url>` or set TRIGGER_API_URL |

## Authentication Errors

| Error | Cause | Fix |
|-------|-------|-----|
| 401 Unauthorized | Invalid secret key | Check format: tr_dev_xxx (dev), tr_prod_xxx (prod) |
| 403 Forbidden | Wrong environment key | Use dev key for dev, prod key for prod |
| Token expired | Key rotated | Generate new key in dashboard |
| CI auth fails | Missing access token | Set TRIGGER_ACCESS_TOKEN (tr_pat_xxx) |

## Deployment Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Build failed | TypeScript errors | Fix compile errors in your task code |
| Push failed | No registry access | `docker login -u <user> <registry-url>` |
| "No tasks found" | Wrong `dirs` config | Check `dirs` in trigger.config.ts |
| Version mismatch | SDK/CLI out of sync | `npm install @trigger.dev/sdk@latest` |

## Dev Server Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Cannot find trigger.config.ts | Wrong directory | Run from project root or pass `--config` |
| Tasks not registering | File not in `dirs` | Check trigger.config.ts `dirs` |
| Hot reload not working | File watcher issue | Restart dev server |

## Self-Hosted v4 Diagnostics

### Check Instance Health

```bash
# Webapp
cd trigger.dev/hosting/docker/webapp
docker compose ps
docker compose logs -f webapp

# Supervisor
cd trigger.dev/hosting/docker/worker
docker compose ps
docker compose logs -f supervisor
```

### Common Self-Hosted Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| All runs CRASHED | Supervisor OOM | Increase Docker memory limits |
| Runs stuck QUEUED | Supervisor disconnected | Check worker token; restart supervisor |
| Dashboard 502 | Webapp crashed | `docker compose restart webapp` |
| Worker token missing | Separate machines | Check webapp logs for token on first start |
| Registry auth fails | Wrong credentials | Check auth.htpasswd in registry config |
| Object storage error | MinIO bucket missing | Create `packets` bucket via MinIO UI (:9001) |
| Disk full | Old runs not cleaned | Configure retention, clean old data |

### Log Analysis

```bash
# Find errors in webapp
docker compose logs webapp 2>&1 | grep -i error | tail -20

# Check for OOM kills
docker compose logs supervisor 2>&1 | grep -i "oom\|killed" | tail -10

# Check registry
curl -s http://localhost:5000/v2/

# Check MinIO
curl -s http://localhost:9000/minio/health/live
```

## Deeper Reference

- @references/common-errors.md — extended error catalog
