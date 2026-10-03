---
description: Update self-hosted Dify — pre-flight (Weaviate migration gate), back up volumes with the stack down, merge a release tag into dev, sync env, pull images, verify
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
argument-hint: "[tag-or-version|main] [--yes] [--weaviate-staged]"
---

# Dify Update

Update a self-hosted Dify instance without losing data: read what the target release changes, stop the stack and archive `volumes/`, and only then merge the release tag into the local `dev` branch, sync environment variables, pull images and start. Nothing is changed before the plan in Step 3 is printed and confirmed.

The Bash tool does not keep shell variables between calls. Start each block below with the assignments from the earlier blocks (`DIFY_ROOT`, `DOCKER_DIR`, `PROJECT_NAME`, `CUR`, `TGT`, `TARGET`, `TARGET_REF`, `STAGED`, `PRE_UPDATE_COMMIT`, and `BACKUP_DIR` once Step 4 has made it); the plan prints their values.

## Arguments

`$ARGUMENTS` — an optional target plus flags:

- a release tag such as `1.17.1`. Dify tags carry no `v` prefix; GitHub release titles read `v1.17.1`, so a leading `v` is dropped
- `main` — merge `origin/main`. Its deployment files track development and can drift from the latest release; use it only when asked
- empty — the latest stable tag (`MAJOR.MINOR.PATCH`). `rc`, `alpha` and `beta` tags are never picked
- `--yes` — apply right after printing the plan, without the confirmation question. It never skips the Weaviate STOP, the dirty-tree question or conflict resolution
- `--weaviate-staged` — you already stepped the bundled Weaviate volume to `1.39.2` with the official runbook (Step 2, check 5). It lifts that one STOP and nothing else

## Step 1: Detect Working Directory

Determine whether the user is in `dify/` or in `dify/docker/`.

```bash
if [ -f "docker-compose.yaml" ] && [ -f ".env.example" ]; then
  DOCKER_DIR="$(pwd)"
  DIFY_ROOT="$(dirname "$(pwd)")"
elif [ -d "docker" ] && [ -f "docker/docker-compose.yaml" ]; then
  DOCKER_DIR="$(pwd)/docker"
  DIFY_ROOT="$(pwd)"
else
  echo "ERROR: Cannot find Dify Docker setup."
  echo "Run this from dify/ or dify/docker/ directory."
  exit 1
fi
echo "DIFY_ROOT=$DIFY_ROOT"
echo "DOCKER_DIR=$DOCKER_DIR"
```

## Step 2: Pre-flight (read-only)

Five checks. None of them changes the working tree, the containers or the volumes.

**1. Git state.** Run from `DIFY_ROOT`:

```bash
cd "$DIFY_ROOT"
git rev-parse --git-dir >/dev/null 2>&1 || { echo "ERROR: Not a git repo"; exit 1; }
BRANCH=$(git branch --show-current)
PRE_UPDATE_COMMIT=$(git rev-parse HEAD)
echo "Branch: ${BRANCH:-detached HEAD}   Commit: $PRE_UPDATE_COMMIT"
git show-ref --verify --quiet refs/heads/dev && echo "dev branch: present" || echo "dev branch: MISSING"
DIRTY=$(git status --porcelain)
[ -n "$DIRTY" ] && { echo "WARNING: Uncommitted changes:"; git status --short; }
```

- Dirty tree — ask: (1) commit first, (2) stash (`git stash`, run in Step 5 right before the merge; record `STASHED=true`), (3) abort.
- `dev` missing — the official `git clone --branch <tag>` leaves a detached HEAD and no `dev`. Tell the user Step 5 will run `git switch -c dev` before merging.

**2. Docker Compose >= 2.24.0** (the compose files use `env_file … required: false`):

```bash
CV=$(docker compose version --short 2>/dev/null | sed 's/^v//')
[ "$(printf '%s\n' "$CV" 2.24.0 | sort -V | head -1)" = 2.24.0 ] || { echo "ERROR: Docker Compose >= 2.24.0 required (found: ${CV:-none})"; exit 1; }
```

**3. Docker project name** — read it from the labels of the running `api` container of this directory, never parse container names:

```bash
cd "$DOCKER_DIR"
PROJECT_NAME=$(docker ps --filter "label=com.docker.compose.service=api" \
  --filter "label=com.docker.compose.project.working_dir=$DOCKER_DIR" \
  --format '{{.Label "com.docker.compose.project"}}' 2>/dev/null | head -1)
echo "Docker project: ${PROJECT_NAME:-none running — compose default (directory name, usually docker)}"
```

