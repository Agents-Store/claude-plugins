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
| `--env <environment>` | Target: staging, prod, preview |
| `--api-url <url>` | Self-hosted server URL (default: `https://api.trigger.dev`) |
| `--env-file <path>` | Load .env file into CLI process (default: `.env`) |
| `--branch <name>` | Branch name (required for preview) |
| `--skip-promotion` | Deploy without making it active |
| `--skip-update-check` | Skip package version check |
| `--skip-sync-env-vars` | Skip syncEnvVars extension |
| `--config <path>` | Custom trigger.config.ts path |
| `--project-ref <ref>` | Override project ref |
| `--dry-run` | Show what would be deployed without deploying |
| `--local-build` | Build Docker image locally |

## Self-Hosted Deploy

For self-hosted instances, pass `--api-url` pointing to your Trigger.dev server and authenticate with `TRIGGER_ACCESS_TOKEN` (a PAT token):

```bash
# Set access token and deploy
TRIGGER_ACCESS_TOKEN=tr_pat_xxx \
npx trigger.dev@latest deploy \
  --env prod \
  --api-url https://your-trigger-instance.example.com \
  --env-file .env

# Or with project ref override
TRIGGER_ACCESS_TOKEN=tr_pat_xxx \
npx trigger.dev@latest deploy \
  --env prod \
  --api-url https://your-trigger-instance.example.com \
  --project-ref proj_xxx \
  --env-file .env
```

There is no `--self-hosted` flag — self-hosted and cloud deploys use the same CLI command, only `--api-url` differs (cloud default: `https://api.trigger.dev`).

The CLI automatically discovers the container registry from the server and handles Docker build + push internally.

## Environments

| Environment | Key Format | Convention Var | Purpose |
|-------------|-----------|----------------|---------|
| dev | `tr_dev_xxx` | `TRIGGER_DEV_SECRET_KEY` | Local development |
| staging | `tr_dev_xxx` (different key) | `TRIGGER_STAGE_SECRET_KEY` | Testing before prod |
| production | `tr_prod_xxx` | `TRIGGER_PROD_SECRET_KEY` | Live traffic |
| preview | `tr_dev_xxx` | — | Feature branch testing |

Each environment has its own unique secret key. Staging uses the `tr_dev_` prefix but it is NOT the same key as development. Pass the appropriate per-env key to the SDK via `configure()`.

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

## Post-Deploy Verification

After every deploy, verify tasks actually work — a successful deploy does NOT mean tasks run correctly. Environment variables, API endpoints, and data dependencies can all fail silently at runtime.

1. **Check recent runs** — use `list_runs` MCP tool (or dashboard) to see if tasks are failing
2. **Trigger each task** — use `trigger_task` MCP tool with test payloads to exercise all deployed tasks
3. **Wait and inspect** — use `wait_for_run_to_complete` and `get_run_details` to check for errors
4. **Common post-deploy failures:**
   - `undefined` in URLs → missing env vars (need `syncEnvVars` extension)
   - `401 Unauthorized` → expired or wrong API tokens in env vars
   - `Cannot read properties of null` → task code expects data that doesn't exist yet

Never declare a deploy done without triggering at least one test run per task.

## Deeper Reference

- @references/deploy-reference.md — preview branches, monorepo deploy
- @references/ci-cd-patterns.md — GitHub Actions, GitLab CI patterns
- @references/self-hosted-infrastructure.md — Docker Compose, supervisor, registry
