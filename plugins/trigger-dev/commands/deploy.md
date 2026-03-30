---
description: Deploy Trigger.dev tasks to an environment
argument-hint: [staging|production] [--profile <name>]
allowed-tools: [Bash]
---

# Deploy Tasks

1. Determine target environment from arguments (default: production)
2. Verify `trigger.config.ts` exists
3. Build the deploy command:
   - Base: `npx trigger.dev@latest deploy --env <environment>`
   - If `--profile` argument: add `--profile <name>`
   - If monorepo: add `--config <path>`
4. Run the deploy command
5. Report the deployment status and version
6. Suggest: "Check deployment with `list_deploys(environment='<env>', limit=1)` or in the dashboard"