If `PROJECT_NAME` is set and differs from the directory name, put `export COMPOSE_PROJECT_NAME="$PROJECT_NAME"` at the top of every later block, so each `docker compose` call below reaches the right project.

**4. Target and versions.** Resolve the tag, then read the Dify version from the compose file of the target and of the current checkout:

```bash
cd "$DIFY_ROOT"
git fetch origin --tags            # moves remote-tracking refs and tags, never the working tree
STABLE='^[0-9]+\.[0-9]+\.[0-9]+$'
REQ=""; YES=no; STAGED=no          # parsed from the arguments; an empty REQ means the latest stable tag
for a in $ARGUMENTS; do
  case "$a" in --yes) YES=yes ;; --weaviate-staged) STAGED=yes ;; *) REQ="$a" ;; esac
done
case "$REQ" in
  "")   TARGET=$(git tag --list | grep -E "$STABLE" | sort -V | tail -1); TARGET_REF="$TARGET" ;;
  main) TARGET=main; TARGET_REF=origin/main ;;
  *)    TARGET="${REQ#v}"; TARGET_REF="$TARGET" ;;
esac
git rev-parse -q --verify "$TARGET_REF^{commit}" >/dev/null || {
  echo "ERROR: '$TARGET_REF' not found. Latest stable tags:"
  git tag --list | grep -E "$STABLE" | sort -V | tail -5
  exit 1; }
TGT=$(git show "$TARGET_REF:docker/docker-compose.yaml" | grep -m1 -oE 'langgenius/dify-api:[0-9][^ ]*' | cut -d: -f2)
CUR=$(grep -m1 -oE 'langgenius/dify-api:[0-9][^ ]*' "$DOCKER_DIR/docker-compose.yaml" | cut -d: -f2)
echo "Current: ${CUR:-unknown}   Target: $TARGET (images $TGT)"
```

An explicit pre-release tag is allowed with a warning that it is not for production.

**5. Weaviate migration gate.** From Dify 1.17.1 the bundled Weaviate server moves from `1.27.0` to `1.39.2`. An existing data volume cannot cross 12 minor versions in one step; pulling and restarting silently and permanently breaks vector search. The gate fires only for a bundled Weaviate that holds data, an update that crosses `1.17.1`, and no `--weaviate-staged`. A fresh install, an external Weaviate and every other `VECTOR_STORE` are not affected.

```bash
cd "$DOCKER_DIR"
VS=$(grep -E '^VECTOR_STORE=' .env 2>/dev/null | tail -1 | cut -d= -f2); VS=${VS:-weaviate}
WV_DATA=no
if [ -d volumes/weaviate ] && { [ -n "$(ls -A volumes/weaviate 2>/dev/null)" ] || [ ! -r volumes/weaviate ]; }; then WV_DATA=yes; fi
older() { [ "$(printf '%s\n' "$1" "$2" | sort -V | head -1)" != "$2" ]; }   # true when $1 < $2; an empty $1 counts as older
# CUR, TGT and STAGED come from check 4
if [ "$VS" = weaviate ] && [ "$WV_DATA" = yes ] && [ "$STAGED" != yes ] \
   && older "$CUR" 1.17.1 && { [ -z "$TGT" ] || ! older "$TGT" 1.17.1; }; then
  echo "STOP: this update crosses Dify 1.17.1 and the bundled Weaviate moves 1.27.0 -> 1.39.2."
  echo "An existing volume cannot jump 12 minor versions; a plain pull + up -d breaks vector search silently."
  echo "Nothing was changed. Runbook: https://docs.dify.ai/en/self-host/deploy/troubleshooting/weaviate-server-migration-path"
  exit 1
fi
echo "Weaviate gate: pass (VECTOR_STORE=$VS, volumes/weaviate data: $WV_DATA)"
```

On STOP do not run Step 4 or later: no merge, no `docker compose up -d`. Hand the user the runbook (summary in the `update-workflow` skill: back up the volume, step through every minor `1.27` → `1.38`, land exactly on `1.39.2`, always stop with `docker compose stop -t -1 weaviate`, never `docker kill` or `rm -f`), then offer three ways forward and ask which one:

1. Follow the runbook, confirm with `/v1/meta` that the server reports `1.39.2`, then run `/dify-ops:update <tag> --weaviate-staged`.
2. Update only to a release below `1.17.1` (for example `1.17.0`); the gate does not fire there.
3. Move to another vector store or an external Weaviate first (re-index the knowledge bases), then update.

If `CUR` or `TGT` could not be read the gate fails closed and stops the same way.

**Release notes for every step.** For each stable tag after `CUR` up to the target, show only the three sections that matter:

