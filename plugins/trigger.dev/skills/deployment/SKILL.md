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

### Deploy to Production
```
Tool: tds-deploy
Input: {
  "environment": "prod"
}

This is a long-running operation.
Returns deployment status when complete.
```

### Deploy to Staging
```
Tool: tds-deploy
Input: {
  "environment": "staging"
}
```

### Deploy Preview Branch
```
Tool: tds-deploy
Input: {
  "environment": "preview",
  "branch": "feature/new-task"
}
```

### Deploy Options

| Option | Type | Description |
|--------|------|-------------|
| `environment` | enum | "staging", "prod", "preview" |
| `branch` | string | Branch name (required for preview) |
| `skipPromotion` | boolean | Deploy without promoting to current |
| `skipSyncEnvVars` | boolean | Skip env var sync (syncEnvVars extension) |
| `skipUpdateCheck` | boolean | Skip @trigger.dev package update check |
| `configPath` | string | Custom path to trigger.config.ts |
| `projectRef` | string | Project ref (auto-detected from config) |

### Deploy without Promoting
```
Tool: tds-deploy
Input: {
  "environment": "prod",
  "skipPromotion": true
}

Deploys but does not make it the active deployment.
Useful for canary / blue-green deployments.
```

## Listing Deployments

### Recent Deployments
```
Tool: tds-list_deploys
Input: {
  "environment": "prod",
  "limit": 10
}
```

### Failed Deployments
```
Tool: tds-list_deploys
Input: {
  "environment": "prod",
  "status": "FAILED",
  "period": "7d"
}
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
| `status` | enum | Filter by deployment status |
| `period` | string | Time range ("1d", "7d", "30d") |
| `from` / `to` | ISO datetime | Custom time range |
| `limit` | number | Results per page (max 100) |
| `cursor` | string | Pagination cursor |

## Preview Branches

### List All Preview Branches
```
Tool: tds-list_preview_branches
Input: {}

Returns list of branches with preview deployments.
```

### Deploy and Test a Preview
```
1. Deploy preview:
   tds-deploy(environment="preview", branch="feature/new-task")

2. Trigger task in preview:
   tds-trigger_task(
     taskId="my-task",
     payload={...},
     environment="preview",
     branch="feature/new-task"
   )

3. Check results:
   tds-list_runs(environment="preview", branch="feature/new-task")
```

## Deployment Workflow

### Standard Flow
```
1. Develop locally with dev environment
2. Deploy to staging:
   tds-deploy(environment="staging")
3. Test in staging:
   tds-trigger_task(environment="staging", ...)
4. Verify runs:
   tds-list_runs(environment="staging", period="1h")
5. Deploy to production:
   tds-deploy(environment="prod")
6. Verify production:
   tds-list_deploys(environment="prod", limit=1)
```

### Preview Branch Flow
```
1. Create feature branch
2. Deploy preview:
   tds-deploy(environment="preview", branch="my-feature")
3. Test in preview
4. Merge to main
5. Deploy to staging -> prod
```

## Monorepo Setup

For monorepos, always pass `configPath`:
```
Tool: tds-deploy
Input: {
  "environment": "prod",
  "configPath": "./packages/jobs/trigger.config.ts"
}
```

## Best Practices

1. **Always deploy to staging first** before production
2. **Use preview branches** for testing new tasks in isolation
3. **Monitor deployment status** - check for FAILED deploys
4. **Use skipPromotion** for gradual rollouts
5. **Check task schemas** after deploy with tds-get_current_worker
