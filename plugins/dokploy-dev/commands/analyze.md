---
description: AI-summarise a failed Dokploy deployment or a crashing container via the configured ai provider
argument-hint: [deployment-id|app-name-or-id|compose-name-or-id]
allowed-tools: [Read, Bash, Skill, Agent]
---

# AI-Analyse a Failure

Pipeline around `ai-analyzeLogs`: fetch the relevant log text, then ask the configured AI provider for a root cause + suggested fix. `ai-analyzeLogs` takes the **log text** (not a `deploymentId`) plus an `aiId` and a `context`.

Follow the `read-logs` skill (`${CLAUDE_PLUGIN_ROOT}/skills/read-logs/SKILL.md`) §5 for the analyze step.

## Arguments

Format: `[deployment-id|app-name-or-id|compose-name-or-id]` (optional)

- Deployment id → analyse that build log (`context: "build"`).
- App / compose name or id → fetch its current runtime log (`context: "runtime"`); for a failed build, fetch the most recent errored deployment's build log instead.
- No argument → `deployment-allCentralized`, list recent `status: error` rows, ask which to analyse.

Parse from "$ARGUMENTS".

## Process

1. **Verify AI is configured** — `mcp__dokploy__ai-getEnabledProviders`.
   - If the array is **empty**: tell the user no AI provider is enabled, offer `/dokploy-dev:debug <id>` (manual decision tree), and point at the `ai-assist` skill to wire one up. Stop.
   - Else: take the `aiId` of an enabled provider.

2. **Fetch the log text** (this is the `logs` argument):
   - Build failure → `deployment-readLogs { deploymentId, tail: 1000 }` → `context: "build"`.
   - App runtime → `application-readLogs { applicationId, tail: 500, since: "2h" }` → `context: "runtime"`.
   - Compose runtime → enumerate containers and concatenate each container's `compose-readLogs { composeId, containerId, tail }` (or run `/dokploy-dev:compose-logs` first) → `context: "runtime"`.
   - Truncate very large logs before sending (provider context limits).

3. **Run the analysis:**

   ```
   mcp__dokploy__ai-analyzeLogs
     → { aiId: "<enabled provider id>", logs: "<text from step 2>", context: "build" | "runtime" }
   ```

4. **Present the result:**

   ```
   ## AI Analysis: <resource name>

   **Context:** build | runtime
   **Provider:** <providerName>/<model>

   ### Root cause
   <ai-analyzeLogs root cause>

   ### Suggested fix
   <ai-analyzeLogs suggested fix>

   ### Verify before applying
   - Cross-check against the raw log (`/dokploy-dev:logs <id>` or `/dokploy-dev:compose-logs <name>`).
   - The model only sees the log you sent it, not the codebase — trust the log if they conflict.
   ```

5. **Offer follow-up:**
   - "Apply this fix? I can update env / build type / Dockerfile and redeploy."
   - "Want the full decision tree? Run `/dokploy-dev:debug <id>`."

## Example Usage

```
/dokploy-dev:analyze
/dokploy-dev:analyze web-frontend
/dokploy-dev:analyze ipbay-website
/dokploy-dev:analyze <deploymentId>
```
