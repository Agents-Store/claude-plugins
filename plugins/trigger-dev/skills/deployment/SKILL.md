---
name: deployment
description: Deploying projects to staging/production/preview, managing deployments, and preview branches. Use when deploying or checking deployment status.
---

# Deployment

This skill covers deploying Trigger.dev projects and managing environments.

## Available Tools

| Tool | Description |
|------|-------------|
| `tds-deploy` | Deploy project to an environment |
| `tds-list_deploys` | List deployments with filters |
| `tds-list_preview_branches` | List preview branches |
| `tds-search_docs` | Search docs for deployment details |

## Deploying

### Deploy to Staging

```
Tool: tds-deploy
Input: {"environment": "staging"}
→ {status: "DEPLOYED", version: "20250225.2"}
```

### Deploy to Production

```
Tool: tds-deploy
Input: {"environment": "prod"}
```

### Deploy Preview Branch

```
Tool: tds-deploy
Input: {
  "environment": "preview",
  "branch": "feature/new-task"
}
```

### Deploy without Promoting

```
Tool: tds-deploy
Input: {
  "environment": "prod",
  "skipPromotion": true
}
→ Deploys but does NOT make it the active deployment (canary/blue-green)
```

### Deploy Options

| Option | Type | Description |
|--------|------|-------------|
| `environment` | enum | staging, prod, preview |
| `branch` | string | Branch name (required for preview) |
| `skipPromotion` | boolean | Deploy without promoting to current |
| `skipSyncEnvVars` | boolean | Skip env var sync |
| `skipUpdateCheck` | boolean | Skip package update check |
| `configPath` | string | Custom trigger.config.ts path |
| `projectRef` | string | Project ref (auto-detected) |

## Listing Deployments

### Recent Deployments

```
Tool: tds-list_deploys
Input: {"environment": "prod", "limit": 10}
```

### Failed Deployments

```
Tool: tds-list_deploys
Input: {"environment": "prod", "status": "FAILED", "period": "7d"}
```

### Deployment Status Values

| Status | Description |
|--------|-------------|
| PENDING | Deployment queued |
| BUILDING | Building the project |
| DEPLOYING | Pushing to environment |
| DEPLOYED | Successfully deployed |
| FAILED | Build or deploy failed |
| CANCELED | Deployment was cancelled |
| TIMED_OUT | Build/deploy timed out |

### Deployment Filters

| Parameter | Type | Description |
|-----------|------|-------------|
| `environment` | enum | staging, prod, preview |
| `status` | enum | Deployment status |
| `period` | string | "1d", "7d", "30d" |
| `from` / `to` | ISO datetime | Custom range |
| `limit` | number | Max 100 |
| `cursor` | string | Pagination |

## Preview Branches

### List All Previews

```
Tool: tds-list_preview_branches
Input: {}
→ [{branch: "feature/new-task", ...}]
```

### Deploy and Test Preview

```
1. tds-deploy(environment="preview", branch="feature/new-task")
2. tds-trigger_task(taskId="my-task", payload={...}, environment="preview", branch="feature/new-task")
3. tds-list_runs(environment="preview", branch="feature/new-task")
```

## Deployment Workflows

### Standard Flow

```
1. Develop locally with dev environment
2. tds-deploy(environment="staging")
3. tds-trigger_task(environment="staging", ...) → test
4. tds-list_runs(environment="staging", period="1h") → verify
5. tds-deploy(environment="prod")
6. tds-list_deploys(environment="prod", limit=1) → confirm
```

### Preview Branch Flow

```
1. Create feature branch
2. tds-deploy(environment="preview", branch="my-feature")
3. Test in preview
4. Merge to main
5. Deploy to staging → prod
```

### Monorepo

Always pass `configPath`:

```
Tool: tds-deploy
Input: {
  "environment": "prod",
  "configPath": "./packages/jobs/trigger.config.ts"
}
```

## Self-Hosted Deployment Notes

### CLI Deploy

For self-hosted instances, use `--self-hosted` flag:

```bash
npx trigger.dev@latest deploy --env production --self-hosted
```

Or ensure `TRIGGER_API_URL` is set in environment.

### CI/CD Pipeline

```yaml
# GitHub Actions
- name: Deploy to production
  run: npx trigger.dev@latest deploy --env production --self-hosted
  env:
    TRIGGER_API_URL: ${{ secrets.TRIGGER_API_URL }}
    TRIGGER_SECRET_KEY: ${{ secrets.TRIGGER_SECRET_KEY }}
```

### Upgrading Self-Hosted Instance

When upgrading your Trigger.dev instance:

1. Pull new images: `docker compose pull`
2. Stop services: `docker compose down`
3. Run migrations: `docker compose run --rm webapp prisma migrate deploy`
4. Start services: `docker compose up -d`
5. Redeploy tasks: `npx trigger.dev@latest deploy --env production --self-hosted`

### Build in Self-Hosted

The build happens inside Docker. Ensure your self-hosted instance has enough resources:
- At least 2GB RAM for the build process
- Docker BuildKit enabled for faster builds
- Registry access if using private npm packages

## Best Practices

1. **Always deploy to staging first** before production
2. **Use preview branches** for testing new tasks in isolation
3. **Monitor deployment status** — check for FAILED deploys
4. **Use skipPromotion** for gradual rollouts
5. **Check task schemas** after deploy with `tds-get_current_worker`
