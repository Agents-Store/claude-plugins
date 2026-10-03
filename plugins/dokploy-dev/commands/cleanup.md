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
   mcp__plugin_dokploy-dev_dokploy__settings-getDockerDiskUsage
   ```

   It returns one row per category (`type`, `totalCount`, `active`, `size`, `reclaimable`, `sizeBytes`) for Images, Containers, Local Volumes and Build Cache. Show:
   - Per-category size and reclaimable space (read `reclaimable` — it tells you which step is worth running)
   - Host disk used / total: on v0.30+ call `mcp__plugin_dokploy-dev_dokploy__docker-getServerHealth` and read `disk.usedBytes` / `disk.totalBytes`
   - Top 5 largest images / volumes (v0.30+: `dockerImage-getImages`, `dockerVolume-getVolumesSize`)
   - For a remote server pass `serverId` to the `dockerDiskUsage-*` / `docker-getServerHealth` tools; the `settings-clean*` tools below (except `cleanMonitoring`) accept an optional `serverId` too

2. **Walk through cleanup operations** in this order. Confirm each with the user (unless `--dry-run`):

   | Step | Tool | What it does | Risk |
   |------|------|--------------|------|
   | a | `mcp__plugin_dokploy-dev_dokploy__settings-cleanDockerBuilder` | Clears the Docker BuildKit cache | None — only cache |
   | b | `mcp__plugin_dokploy-dev_dokploy__settings-cleanStoppedContainers` | Removes containers in `exited` state | None — already stopped |
   | c | `mcp__plugin_dokploy-dev_dokploy__settings-cleanUnusedImages` | Removes images not currently used by any container | Low — images can be rebuilt |
   | d | `mcp__plugin_dokploy-dev_dokploy__settings-cleanUnusedVolumes` | Removes volumes not attached to any container | **Medium — destroys data**. Confirm explicitly; orphan volumes can still contain DB files |
   | e | `mcp__plugin_dokploy-dev_dokploy__settings-cleanDockerPrune` | Equivalent to `docker system prune` | Low — combination of a-c |
   | f | `mcp__plugin_dokploy-dev_dokploy__settings-cleanMonitoring` | Removes monitoring data | None |

   Skip step `d` unless the user explicitly opts in.

3. **Report final state:**
   - Re-run `settings-getDockerDiskUsage` and show the delta in plain language ("Reclaimed 12.4 GB").

4. **Configure log cleanup automation (optional):**
   - `mcp__plugin_dokploy-dev_dokploy__settings-getLogCleanupStatus` — show current schedule.
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
