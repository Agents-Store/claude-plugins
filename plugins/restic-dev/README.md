# restic-dev

Set up **encrypted, scheduled `restic` backups on any Linux server** to S3-compatible object storage (Cloudflare R2 first-class) — a Technology (dev) plugin for the Agents Store marketplace. Knowledge-only: **no MCP server, no stored credentials**. Everything runs through the `restic` binary on the target server; R2 keys and the encryption password are created at runtime on that server (`/root/.restic/`, mode `600`) and never touch the plugin or git.

## What it covers

You give the plugin your S3/R2 access and the folder where your Docker projects live. It recons the server, **auto-discovers what to back up** — every container's bind-mounts and named volumes (including data living *outside* the named folder), separating regenerable junk and databases (which get logical dumps, not file copies) — then wires up an encrypted R2 repository, a partial-failure-tolerant daily backup script, a timezone-aware schedule, verification with a real test-restore, ongoing monitoring, and disaster recovery.

## Skills

| Skill | Use it for |
|-------|------------|
| `setup` | Server recon (arch/init/timezone/disk/docker) and install the correct latest `restic` binary |
| `discover-backup-sources` | ⭐ Auto-discover every Docker volume/mount + databases and produce a concrete backup plan |
| `repository-setup` | Encryption password, R2/S3 credentials, repository URL, `restic init` (and R2 AccessDenied fixes) |
| `backup-script` | The daily script: logical DB dumps, exit-code-3 tolerance, `forget`/`prune` retention, excludes |
| `scheduling` | Timezone-aware systemd timer (or cron fallback on non-systemd hosts) |
| `verify-backup` | First run, `snapshots`, `check`, test-restore + diff — the gate before enabling the schedule |
| `monitoring` | Dead-man's-switch, failure alerts, snapshot-freshness checks, periodic integrity `check` |
| `disaster-recovery` | Restore files/volumes/databases and rebuild on a fresh server |
| `troubleshoot` | Exit codes, R2/S3 errors, stale locks, repo/index repair, cron-only failures |
| `cli-reference` | Full command / flag / environment-variable reference (manual-load only) |
| `examples` | End-to-end scenario walkthroughs (Docker server → R2, cron host, disaster recovery, multi-DB) |

## Agent

`restic-backup-engineer` — a restic backup specialist that recons a server, discovers what to back up, configures the R2 repository, writes and schedules a verified daily backup, monitors it, and drives disaster recovery. Confirms before any destructive operation and never enables a schedule until a test-restore passes.

## Commands

| Command | Does |
|---------|------|
| `/restic-dev:status` | Are backups healthy? Timer state, latest snapshot, freshness, log tail |
| `/restic-dev:restore` | Guided restore / disaster recovery |
| `/restic-dev:backup-now` | Run an ad-hoc backup now and show the resulting snapshot |

## Prerequisites

- A Linux server you can run commands on (SSH or local), with `docker` if you want volume auto-discovery
- S3-compatible object storage. For Cloudflare R2: a bucket and an **R2 API token with Object Read & Write**, plus the account endpoint `https://<account_id>.r2.cloudflarestorage.com`
- `restic` is installed by the `setup` skill if missing — no manual install required

No plugin configuration is required. The encryption password and storage credentials are generated and stored **on the target server** — keep an off-server copy of the password, or restore is impossible.

## Quick start

```bash
# Inside Claude Code, on (or connected to) the target server:
/restic-dev:status                     # if already set up — health at a glance
# or just ask the restic-backup-engineer agent:
#   "I have Docker projects in /docker and Cloudflare R2 keys. Set up daily backups."
```

## Notes

- restic always encrypts client-side (AES-256) — the password is the only key. **Losing it means total, unrecoverable data loss.**
- Built from the official docs at https://restic.readthedocs.io/ and Cloudflare R2's S3 API docs.

---

Made by **AGENTS.STORE**.