```bash
cd "$DIFY_ROOT"
git tag --list | grep -E "$STABLE" | sort -V | awk -v lo="$CUR" -v hi="$TARGET" 'p{print} $0==lo{p=1} $0==hi{exit}' | while read -r T; do
  echo "=== $T ==="
  gh release view "$T" -R langgenius/dify --json body -q .body 2>/dev/null \
    | awk '/^## (Environment Variable Changes|Database Migrations|Upgrade Guide)/{p=1} /^## /&&!/^## (Environment Variable Changes|Database Migrations|Upgrade Guide)/{p=0} p'
done
```

Without `gh`, give the links `https://github.com/langgenius/dify/releases/tag/<tag>` instead. Summarise renamed or removed variables, changed defaults, new services, slow or irreversible migrations; the upgrade steps depend on the release.

## Step 3: Plan (dry run)

Print the plan with all eight blocks, then stop and ask "Apply this plan?" unless `--yes` was given.

```text
DIFY UPDATE PLAN   <CUR> -> <TARGET>
TARGET    <DIFY_ROOT> · compose project <PROJECT_NAME> · merge <TARGET_REF> into dev
PRECHECK  tree clean · Compose >= 2.24.0 · Weaviate gate: pass | n/a (<VECTOR_STORE>) · release notes read
CHANGE    git merge <TARGET_REF> · env sync (.env, envs/) · docker compose pull && docker compose up -d
BACKUP    <backup-dir>: docker-compose.yaml, .env, volumes.tgz — the whole stack is down while volumes/ is archived
IMPACT    downtime from down to up · start-up runs DB migrations, which are one-way · <changed env defaults, new services>
VALIDATE  docker compose ps · HTTP check · test retrieval in one knowledge base · model providers list
ROLLBACK  restore <backup-dir> and reset to <PRE_UPDATE_COMMIT> (command below)
APPLY     --yes, or the user's explicit go
```

Print the exact ROLLBACK command with the real values filled in — one runnable line, because git alone cannot undo a database migration:

```bash
cd <DOCKER_DIR> && docker compose down && git -C <DIFY_ROOT> reset --hard <pre-update-sha> && cp -p <backup-dir>/.env .env && sudo mv volumes volumes.failed && mkdir volumes && sudo tar -xzpf <backup-dir>/volumes.tgz -C volumes && docker compose up -d
```

(`<backup-dir>` is the directory Step 4 creates; drop `sudo` when running as root; if the update was stashed, run `git stash pop` afterwards.)

## Step 4: Backup, stack down

Order matters: stop, archive, and only then change anything. The archive is taken from stopped containers, so postgres and Weaviate files are consistent.

```bash
cd "$DOCKER_DIR"
umask 077                                                  # the archive holds the database and the storage key
SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO=sudo
VS=$(grep -E '^VECTOR_STORE=' .env 2>/dev/null | tail -1 | cut -d= -f2); VS=${VS:-weaviate}
BACKUP_DIR="${DIFY_BACKUP_DIR:-$(dirname "$DIFY_ROOT")/dify-backups}/$(date +%Y%m%d-%H%M%S)"   # outside the git repository
mkdir -p "$BACKUP_DIR"
NEED=$($SUDO du -sk volumes | cut -f1); FREE=$(df -Pk "$BACKUP_DIR" | awk 'NR==2{print $4}')
[ "$FREE" -gt "$NEED" ] || { echo "ERROR: not enough free space for the backup (need ${NEED} KB, free ${FREE} KB)"; exit 1; }
cp -p docker-compose.yaml "$BACKUP_DIR/docker-compose.yaml"
[ -f .env ] && cp -p .env "$BACKUP_DIR/.env"               # copied, never printed
APP=$(docker compose config --services | grep -E '^(nginx|api|api_websocket|worker|worker_beat)$' | tr '\n' ' ')
[ -n "$APP" ] && docker compose stop -t 120 $APP
[ "$VS" = weaviate ] && docker compose stop -t -1 weaviate  # no timeout: a hard kill silently breaks vector search
docker compose down -t 120                                  # never add -v
$SUDO tar -czpf "$BACKUP_DIR/volumes.tgz" -C volumes . \
  && $SUDO tar -tzf "$BACKUP_DIR/volumes.tgz" >/dev/null \
  && echo "Backup OK" || { echo "BACKUP FAILED — nothing merged. Bring the stack back with: docker compose up -d"; exit 1; }
ls -l "$BACKUP_DIR"                                         # names and sizes only
```

Never `cat` or print `.env`, the archive listing or the backup directory contents; `volumes/app/storage` can hold the generated `SECRET_KEY`. Keep the backup until the update is verified healthy.

## Step 5: Merge

