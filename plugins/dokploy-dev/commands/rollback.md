---
description: Roll a Dokploy application or compose stack back to a previous version
argument-hint: <app-name-or-id|compose-id>
---

# Rollback Deployment

Guided rollback to a previously-successful deployment. Lists available rollback points, asks the user to pick one, then calls `rollback-rollback`.

## Arguments

Format: `<app-name-or-id|compose-id>` (required)

Parse from "$ARGUMENTS".

## Process

1. **Resolve the resource:**
   - Try `application-one { applicationId }` first.
   - Fall back to `compose-one { composeId }`.
   - If a name was passed, use `project-all` to find the matching project and resource.

2. **List available rollback points:**
   - From the resource record, look for the `rollbacks` array (each entry has `rollbackId`, `version`, `deploymentId`, `createdAt`, `description`).
   - If there are no rollbacks, tell the user — Dokploy only creates rollback points on successful deploys. Stop here.

3. **Present options** as a numbered list:

   ```
   Available rollback points for <appName>:

   1. v3 — 2026-05-20 14:22 UTC (current: v4)
      Deployment: deploy_xyz789
   2. v2 — 2026-05-19 11:08 UTC
   3. v1 — 2026-05-18 09:30 UTC
   ```

4. **Confirm with the user:**
   - "Which version do you want to roll back to? This will stop the current container and start the rolled-back image."
   - Use AskUserQuestion for the choice if running in an interactive context.

5. **Execute:**

   ```
   mcp__dokploy__rollback-rollback
     → { rollbackId: "<chosen rollbackId>" }
   ```

6. **Verify:**
   - Poll `application-one` (or `compose-one`) until `applicationStatus: running`.
   - `docker-getContainersByAppLabel { appName }` to confirm the image tag matches the rolled-back version.
   - `domain-validateDomain` if domains are attached.
   - Curl the endpoint to confirm responsive.

7. **Tidy up (optional):**
   - Offer to delete the failed deployments that triggered the rollback via `deployment-removeDeployment` or `application-dropDeployment`. Confirm before doing so — audit trail matters.

## Notes

- Rollbacks are **image-level**, not source-level. The rolled-back container uses the previously-built image; no rebuild happens.
- Environment variables are **not** rolled back automatically. If the env changed alongside the bad deploy, ask the user whether to also restore prior env values (Dokploy keeps env history in deployment records).
- Rollback does not affect attached databases or persistent volumes.

## Example Usage

```
/dokploy-dev:rollback web-frontend
/dokploy-dev:rollback abc123-def456
```
