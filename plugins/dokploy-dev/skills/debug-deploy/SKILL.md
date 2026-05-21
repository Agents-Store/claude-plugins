---
name: debug-deploy
description: "This skill should be used when a Dokploy deployment fails, gets stuck, or behaves incorrectly after deploying — provides an end-to-end decision tree that locates the failed run, reads the right logs, inspects the container and Traefik state, summarises root cause with AI, and recovers safely. Triggers: \"my dokploy deploy failed\", \"deployment stuck\", \"build error in dokploy\", \"app crashed after deploy\", \"diagnose failed deployment\", \"dokploy deploy not working\", \"why did my deploy fail\", \"recover from broken deploy\"."
---

# Debug a Failed Dokploy Deployment

This is the **canonical workflow** when a Dokploy deployment fails, gets stuck, or the production site does not change after a "successful" deploy. Work through the steps in order — each step narrows the cause and feeds the next.

Companion command: **`/dokploy-dev:debug [applicationId|composeId]`** runs this entire chain.

> **Runtime-log REST gap (important):** Dokploy does **not** expose live container `stdout` / `stderr` over its public REST API yet (see [issue #3719](https://github.com/Dokploy/dokploy/issues/3719)). `application-readLogs` / `compose-readLogs` return the deployment **build** log path and metadata, not a streaming tail. For *runtime* stdout/stderr you must either (a) `ssh` to the server and `docker logs <container>`, (b) read the build-log file Dokploy writes at `/etc/dokploy/logs/<appName>/<appName>-<timestamp>.log`, or (c) read it via Beszel if Beszel is monitoring the container. Set this expectation with the user up front so they don't think the tool is broken.

---

## Step 0 — Confirm the platform itself is healthy

Before blaming the deploy, rule out the server.

1. `mcp__dokploy__settings-health` — must return ok.
2. `mcp__dokploy__settings-checkInfrastructureHealth` — checks Docker daemon, Traefik, network, disk.
3. `mcp__dokploy__settings-getDockerDiskUsage` — if the disk is >90% full, builds silently fail with "no space left on device". Run `/dokploy-dev:cleanup` to recover.
4. `mcp__dokploy__settings-getDokployVersion` — note the version; some bugs are version-specific.

If any of these fail, fix the server first. Do not proceed.

---

## Step 1 — Locate the failed deployment

Find the most recent deployment for the resource and confirm its status.

**For a single resource (you know the ID):**

```
mcp__dokploy__deployment-all
  → { applicationId: "<id>" }     # for applications
  → { composeId: "<id>" }         # for compose stacks
  → { serverId: "<id>" }          # for server-level deploys
```

**For "I don't know which app failed":**

```
mcp__dokploy__deployment-allCentralized   # all deployments across the instance
mcp__dokploy__deployment-queueList        # what's currently queued / in-flight
```

In both responses, look at `status`. Values you care about:

| Status | Meaning | Next step |
|---|---|---|
| `running` | Build / deploy in progress | Step 2 (read live logs) |
| `error` | Deploy failed | Step 2, then Step 3 |
| `done` but site unchanged | Compose-mode mismatch — you deployed the standalone app while production runs from compose, or vice-versa | Re-check via `project-one`; deploy the *compose* resource using `compose-deploy` |
| `queued` for >2 minutes | Queue stuck | Step 5 (recovery: `cleanQueues`) |

Save the `deploymentId` of the failed run — multiple steps below take it.

---

## Step 2 — Read the build log

The build log is the single most informative artifact for diagnosing failures.

1. **Get the build-log file path** for this deployment from the `deployment-all` response — Dokploy stores the path under `logPath` (typically `/etc/dokploy/logs/<appName>/<appName>-<timestamp>.log` on the host).

2. **Read it via whichever channel is available:**

   - **MCP path:** `mcp__dokploy__application-readLogs { applicationId }` (apps) or `mcp__dokploy__compose-readLogs { composeId }` (compose). Returns the build/deploy log metadata.
   - **Beszel fallback** (most reliable for runtime stdout): if the user has Beszel installed, use `beszel-getContainerLogs` against the Dokploy container — the `/etc/dokploy/logs/...` files are visible inside the container. The container ID for the dokploy-server system can be found via `beszel-get_collections_containers_records`.
   - **SSH fallback** (last resort, requires user action): tell the user to run `sudo tail -n 500 /etc/dokploy/logs/<appName>/<latest>.log` on the server.

3. **Scan the log for these patterns first** — they account for the majority of Dokploy build failures:

| Pattern in log | Root cause | Fix |
|---|---|---|
| `no space left on device` | Disk full | Step 5 → `/dokploy-dev:cleanup` |
| `failed to compute cache key` / `failed to fetch` | Stale build cache or bad layer | `application-killBuild`, then `application-redeploy` |
| `error: failed to solve` | Dockerfile error / missing context | Inspect Dockerfile / context path; fix and `application-saveBuildType` |
| `Authentication failed` (git) | Wrong / expired token | `github-update` / `gitlab-update` / `bitbucket-update` / `gitea-update` |
| `nixpacks` cannot detect language | Wrong build type | Switch to `dockerfile` via `application-saveBuildType` |
| `MODULE_NOT_FOUND` / `ImportError` | Missing dep or wrong working dir | Check `dockerContextPath` and Dockerfile `WORKDIR` |
| Build times out | Heavy image or slow network | Increase timeout, use multi-stage builds, or pre-build & push image |
| App exits 0/1 immediately after start | Missing runtime env var | Step 4 (check env), then `saveEnvironment` + `redeploy` |

---

## Step 3 — Inspect the container state

If the *build* succeeded but the *runtime* is broken, switch from build logs to container introspection.

```
mcp__dokploy__docker-getContainersByAppLabel
  → { appName: "<appName>" }
```

Returns the list of running containers tagged with this app's Docker label. You want to see:

- **State** — `running`, `exited`, `restarting` (crash loop)
- **Health** — `healthy`, `unhealthy`, `starting`, `none`
- **Image** — confirm Dokploy is running the image it just built (not an old one)
- **Ports** — what's actually published

Drill down with these as needed:

| Tool | When to use |
|---|---|
| `mcp__dokploy__docker-getConfig` | Inspect full container config: env, command, mounts, network, restart policy. Catches misconfigured `command:` overrides and missing mounts |
| `mcp__dokploy__docker-getServiceContainersByAppName` | For Swarm-deployed apps — finds containers across nodes |
| `mcp__dokploy__docker-getStackContainersByAppName` | For compose-deployed apps — lists every service container in the stack |
| `mcp__dokploy__docker-getContainersByAppNameMatch` | Loose match by app-name substring — useful when `appName` is not exact |
| `mcp__dokploy__docker-killContainer` | Force-stop a wedged container |
| `mcp__dokploy__docker-restartContainer` | Restart in place (no rebuild) — first try after a transient runtime failure |
| `mcp__dokploy__docker-stopContainer` / `startContainer` | Graceful stop/start |
| `mcp__dokploy__docker-removeContainer` | Hard-delete; Dokploy will recreate on next `deploy` |
| `mcp__dokploy__docker-uploadFileToContainer` | Push a one-off config or credential without rebuilding (use sparingly — does not survive redeploy) |

> **Crash loop pattern:** state oscillates between `restarting` and `exited`. Always read `docker-getConfig` and check the `RestartPolicy` and the container's exit code before chasing the wrong issue.

---

## Step 4 — Check the request path (502 / 504 / wrong content)

If the container is running but HTTPS clients see 502 / 504 / wrong response, the failure is between Traefik and the container.

```
mcp__dokploy__application-readTraefikConfig
  → { applicationId }
```

Look for:

| Symptom in Traefik config | Cause | Fix |
|---|---|---|
| Service URL points to wrong port | Domain port doesn't match the port the app actually listens on | `domain-update` to correct port |
| `Bad Gateway` from Traefik logs | App bound to `127.0.0.1` instead of `0.0.0.0` | Fix env / startup args in the app code; redeploy |
| No router for this host | Domain not attached, or attached to wrong resource (app vs compose) | `domain-byApplicationId` / `domain-byComposeId`; re-create with `domain-create` |
| TLS cert error | Domain added before DNS propagation, or DNS not pointing at server | `domain-validateDomain`; fix DNS; delete and re-add with `https: true, certificateType: "letsencrypt"` |
| App not on `dokploy-network` | Container isn't routable from Traefik | Inspect via `docker-getConfig`; for compose, every public-facing service needs `networks: [dokploy-network]` |

If the resource is exposing ports directly (`ports: ["80:80"]` in compose), there will be a **port collision** with Traefik (80/443/8080). Either remove the explicit port mapping (let Traefik handle it via labels) or change the host port.

---

## Step 5 — Recover

Pick the smallest action that unblocks the user. Always confirm destructive operations first.

| Goal | Tool | Notes |
|---|---|---|
| Stop the failing build immediately | `application-killBuild` / `compose-killBuild` | Aborts the in-progress builder process |
| Cancel a queued/in-flight deploy | `application-cancelDeployment` / `compose-cancelDeployment` | Marks the deploy as cancelled, releases the queue slot |
| Clear a stuck queue | `application-cleanQueues` / `compose-cleanQueues` / `settings-cleanAllDeploymentQueue` | Use when multiple deploys are wedged |
| Forget a specific bad deployment record | `application-dropDeployment` / `deployment-removeDeployment` | Removes one row from history without affecting others |
| Wipe deployment history | `application-clearDeployments` / `compose-clearDeployments` | Use sparingly — destroys audit trail |
| Force "running" state on a healthy-but-misreported container | `application-markRunning` | Cosmetic only — does not start anything |
| Roll back to the previous good version | `mcp__dokploy__rollback-rollback { rollbackId }` | Look up valid rollbacks via the app's `rollbacks` array on `application-one`. Use `/dokploy-dev:rollback` for the guided flow |
| Reclaim disk and clear build cache | `settings-cleanDockerBuilder`, `cleanUnusedImages`, `cleanUnusedVolumes`, `cleanStoppedContainers` | Use `/dokploy-dev:cleanup` for the guided flow |
| Kill a wedged runtime container | `docker-killContainer` then `application-redeploy` | Fastest path out of a crash loop |

---

## Step 6 — Ask the AI to summarise (when available)

If an AI provider is configured (`mcp__dokploy__ai-getEnabledProviders` returns at least one), let it digest the build log and recommend a fix instead of grepping manually.

```
mcp__dokploy__ai-analyzeLogs
  → { deploymentId: "<failed deploymentId>" }
```

The response includes a natural-language root-cause summary and suggested remediation. For broader recommendations (e.g. "given this app, what should I check next?"), use `ai-suggest`. See the [`ai-assist`](../ai-assist/SKILL.md) skill for full setup and provider configuration.

> If `ai-getEnabledProviders` returns an empty list, AI is not configured — either wire it up via `ai-create` + `ai-testConnection`, or do the analysis manually using the patterns in Step 2's table.

---

## Step 7 — Verify the fix

After applying a fix:

1. `application-redeploy` (or `compose-redeploy`) — re-runs with the corrected config.
2. Poll `deployment-all` filtered by the resource ID — wait for `status: done`.
3. `domain-validateDomain` if a domain is involved.
4. `docker-getContainersByAppLabel` — confirm the container is `running` and `healthy`.
5. `curl -sI <domain>` — final HTTP 200 / expected status.

If the fix didn't take, **go back to Step 1**. Do not chain more fixes on top of an unverified state.

---

## Failure mode → recovery quick reference

| Failure mode | First diagnostic | Recovery |
|---|---|---|
| Build fails repeatedly | Step 2 build log | Fix Dockerfile / build type; `killBuild` + `redeploy` |
| Build succeeds, container crash-loops | Step 3 `docker-getConfig`, runtime log | Fix env vars / start command; `redeploy` |
| Deploy "done" but site unchanged | Step 1 — check for compose+app mismatch | Deploy the *compose* resource, not the standalone app |
| 502 Bad Gateway | Step 4 Traefik config; check `0.0.0.0` binding | Fix listen address; `redeploy` |
| TLS handshake error | Step 4; `domain-validateDomain` | Fix DNS, recreate domain with letsencrypt |
| Deploy stuck `queued` | Step 1 `queueList` | Step 5 `cleanQueues` |
| Disk-full silent failure | Step 0 `getDockerDiskUsage` | `/dokploy-dev:cleanup`; `redeploy` |
| Registry pull fails | Build log "unauthorized" | `registry-all`; re-add creds; `redeploy` |
| Database connection refused from app | `docker-getConfig` (check network), DB `readLogs` | Ensure both containers on same network; verify DB deployed |

---

## When to escalate

- **Persistent 502 with everything green** → server resource exhaustion. Check `server-getServerMetrics` and `settings-checkInfrastructureHealth`.
- **Cluster / Swarm deploy failures** → `cluster-getNodes`, `swarm-getNodeInfo`. Out-of-quorum nodes break Swarm deploys silently.
- **Traefik returns nothing for any domain** → `settings-readTraefikConfig` and the dynamic config under `/etc/dokploy/traefik/dynamic/`. A malformed dynamic config takes the whole router down.
- **API endpoints returning 401 mid-session** → API key was rotated or revoked. Regenerate in **Settings > API/Tokens**.
