# LEARNINGS

## 2026-03-27 — update-workflow: Add volume backup before container rebuild

**Problem:** The update workflow went straight from git merge + env sync to `docker compose up -d` without backing up Docker volumes. Volumes contain postgres data, redis state, weaviate vectors, and file storage — a failed rebuild or bad migration could cause irreversible data loss.
**Fix:** Added a "Post-merge: Volume Backup" section to update-workflow SKILL.md that runs `tar -cvf volumes-$(date +%s).tgz volumes` in the docker directory before rebuilding. Updated both example scenarios (routine-update, tagged-release-update) to include the backup step.
**Root cause:** Initial skill creation focused on git workflow and env sync, overlooked the data safety step before destructive container operations.
**Severity:** Critical
