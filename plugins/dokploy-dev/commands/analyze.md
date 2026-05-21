---
description: AI-summarise a failed Dokploy deployment via the configured ai provider
argument-hint: [deployment-id|app-name-or-id]
---

# AI-Analyse Deployment

One-shot wrapper around `ai-analyzeLogs`. Locates a failed deployment, runs the configured AI provider against its build log, and reports root cause + suggested fix.

## Arguments

Format: `[deployment-id|app-name-or-id]` (optional)

- If a deployment ID is passed, analyse that specific deployment.
- If an application/compose name or ID is passed, find its most recent failed deployment.
- If **no argument**, call `deployment-allCentralized`, filter to the most recent `status: error` rows, and ask the user which to analyse.

Parse from "$ARGUMENTS".

## Process

1. **Verify AI is configured** — `mcp__dokploy__ai-getEnabledProviders`. If empty:
   - Tell the user no AI provider is configured.
   - Offer the manual debug path: "Run `/dokploy-dev:debug <id>` instead."
   - Optionally point them at the `ai-assist` skill to wire one up.
   - Stop here.

2. **Resolve the deployment ID:**
   - If a deployment ID is passed, use it directly.
   - If a resource name/ID is passed, call `deployment-all { applicationId }` (or `composeId`), filter to `status: error`, take the most recent.

3. **Run the analysis:**

   ```
   mcp__dokploy__ai-analyzeLogs
     → { deploymentId }
   ```

4. **Present the result** in this format:

   ```
   ## AI Analysis: <appName / composeName>

   **Deployment:** <deploymentId>
   **Started:** <timestamp>
   **Status:** error

   ### Root cause (per <providerName>/<model>)
   <ai-analyzeLogs.rootCause>

   ### Summary
   <ai-analyzeLogs.summary>

   ### Suggested fix
   <ai-analyzeLogs.suggestedFix>

   ### Verify before applying
   - Compare against the actual build log: `<logPath>`
   - Run `/dokploy-dev:logs <id>` to see the raw output
   - LLMs occasionally invent fixes for symptoms they don't fully understand
   ```

5. **Offer follow-up:**
   - "Apply this fix? I can update env / build type / Dockerfile and redeploy."
   - "Want a deeper analysis? Run `/dokploy-dev:debug <id>` for the full decision tree."

## Example Usage

```
/dokploy-dev:analyze
/dokploy-dev:analyze web-frontend
/dokploy-dev:analyze deploy_abc123def456
```
