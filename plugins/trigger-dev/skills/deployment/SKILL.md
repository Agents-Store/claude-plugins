---
name: deployment
description: Deploy Trigger.dev tasks to staging, production, or preview environments. Use when the user asks to "deploy trigger.dev tasks", "set up CI/CD for trigger.dev", "deploy to production", "deploy self-hosted trigger", "manage environments", or needs deployment workflows and self-hosted infrastructure guidance.
---

# Deployment

Deploy Trigger.dev tasks to staging, production, or preview environments.

## Deploy Cycle

1. Develop locally with `npx trigger.dev@latest dev`
2. Deploy to staging: `npx trigger.dev@latest deploy --env staging`
3. Test in staging
4. Deploy to production: `npx trigger.dev@latest deploy --env production`
5. Verify: check dashboard or `list_deploys` MCP tool

## CLI Deploy

```bash
# Deploy to production (default)
npx trigger.dev@latest deploy

# Deploy to staging
npx trigger.dev@latest deploy --env staging

# Deploy to preview branch
npx trigger.dev@latest deploy --env preview --branch feature/new-task

# Deploy without promoting (canary)
npx trigger.dev@latest deploy --skip-promotion
```

## Deploy Flags

| Flag | Description |
|------|-------------|
| `--env <environment>` | Target: staging, production, preview |
| `--branch <name>` | Branch name (required for preview) |
| `--skip-promotion` | Deploy without making it active |
| `--skip-update-check` | Skip package version check |
| `--config <path>` | Custom trigger.config.ts path |
| `--project-ref <ref>` | Override project ref |

## Self-Hosted Deploy

For self-hosted instances, ensure you're logged in to the correct profile:

```bash
# Already logged in via: login -a <url>
npx trigger.dev@latest deploy --env production
```

The CLI builds locally and pushes to the self-hosted container registry.

### Registry Login

```bash
docker login -u <username> <registry-url>
# Default: localhost:5000, user: registry-user
```

## Environments

| Environment | Key Format | Convention Var | Purpose |
|-------------|-----------|----------------|---------|
| dev | `tr_dev_xxx` | `TRIGGER_DEV_SECRET_KEY` | Local development |
| staging | `tr_dev_xxx` (different key) | `TRIGGER_STAGE_SECRET_KEY` | Testing before prod |
| production | `tr_prod_xxx` | `TRIGGER_PROD_SECRET_KEY` | Live traffic |
| preview | `tr_dev_xxx` | — | Feature branch testing |

Each environment has its own unique secret key. Staging uses the `tr_dev_` prefix but it is NOT the same key as development. Store each key in a separate env var and map the active one to `TRIGGER_SECRET_KEY`.

## CI/CD (GitHub Actions)

```yaml
name: Deploy Trigger.dev
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm ci
      - name: Deploy to production
        run: npx trigger.dev@latest deploy --env production
        env:
          TRIGGER_ACCESS_TOKEN: ${{ secrets.TRIGGER_ACCESS_TOKEN }}
          # For self-hosted:
          TRIGGER_API_URL: ${{ secrets.TRIGGER_API_URL }}
```

## Deployment Status Values

| Status | Description |
|--------|-------------|
| PENDING | Queued |
| BUILDING | Building project |
| DEPLOYING | Pushing to environment |
| DEPLOYED | Successfully deployed |
| FAILED | Build or deploy failed |
| CANCELED | Deployment cancelled |
| TIMED_OUT | Build/deploy timed out |

## Package.json Scripts

```json
{
  "scripts": {
    "trigger:dev": "trigger.dev dev",
    "trigger:deploy:staging": "trigger.dev deploy --env staging",
    "trigger:deploy:prod": "trigger.dev deploy --env production"
  }
}
```

## Deeper Reference

- @references/deploy-reference.md — preview branches, monorepo deploy
- @references/ci-cd-patterns.md — GitHub Actions, GitLab CI patterns
- @references/self-hosted-infrastructure.md — Docker Compose, supervisor, registry
