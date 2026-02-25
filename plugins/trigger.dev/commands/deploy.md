---
description: Deploy project to an environment
allowed-tools: mcp__trigger_dev__tds-deploy, mcp__trigger_dev__tds-list_deploys
argument-hint: <environment> [--branch <branch>]
---

# Deploy

Deploy the Trigger.dev project to an environment.

## Arguments
Format: `<environment> [--branch <branch>]`
- environment: staging, prod, or preview
- --branch: Branch name (required for preview)

Parse from "$ARGUMENTS".

## Process

1. **Parse environment and options**

2. **Deploy:**
   ```
   tds-deploy(
     environment=<environment>,
     branch=<branch if preview>
   )
   ```
   This is a long-running operation. Wait for completion.

3. **Verify deployment:**
   ```
   tds-list_deploys(
     environment=<environment>,
     limit=1
   )
   ```

4. **Report result:**
   - Deployment status
   - Version number
   - Environment
   - Task count

## Example Usage
```
/deploy staging
/deploy prod
/deploy preview --branch feature/new-task
```

## Notes
- Always test in staging before deploying to prod
- Preview requires a branch name
- Deployment is a long-running operation
- Check /list-deploys for deployment history
