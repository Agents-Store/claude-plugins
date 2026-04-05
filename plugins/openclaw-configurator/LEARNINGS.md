# Learnings

## 2026-04-05 — instance-update: Tag-based update command for multi-instance Docker deployments

**Feature:** New `/openclaw-configurator:instance-update` command that fetches the latest official release tag, merges it into the local `dev` branch preserving customizations, and rebuilds Docker containers.
**Implementation:** Created `commands/instance-update.md` — 12-step workflow with pre-flight checks, docker-compose backup, tag-based merge, conflict resolution strategy (auto-accept upstream for source, manual merge for docker-compose), syntax validation, container rebuild and verification.
**Rationale:** OpenClaw instances run as git clones with a local `dev` branch holding per-project docker-compose customizations. Updates require merging tagged releases (not branch tracking) while preserving these local changes. Modeled after `dify-ops/commands/update.md` but adapted for tag-based releases and docker-compose-centric customizations (vs Dify's .env-centric approach).
