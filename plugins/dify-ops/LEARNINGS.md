# LEARNINGS

## 2026-10-03 — update command: Pre-flight the Weaviate migration path and back up before the merge

**Problem:** `/dify-ops:update` merged `origin/main` and ran `docker compose up -d` with no version check and no backup. On an install older than 1.17.1 with the bundled Weaviate that pulls server 1.39.2 over a 1.27.0 data volume; upstream says vector search then breaks silently and permanently, and a hard kill during any stop does the same. The 2026-03-27 backup fix had reached the skill and the scenarios but never the command, and it archived `volumes/` after the merge, from running containers.
**Fix:** `commands/update.md` now runs a read-only pre-flight first (git state, Compose >= 2.24.0, project name from labels, target tag, release notes of every version in between, Weaviate gate), prints the eight-block plan, and backs up with the stack down (compose and `.env` copied, Weaviate stopped with `-t -1`, `docker compose down`, `volumes/` archived outside the repo, no secrets in the output) before the merge and before `up -d`. The gate stops the update when the running version is below 1.17.1, the target is 1.17.1 or newer, `VECTOR_STORE=weaviate` and `volumes/weaviate` holds data; it hands the user the official runbook and `--weaviate-staged` lifts it afterwards. ROLLBACK is one runnable line restoring git and the volumes. Version 1.1.0.
**Root cause:** The plugin was written for Dify 1.0 to about 1.14, when an update was a plain merge and a restart and image bumps never needed a staged data migration. The 2026-03-27 fix was applied to the documentation of the workflow instead of the command that runs it.
**Severity:** Critical

## 2026-10-03 — update-workflow, env-sync, dify-docker-architecture, examples: Align with the Dify 1.17.x layout

**Problem:** The plugin described Dify 1.0 to 1.14: default target `latest main`, a `v` fallback for tags that never had one, `docker compose up -d` with a build flag although no service builds, host ports set through `NGINX_PORT`, customizations merged by hand into the generated compose file, one monolithic `.env.example`, 11 services, wrong plugin daemon port, wrong volume paths, `pg_dump` of one database, container-name parsing for the project name, and example scenarios built on invented variables.
**Fix:** Default target is the latest stable tag (tags have no `v`, `main` only on request); pull instead of build; host ports are `EXPOSE_NGINX_PORT` and `EXPOSE_NGINX_SSL_PORT`; customizations go to `.env`, `envs/` and `docker-compose.override.yaml`, and upstream's files win conflicts on the generated compose file; env-sync covers `envs/**` templates, the official `dify-env-sync.sh` and the keys a name comparison misses (`COMPOSE_PROFILES` needs `collaboration`, `EDITION` became `DEPLOYMENT_EDITION`, a changed retention default); the architecture skill lists the 1.17.x services, paths and ports; both scenarios were rewritten on real variables and the Weaviate STOP.
**Root cause:** Nothing tied the plugin to a Dify version, so it aged silently while upstream split `.env.example` into `envs/`, generated the compose file and added the agent services.
**Severity:** Major

## 2026-10-03 — env-sync: The official dify-env-sync.sh prints secrets

**Problem:** `dify-env-sync.sh` prints the current `.env` value of every key whose value differs from `.env.example` — passwords, `SECRET_KEY`, API keys included. Run inside an agent session, those values land in the transcript. The previous guidance only said to offer the script.
**Fix:** The script is now the default sync path, but only through an `awk` filter that strips ANSI codes and masks the value of any key whose name looks secret. The same filter is in `commands/update.md` and in the env-sync skill; the backup step copies `.env` and never prints it.
**Root cause:** The script was written for a human at a terminal; nobody had read what it echoes.
**Severity:** Major

## 2026-03-27 — update-workflow: Add volume backup before container rebuild

**Problem:** The update workflow went straight from git merge + env sync to `docker compose up -d` without backing up Docker volumes. Volumes contain postgres data, redis state, weaviate vectors, and file storage — a failed rebuild or bad migration could cause irreversible data loss.
**Fix:** Added a "Post-merge: Volume Backup" section to update-workflow SKILL.md that runs `tar -cvf volumes-$(date +%s).tgz volumes` in the docker directory before rebuilding. Updated both example scenarios (routine-update, tagged-release-update) to include the backup step.
**Root cause:** Initial skill creation focused on git workflow and env sync, overlooked the data safety step before destructive container operations.
**Severity:** Critical
