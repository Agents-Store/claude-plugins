---
description: Deduplicate skills and plugins across instances, promote the identical ones into the shared trees, register them, remove the local copies that shadow them, and verify on four levels
argument-hint: "[selector] [--adopt-duplicates] [--restart] [--yes]"
allowed-tools: ["Bash", "Read", "Skill"]
---

# Shared skills and plugins — sync

Parse `[selector] [--adopt-duplicates] [--restart] [--yes]` from "$ARGUMENTS". Scripts live in
`${CLAUDE_PLUGIN_ROOT}/scripts/` and are named bare below. Load `shared-assets` first — it owns the load order,
the shadow trap, the install policy, ownership and the four verification levels. Mutation: plan first, `--yes` later.

## Process

1. **Targets.** `fleet.py resolve "<selector>" --mutation --json`. Empty and `all` are refused — a
   selector that widens as the fleet grows is how one promotion becomes a fleet incident.
   `fleet.py discover --json` gives the mount table: shared trees, asset paths, shared skills/plugins.
2. **Inventory and hash on the host.** Digest each asset directory from its host path
   (`find … -type f | sort` piped to `sha256sum`); group asset → present on N, identical on M. Hashing
   answers "same file", never "what the process loads" — that is step 6, and they are not the same.
3. **Candidates.** `M == N` and no instance-specific content — grep each candidate for instance names,
   host paths from the mount table, ports and key prefixes. `M < N` is **reported, never touched**.
   `--adopt-duplicates` only widens the candidate set; it never overrides divergence.
4. **Plan — the eight blocks, and no shortcut through any of them:**
   - `TARGET` — instances by name, assets by name. Canary first (`gate.canary_barrier`); anything past
     it is a separate confirmation.
   - `PRECHECK` — hash groups with their N/M, divergences, the install lock read and parsed, ownership
     of the shared tree, whether `plugins.load.paths` changes (that forces a restart).
   - `CHANGE` — per file: promote, register, move-to-quarantine. **With a deletion count**, which must
     be zero: shadows are moved, never deleted.
   - `BACKUP` — `gate.snapshot` of every config to be edited plus the install lock, outside the
     runtime's own backup ring (`gate.bak_ring_warning`), path and fingerprint printed.
   - `IMPACT` — what stops loading between the move and the restart, and for how long.
   - `VALIDATE` — the four levels from `shared-assets`.
   - `ROLLBACK` — executable: `mv <quarantine>/<asset> <instance-asset-path>/<asset> && cp <snapshot>
     <config-path>`, plus the gateway restart when plugin paths moved.
   - `APPLY` — the exact command line, run only after the human answers.
5. **Apply (`--yes` in a later turn, the applying `ocexec.py` call carrying the id from
   `gate.py plan mint shared-sync <instance>` as `--plan-id`).** Promote the canonical copy into the shared tree, align ownership
   **on the host side**, register through `config-surgery` (`skills.load.extraDirs`,
   `plugins.load.paths`), then move every shadow into quarantine. Restart when plugin paths changed or
   `--restart` was given. Good→changed, so **fail fast** on the first failure.
6. **Verify — all four levels of `shared-assets`, in order**, none skipped: shared tree listed from
   inside the container · effective config read back · registered assets **with the path each resolved
   from** · loaded plugins compared against the config after a restart.

## Rules

- `skills install --global` is never used (`fleet.shared.install-global-invisible`); ownership is
  aligned on the host (red line `in-container-write-outside-mount`).
- Zero retries on a failed install (`gate.RETRY_RULES`); one failure stops the batch and the lock gets
  read (`fleet.shared.lock-corrupt`, red line `skill-install-unread-lock`).
- Capability consent is printed for a human; the accept flag is never passed (`gate.BANNED_ARGS`).

## Example

```
/openclaw-ops:shared-sync @canary
/openclaw-ops:shared-sync managed,-vintage --adopt-duplicates
```
