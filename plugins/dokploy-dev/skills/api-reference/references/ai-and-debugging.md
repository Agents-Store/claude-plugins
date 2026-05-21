# Dokploy REST API — AI Router, Debugging & Recovery

REST endpoint reference for the AI router, debugging-oriented endpoints across multiple routers, and recovery actions. Pair this with the `debug-deploy` and `ai-assist` skills.

All endpoints follow `{METHOD} /api/{tag}.{operationName}` with `x-api-key` auth.

## Contents
- [AI Router](#ai-router)
- [Deployment Inspection](#deployment-inspection)
- [Application / Compose Log Endpoints](#application--compose-log-endpoints)
- [Docker Introspection](#docker-introspection)
- [Recovery Actions](#recovery-actions)
- [Rollback](#rollback)
- [Settings — Health & Cleanup](#settings--health--cleanup)
- [Common Diagnostic Curl Recipes](#common-diagnostic-curl-recipes)

---

## AI Router

Dokploy v0.29+ provider-agnostic LLM integration.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/ai.getEnabledProviders` | List currently-enabled providers (empty = AI unavailable) |
| GET | `/api/ai.getAll` | All providers (enabled and disabled) |
| GET | `/api/ai.get` | One provider (input: `aiId`) |
| GET | `/api/ai.one` | Same as `get` (alias) |
| GET | `/api/ai.getModels` | Models advertised by a provider (input: `aiId`) |
| POST | `/api/ai.create` | Add a provider: `name`, `apiKey`, `apiUrl`, `model`, `isEnabled` |
| POST | `/api/ai.update` | Update provider config |
| POST | `/api/ai.delete` | Remove a provider |
| POST | `/api/ai.testConnection` | Validate credentials/reachability |
| POST | `/api/ai.deploy` | Deploy AI orchestrator side-service (admin) |
| POST | `/api/ai.analyzeLogs` | **Headline:** AI-summarise a deployment's build log. Input: `deploymentId` |
| POST | `/api/ai.suggest` | Open-ended recommendations. Input: `applicationId` (or compose), optional `prompt` |

### `apiUrl` examples

All providers must speak the OpenAI chat-completions shape:

| Provider | `apiUrl` |
|---|---|
| OpenAI | `https://api.openai.com/v1` |
| OpenRouter | `https://openrouter.ai/api/v1` |
| Groq | `https://api.groq.com/openai/v1` |
| Gemini (OpenAI-compatible) | `https://generativelanguage.googleapis.com/v1beta/openai` |
| Anthropic (via OAI proxy) | proxy URL |
| Ollama (self-hosted) | `http://<host>:11434/v1` |

---

## Deployment Inspection

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/deployment.all` | List deployments, filter by `applicationId` / `composeId` / `serverId` |
| GET | `/api/deployment.allByCompose` | Deployments for a compose stack |
| GET | `/api/deployment.allByServer` | Deployments for a remote server |
| GET | `/api/deployment.allByType` | Filter by `type` (`deploy`, `rollback`, `redeploy`, etc.) |
| GET | `/api/deployment.allCentralized` | Every deployment across the instance |
| GET | `/api/deployment.queueList` | Inspect the live deployment queue |
| POST | `/api/deployment.killProcess` | Kill a deployment process by `deploymentId` |
| POST | `/api/deployment.removeDeployment` | Remove a deployment record |

The deployment object includes `status`, `startedAt`, `finishedAt`, `logPath`, `errorMessage`, `triggerType`, and `version` — everything `debug-deploy` Step 1 needs.

---

## Application / Compose Log Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/application.readLogs` | Build log metadata + `logPath` for an application |
| POST | `/api/application.readAppMonitoring` | CPU / memory / network for an application |
| POST | `/api/application.readTraefikConfig` | Traefik router/service entries for an application |
| POST | `/api/application.updateTraefikConfig` | Overwrite Traefik config |
| POST | `/api/compose.readLogs` | Build log metadata + `logPath` for a compose stack |
| POST | `/api/{db}.readLogs` | DB container log metadata (`{db}` is `postgres`/`mysql`/`mariadb`/`mongo`/`redis`/`libsql`) |

> `readLogs` returns the **build** log artifact. Live container stdout/stderr is not exposed via REST yet — track [issue #3719](https://github.com/Dokploy/dokploy/issues/3719). Workaround: read the file at `logPath` via Beszel or SSH.

---

## Docker Introspection

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/docker.getContainers` | All containers on the host |
| GET | `/api/docker.getContainersByAppLabel` | Containers matching a Dokploy app label (`appName`) |
| GET | `/api/docker.getContainersByAppNameMatch` | Loose substring match |
| GET | `/api/docker.getServiceContainersByAppName` | Swarm service containers |
| GET | `/api/docker.getStackContainersByAppName` | Compose stack service containers |
| GET | `/api/docker.getConfig` | Full container config (env, command, mounts, network) |
| POST | `/api/docker.startContainer` | Start by `containerId` |
| POST | `/api/docker.stopContainer` | Graceful stop |
| POST | `/api/docker.restartContainer` | Restart in place |
| POST | `/api/docker.killContainer` | SIGKILL |
| POST | `/api/docker.removeContainer` | Hard-delete |
| POST | `/api/docker.uploadFileToContainer` | One-off file push (does NOT survive redeploy) |

---

## Recovery Actions

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/application.killBuild` | Abort the running builder process |
| POST | `/api/application.cancelDeployment` | Cancel queued/in-flight deploy |
| POST | `/api/application.cleanQueues` | Clear the application's stuck queue |
| POST | `/api/application.clearDeployments` | Wipe deployment history (destructive) |
| POST | `/api/application.dropDeployment` | Drop a single deployment record |
| POST | `/api/application.markRunning` | Force `running` status (cosmetic only) |
| POST | `/api/compose.killBuild` | Abort compose builder |
| POST | `/api/compose.cancelDeployment` | Cancel compose deploy |
| POST | `/api/compose.cleanQueues` | Clear compose queue |
| POST | `/api/compose.clearDeployments` | Wipe compose deployment history |
| POST | `/api/settings.cleanAllDeploymentQueue` | Clear stuck queues across every resource |

---

## Rollback

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/rollback.rollback` | Switch a resource to a previously-successful image. Input: `rollbackId` |
| POST | `/api/rollback.delete` | Remove a rollback record |

Rollback points live on the resource object — `application-one` and `compose-one` responses include a `rollbacks` array with `rollbackId`, `version`, `deploymentId`, `createdAt`, and `description`.

---

## Settings — Health & Cleanup

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/settings.health` | Liveness probe (no auth required) |
| GET | `/api/settings.checkInfrastructureHealth` | Docker + Traefik + disk + network composite check |
| GET | `/api/settings.checkGPUStatus` | GPU availability |
| GET | `/api/settings.getDockerDiskUsage` | Per-category disk usage |
| GET | `/api/settings.getLogCleanupStatus` | Log rotation status |
| GET | `/api/settings.getDokployVersion` / `.getReleaseTag` / `.getUpdateData` | Version metadata |
| GET | `/api/settings.getIp` / `.getDokployCloudIps` | Server IPs |
| GET | `/api/settings.getTraefikPorts` | Currently-bound Traefik ports |
| GET | `/api/settings.haveTraefikDashboardPortEnabled` | Dashboard exposure check |
| POST | `/api/settings.cleanDockerBuilder` | Clear BuildKit cache |
| POST | `/api/settings.cleanDockerPrune` | `docker system prune` equivalent |
| POST | `/api/settings.cleanStoppedContainers` | Remove exited containers |
| POST | `/api/settings.cleanUnusedImages` | Remove dangling images |
| POST | `/api/settings.cleanUnusedVolumes` | **Destructive** — orphan volumes |
| POST | `/api/settings.cleanMonitoring` | Reset monitoring data |
| POST | `/api/settings.cleanRedis` | Flush Dokploy's Redis cache |
| POST | `/api/settings.cleanAll` | Combined: builder + prune + monitoring + redis |
| POST | `/api/settings.updateLogCleanup` | Tune log rotation |
| POST | `/api/settings.reloadTraefik` / `.reloadServer` / `.reloadRedis` | Restart subsystems |

---

## Common Diagnostic Curl Recipes

### Find the latest failed deployment for an app

```bash
curl -s -G "$DOKPLOY_URL/api/deployment.all" \
  -H "x-api-key: $DOKPLOY_API_KEY" \
  --data-urlencode "input={\"json\":{\"applicationId\":\"$APP_ID\"}}" \
  | jq '.result.data.json | map(select(.status=="error")) | sort_by(.startedAt) | last'
```

### Inspect the container behind an app

```bash
APP_NAME=my-app
curl -s -G "$DOKPLOY_URL/api/docker.getContainersByAppLabel" \
  -H "x-api-key: $DOKPLOY_API_KEY" \
  --data-urlencode "input={\"json\":{\"appName\":\"$APP_NAME\"}}" \
  | jq '.result.data.json[0] | {Id, State, Status, Health: .State.Health.Status}'
```

### AI-analyse a deployment

```bash
curl -s -X POST "$DOKPLOY_URL/api/ai.analyzeLogs" \
  -H "x-api-key: $DOKPLOY_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"json\":{\"deploymentId\":\"$DEPLOY_ID\"}}"
```

### Clean disk cache

```bash
for op in cleanDockerBuilder cleanStoppedContainers cleanUnusedImages; do
  curl -s -X POST "$DOKPLOY_URL/api/settings.$op" \
    -H "x-api-key: $DOKPLOY_API_KEY" -H "Content-Type: application/json" -d '{"json":{}}'
done
```

### Rollback

```bash
curl -s -X POST "$DOKPLOY_URL/api/rollback.rollback" \
  -H "x-api-key: $DOKPLOY_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"json\":{\"rollbackId\":\"$ROLLBACK_ID\"}}"
```
