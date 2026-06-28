---
description: Run an ad-hoc restic backup now and show the resulting snapshot
argument-hint: "[--dry-run]"
allowed-tools: ["Bash", "Read", "Skill"]
---

# restic Backup Now

Trigger an immediate, off-schedule backup using the existing configured script — useful before a risky change or to confirm a freshly-set-up backup works.

Parse `[--dry-run]` from "$ARGUMENTS".

## Process

1. **Preflight** — confirm the setup exists:
   ```bash
   test -x /usr/local/sbin/restic-backup.sh && test -f /root/.restic/r2.env \
     || echo "Backup not set up yet — use the restic-backup-engineer agent / setup skills first."
   ```

2. **Dry run** (if `--dry-run`):
   ```bash
   set -a; . /root/.restic/r2.env; set +a
   restic backup --dry-run --files-from /etc/restic/backup-paths.txt --exclude-file /etc/restic/excludes.txt -v
   ```
   Report what would be backed up, then stop.

3. **Run** (otherwise) — prefer the real script so DB dumps + retention run too:
   ```bash
   /usr/local/sbin/restic-backup.sh
   ```

4. **Show the result:**
   ```bash
   set -a; . /root/.restic/r2.env; set +a
   restic snapshots --latest 1
   restic stats latest
   ```

5. **Report** the new snapshot (id, time, size). If it exits 3, note that's a partial-read success, not a failure. On a real failure (1/10/11/12), point to the `troubleshoot` skill.

Concurrency: if the scheduled run might be active, avoid a second simultaneous run (repo lock). Check `restic list locks` first if unsure.
