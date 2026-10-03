# restic-dev — Learnings

Accumulated fixes and discoveries for the restic backup plugin. Newest first.

<!-- Format:
## [YYYY-MM-DD] — [skill-name]: Brief description
**Problem:** What went wrong
**Fix:** What was changed
**Root cause:** Why the original was wrong
**Severity:** Critical / Major / Minor
-->

## [2026-10-03] — monitoring, status: freshness check read the first snapshot, not the newest
**Problem:** `restic snapshots --json --latest 1` returns the newest snapshot per host/path group; the freshness snippet used `s[0]`, which is an arbitrary group's snapshot, so a repo with several path sets could report a stale age (or a false "fresh").
**Fix:** take the maximum `time` over everything returned (`max(...)`); `status` computes the age the same way. restic 0.19.0 briefly stopped grouping `--latest <n>` by default, 0.19.1 restored it — the `max` is right on every version. Recommended restic is now >= 0.19.1.
**Root cause:** the snippet assumed one snapshot is returned. Verified on a throwaway repo with two path sets (0.19.1).
**Severity:** Minor

## [2026-10-03] — backup-script, troubleshoot, cli-reference: restic 0.19 exit codes and `forget`
**Problem:** docs said exit 3 = "some files unreadable" only and "130 = SIGINT/SIGTERM", and the script silently tolerated 3. Since 0.19.0 `backup` also returns 3 for a missing source path (it returned 0 for a top-level path), `forget` returns 3 when it cannot remove a snapshot (it returned 0), and cancel returns 130. Invalid `RESTIC_COMPRESSION` / `RESTIC_PACK_SIZE` / `RESTIC_READ_CONCURRENCY` is now a fatal error instead of being ignored. Excludes no longer apply to root paths named on the command line.
**Fix:** exit-code tables split by command (3 from `backup` = partial success, log it; 3 from `forget` = real failure). The script logs the `backup` 3 and fails with the original code on any non-zero `forget` (so the `/fail` ping fires). Documented the new env validation, the exclude change, `--skip-if-unchanged`, `--retry-lock`, `check --tag/--host/--path`, `restore --ownership-by-name --verify`, `GITHUB_ACCESS_TOKEN` for `self-update`, `RESTIC_COMPRESSION=fastest|better`, `--keep-tag` + `safe-forget-keep-tags` + `--unsafe-allow-remove-all`, and the missing commands (`mount`, `cache`, `recover`, `features`, `options`). Verified against restic 0.19.1: `backup` with an existing and a missing path exits 3 with a snapshot; only missing paths exits 1; `forget` against an undeletable snapshot file exits 3; SIGINT and SIGTERM both exit 130.
**Root cause:** the docs described pre-0.19 semantics. Note: SIGTERM also gives 130 (the upstream changelog only names SIGINT).
**Severity:** Major

## [2026-10-03] — cli-reference: wrong `init` flag, deprecated `rebuild-index`
**Problem:** `restic init [--from-repository ... (copy keys)]` — `--from-repository` is not a flag (restic answers `unknown flag`); the flag is `--from-repo`, and with `--copy-chunker-params` it copies the source repository's chunker parameters, not keys. `restic rebuild-index` was presented as a working "older alias".
**Fix:** `init` line rewritten (`--repository-version <N|latest|stable>`, `--from-repo`, `--from-password-file`, `--copy-chunker-params`); `rebuild-index` replaced by `repair index` everywhere and marked deprecated (restic prints `Command "rebuild-index" is deprecated, Use "repair index" instead`).
**Root cause:** the flag name did not match `restic init --help`.
**Severity:** Minor