```bash
cd "$DIFY_ROOT"
git show-ref --verify --quiet refs/heads/dev || git switch -c dev   # official clones are detached HEAD
[ "$(git branch --show-current)" = dev ] || git checkout dev
git merge "$TARGET_REF"
```

If the user chose to stash, run `git stash` right before this block.

**If merge conflicts occur:**

1. List conflicted files: `git diff --name-only --diff-filter=U`
2. Generated or template files — `docker/.env.example`, `docker/docker-compose.yaml`, `docker/docker-compose-template.yaml`, `docker/envs/**/*.env.example`: take upstream (`git checkout --theirs <path> && git add <path>`). `docker-compose.yaml` is generated by `generate_docker_compose` and a release can add services Dify needs — never keep the old file.
3. The user's customizations move out of those files: ports and most settings into `.env` (host ports are `EXPOSE_NGINX_PORT` and `EXPOSE_NGINX_SSL_PORT`), extra volumes or services into `docker/docker-compose.override.yaml` (Compose reads it automatically; upstream git ignores it), template-level changes into `docker-compose-template.yaml` followed by `./generate_docker_compose` in `docker/`.
4. Other files: show the diff, let the user decide.
5. Stage the resolved files by name and commit: `git add <each resolved path> && git commit -m "Merge <TARGET> into dev"`. Never `git add .`.

## Step 6: Sync env

```bash
cd "$DOCKER_DIR"
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example — review security-sensitive values"
elif [ -f dify-env-sync.sh ]; then
  bash dify-env-sync.sh 2>&1 | awk '
    { gsub(/\033\[[0-9;]*m/, "") }
    /^\[[0-9]+\] /{ key=$2; print; next }
    key ~ /SECRET|PASSWORD|PASSWD|TOKEN|KEY|CREDENTIAL|DSN|AUTH/ && /^  [^ ]/ {
      if ($0 ~ /^  \.env/) { sub(/:.*/, ": ***"); print }
      next }
    { print }'
else
  echo "No official script — use the manual algorithm from the env-sync skill"
fi
```

The official `dify-env-sync.sh` backs `.env` up to `env-backup/`, adds the new keys, keeps the user's values and lists differences — and it prints the current value of every differing key, passwords and secrets included. The `awk` filter above masks the value of any key whose name looks secret; never run the script without it. Then check three things:

- `COMPOSE_PROFILES` contains `collaboration`, or the `api_websocket` service never starts
- `EDITION` was renamed `DEPLOYMENT_EDITION` in 1.17.0
- `DIFY_AGENT_RUN_RETENTION_SECONDS` default dropped from 3 days to 2 hours in 1.17.1 (an older `.env` still pins the old value, because `.env` wins)

Optional settings live in `docker/envs/**/*.env.example`; for each existing `envs/**/*.env`, compare with its paired template and only show new keys. Flag security-sensitive new keys (`*SECRET*`, `*PASSWORD*`, `*KEY*`, `*TOKEN*`) and development defaults (`*-for-dev-only`, `difyai123456`). Ask before appending anything.

## Step 7: Pull and start

The compose files have no `build:` sections (couchbase aside), so images are pulled, not built:

```bash
cd "$DOCKER_DIR"
docker compose pull
docker compose up -d
```

Database migrations run automatically at start-up (`MIGRATION_ENABLED=true`); the first start after a release can take minutes.

Targets between 1.15 and 1.17.0, on an install upgraded from before 1.15, also need the one-time `flask data-migrate legacy-model-types` step from their upgrade notes (see the `update-workflow` skill); 1.17.1 and newer do it automatically.

## Step 8: Verify

```bash
cd "$DOCKER_DIR"
sleep 15
docker compose ps
PORT=$(grep -E '^EXPOSE_NGINX_PORT=' .env 2>/dev/null | tail -1 | cut -d= -f2); PORT=${PORT:-80}
curl -s -o /dev/null -w "HTTP %{http_code}" "http://localhost:${PORT}/" && echo " — Dify reachable" || echo " — not reachable yet (may still be starting)"
```

Every service is `Up` or `healthy`; `init_permissions` shows `Exited (0)` and that is normal. Then ask the user to run a test retrieval against a knowledge base (getting chunks back proves the vector index survived — an object count does not) and to confirm the model providers still list their models.

## Step 9: Summary

Print:

- Previous version and commit → target version and commit
- Branch and merge source
- Backup directory and archive size
- New or changed env variables (count and any needing attention)
- Conflicts resolved (if any)
- Docker project name and container status
- The ROLLBACK command from Step 3 with a warning: it restores the volumes from the backup; database migrations are not reversible any other way

If stashed earlier: `git stash pop` and show the result.
