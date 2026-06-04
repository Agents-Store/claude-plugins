---
description: Read the logs of EVERY container in a Dokploy Docker Compose stack and highlight errors
argument-hint: <compose-name-or-id> [--tail <N>] [--since <1h>] [--search <term>] [--errors-only]
allowed-tools: [Read, Bash, Skill, Agent]
---

# Read All Compose Container Logs

Reads the runtime logs of **every container** in a Docker Compose stack, aggregates them, and surfaces errors per container. This is the right tool when a multi-service stack is misbehaving and you don't yet know which service is at fault.

Follow the `read-logs` skill (`${CLAUDE_PLUGIN_ROOT}/skills/read-logs/SKILL.md`), §2 — load it first.

## Arguments

Format: `<compose-name-or-id> [--tail <N>] [--since <1h>] [--search <term>] [--errors-only]`

- `compose-name-or-id` — required. Name or `composeId` of the compose stack.
- `--tail` — lines per container (default `200`, max `10000`).
- `--since` — time window: `all` or `<n>{s|m|h|d}` (e.g. `30m`, `2h`). Default `all`.
- `--search` — server-side substring filter applied to every container's log.
- `--errors-only` — show only lines matching the error patterns (see skill §6); hide clean output.

Parse from "$ARGUMENTS".

## Process

1. **Resolve the stack.**
   - If given a name, `mcp__dokploy__compose-search { q: "<name>" }` → pick the match → `composeId`.
   - `mcp__dokploy__compose-one { composeId }` → read `appName` and `composeType`.

2. **Enumerate every container** (skill §2 step 2):
   - `composeType: "docker-compose"` → `mcp__dokploy__docker-getContainersByAppNameMatch { appName, appType: "docker-compose" }`
   - `composeType: "stack"` → `mcp__dokploy__docker-getStackContainersByAppName { appName }`
   - Fallback → `mcp__dokploy__docker-getContainers {}` and filter to names containing `appName`.
   - Collect each container's identifier (`containerId` / `name`) and current `state` / `status`.

3. **Loop — read logs for EACH container** (never stop at the first):
   ```
   mcp__dokploy__compose-readLogs
     → { composeId, containerId: <each>, tail: <--tail>, since: <--since>, search: <--search?> }
   ```

4. **Aggregate the output:**
   ```
   ## Compose logs: <appName>   (<composeType>, <N> containers)

   ### <containerId / service> — <state> (<status>)
   <last --tail lines; error lines surfaced first>
   ...repeat for every container...

   ### Summary
   - Containers down/unhealthy: <list>
   - Errors found: <count> across <containers>
   - Likely root cause: <the lowest-level failing service — e.g. a crashed db that others depend on>
   ```
   With `--errors-only`, print just the matching lines per container and skip clean ones.

5. **Diagnose across containers.** A failure in one service often shows up as a symptom in another (a dead `db` → `ECONNREFUSED` in `web`). Identify the *lowest-level* failing container as the root cause, not the loudest one.

6. **Offer next steps:**
   - `/dokploy-dev:analyze <composeId>` — AI root-cause on the collected logs (`ai-analyzeLogs { aiId, logs, context: "runtime" }`).
   - `/dokploy-dev:debug <composeId>` — full failure decision tree (build log, Traefik, recovery).

## Example Usage

```
/dokploy-dev:compose-logs n8n-stack
/dokploy-dev:compose-logs supabase --since 1h --search error
/dokploy-dev:compose-logs my-stack --tail 500 --errors-only
/dokploy-dev:compose-logs cmp_abc123
```
