---
description: Reclaim disk space on the Dokploy server with a guided cleanup chain
argument-hint: [--dry-run]
allowed-tools: [Read, Bash, Skill, Agent]
---

# Dokploy Server Cleanup

Guided cleanup chain to reclaim disk space. Always reports current usage first, then walks through each cleanup operation with explicit user confirmation.

Use this when builds start failing with `no space left on device`, deploys silently time out, or `settings-getDockerDiskUsage` reports >90% utilisation.

## Arguments

Format: `[--dry-run]` (optional)

- `--dry-run` — show what would be cleaned without actually executing any destructive operation.

Parse from "$ARGUMENTS".

## Process

1. **Report current state:**

   ```
   mcp__dokploy__settings-getDockerDiskUsage
   ```

   Show:
   - Total / used / available disk
   - Per-category sizes: Images, Containers, Volumes, Build cache
   - Top 5 largest images / volumes (if returned)

2. **Walk through cleanup operations** in this order. Confirm each with the user (unless `--dry-run`):

   | Step | Tool | What it does | Risk |
   |------|------|--------------|------|
   | a | `mcp__dokploy__settings-cleanDockerBuilder` | Clears the Docker BuildKit cache | None — only cache |
   | b | `mcp__dokploy__settings-cleanStoppedContainers` | Removes containers in `exited` state | None — already stopped |
   | c | `mcp__dokploy__settings-cleanUnusedImages` | Removes images not currently used by any container | Low — images can be rebuilt |
   | d | `mcp__dokploy__settings-cleanUnusedVolumes` | Removes volumes not attached to any container | **Medium — destroys data**. Confirm explicitly; orphan volumes can still contain DB files |
   | e | `mcp__dokploy__settings-cleanDockerPrune` | Equivalent to `docker system prune` | Low — combination of a-c |
   | f | `mcp__dokploy__settings-cleanMonitoring` | Removes monitoring data | None |
   | g | `mcp__dokploy__settings-cleanRedis` | Flushes Dokploy's internal Redis cache | None — Dokploy will repopulate |

   Skip steps `d` and `g` unless the user explicitly opts in.

3. **Report final state:**
   - Re-run `settings-getDockerDiskUsage` and show the delta in plain language ("Reclaimed 12.4 GB").

4. **Configure log cleanup automation (optional):**
   - `mcp__dokploy__settings-getLogCleanupStatus` — show current schedule.
   - Offer to enable / tune via `settings-updateLogCleanup` if disk pressure was caused by log accumulation.

## When to stop

If `cleanDockerBuilder` + `cleanUnusedImages` reclaim less than 5% disk, the bottleneck isn't Docker. Check:

- Big application volumes (databases that grew unbounded).
- `/etc/dokploy/logs/` accumulation — `getLogCleanupStatus` will show if rotation is off.
- The host filesystem outside Docker (`/var/log`, large user files).

In that case, escalate: ssh to the server and run `du -sh /var/lib/docker /etc/dokploy /var/log`.

## Example Usage

```
/dokploy-dev:cleanup
/dokploy-dev:cleanup --dry-run
```
