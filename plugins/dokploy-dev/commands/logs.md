---
description: Read logs for a Dokploy application, compose stack, database, or deployment
argument-hint: <resource-name-or-id> [--type <app|compose|db|deployment>] [--tail <N>]
---

# Read Dokploy Logs

Unified log reader. Resolves the resource type, picks the right MCP tool, and falls back to file-path / Beszel for runtime stdout (which Dokploy does not yet expose via REST — see [issue #3719](https://github.com/Dokploy/dokploy/issues/3719)).

## Arguments

Format: `<resource-name-or-id> [--type <app|compose|db|deployment>] [--tail <N>]`

- `resource-name-or-id` — required. Name or UUID of the app / compose / database / deployment.
- `--type` — optional. Force a specific resource type. If omitted, auto-detect by trying `application-one` → `compose-one` → `<db>-one` → `deployment-all` in that order.
- `--tail` — optional. Number of recent lines to return (default 200). Honored only for the file/Beszel fallback paths.

Parse from "$ARGUMENTS".

## Process

1. **Resolve the resource:**
   - If `--type` is set, jump straight to that branch.
   - Else, try `application-one` → on miss, `compose-one` → on miss, each `{type}-one` for `postgres/mysql/mariadb/mongo/redis/libsql` → on miss, `deployment-allCentralized` and search by id.

2. **Pick the right tool:**

   | Resource type | MCP tool | Returns |
   |---|---|---|
   | Application | `application-readLogs { applicationId }` | Build log metadata + `logPath` |
   | Compose | `compose-readLogs { composeId }` | Build log metadata + `logPath` |
   | Database (any of 6) | `{type}-readLogs { {type}Id }` | DB container log metadata |
   | Deployment | `deployment-all` filtered to find this run | Includes `logPath` for the build log |

3. **Stream the actual log content:**
   - `application-readLogs` / `compose-readLogs` return the build log **path** (and sometimes a snapshot), not a live tail. For real content:
     - **Preferred:** if Beszel is installed, call `beszel-getContainerLogs` against the Dokploy container — the log files at `/etc/dokploy/logs/<appName>/*.log` are visible inside it.
     - **Fallback:** print the `logPath` and tell the user to `sudo tail -n <N> <logPath>` on the server.
   - For *database* logs and *runtime* container stdout, `{type}-readLogs` works directly via MCP.

4. **Format the output** so the user can immediately spot the relevant section:
   - Show last `--tail` lines.
   - Highlight ERROR / FATAL / panic / exited / unauthorized lines.
   - If the deployment has `status: error`, surface the last 30 lines first.

5. **Suggest next step** when an error pattern is recognised — usually `/dokploy-dev:debug <id>` for a full diagnosis, or `/dokploy-dev:analyze <deploymentId>` to AI-summarise.

## Example Usage

```
/dokploy-dev:logs web-frontend
/dokploy-dev:logs my-stack --type compose
/dokploy-dev:logs pg-main --type db --tail 500
/dokploy-dev:logs deploy_abc123 --type deployment
```
