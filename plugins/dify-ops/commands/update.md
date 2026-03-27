---
description: Update self-hosted Dify — pull upstream, merge into dev, sync .env, rebuild Docker containers
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
argument-hint: "[tag-or-version]"
---

# Dify Update

Update a self-hosted Dify instance: pull upstream changes, merge into local dev branch, sync environment variables, and rebuild Docker containers.

## Arguments

- `$ARGUMENTS` — optional tag/version (e.g., `0.15.0`, `v0.15.0`). If empty, update to latest main.

## Process

### Step 1: Detect Working Directory

Determine whether user is in `dify/` root or `dify/docker/`.

```bash
if [ -f "docker-compose.yaml" ] && [ -f ".env.example" ]; then
  DOCKER_DIR="$(pwd)"
  DIFY_ROOT="$(dirname $(pwd))"
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

### Step 2: Pre-flight Checks

Run from DIFY_ROOT:

```bash
cd "$DIFY_ROOT"
git rev-parse --git-dir 2>/dev/null && echo "Git repo: OK" || { echo "ERROR: Not a git repo"; exit 1; }
echo "Branch: $(git branch --show-current)"
PRE_UPDATE_COMMIT=$(git rev-parse --short HEAD)
echo "Commit: $PRE_UPDATE_COMMIT"
DIRTY=$(git status --porcelain)
if [ -n "$DIRTY" ]; then
  echo "WARNING: Uncommitted changes:"
  git status --short
fi
```

If dirty working tree, ask user:
1. Commit changes first
2. Stash changes (`git stash`)
3. Abort update

If stashing, record `STASHED=true`.

### Step 3: Fetch Upstream

```bash
cd "$DIFY_ROOT"
git fetch origin --tags
echo "Fetched latest from origin"
```

### Step 4: Merge

**If no tag specified (update to latest main):**

```bash
cd "$DIFY_ROOT"
CURRENT=$(git branch --show-current)
[ "$CURRENT" != "dev" ] && git checkout dev
git merge origin/main
```

**If tag specified:**

```bash
cd "$DIFY_ROOT"
TAG="$ARGUMENTS"

# Verify tag exists (try with and without 'v' prefix)
if ! git tag -l "$TAG" | grep -q .; then
  if git tag -l "v$TAG" | grep -q .; then
    TAG="v$TAG"
  else
    echo "ERROR: Tag '$TAG' not found. Recent tags:"
    git tag --sort=-creatordate | head -10
    # STOP — ask user to select a valid tag
  fi
fi

git checkout dev
git merge "$TAG"
```

**If merge conflicts occur:**

1. List conflicted files: `git diff --name-only --diff-filter=U`
2. For `.env.example`: accept theirs (`git checkout --theirs docker/.env.example && git add docker/.env.example`)
3. For `docker-compose.yaml`: show conflicts, help user merge manually (preserve their custom ports/volumes, accept upstream service changes)
4. For other files: show diff, let user decide
5. After resolving: `git add . && git commit -m "Merge upstream into dev"`

### Step 5: Sync .env

```bash
cd "$DOCKER_DIR"

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created .env from .env.example — review security-sensitive values"
else
  # Check for official sync script
  if [ -f "dify-env-sync.sh" ]; then
    echo "Found official dify-env-sync.sh — offer to use it"
  fi

  # Find new variables
  grep -E '^[A-Z_][A-Z0-9_]*=' .env.example | cut -d= -f1 | sort > /tmp/dify-example-keys
  grep -E '^[A-Z_][A-Z0-9_]*=' .env | cut -d= -f1 | sort > /tmp/dify-env-keys
  NEW_KEYS=$(comm -23 /tmp/dify-example-keys /tmp/dify-env-keys)

  if [ -z "$NEW_KEYS" ]; then
    echo "No new environment variables. .env is up to date."
  else
    echo "New variables found — show table with defaults and security flags"
    echo "Ask user to confirm before appending"
    # Append with date header comment
  fi

  rm -f /tmp/dify-example-keys /tmp/dify-env-keys
fi
```

Show new variables as a table. Flag security-sensitive ones (`*SECRET*`, `*PASSWORD*`, `*KEY*`, `*TOKEN*`). Ask for confirmation before appending.

### Step 6: Detect Docker Project Name

```bash
CONTAINER=$(docker ps --format '{{.Names}}' 2>/dev/null | grep -E '-(api|web|worker)-' | head -1)

if [ -n "$CONTAINER" ]; then
  PROJECT_NAME=$(echo "$CONTAINER" | sed 's/-\(api\|web\|worker\|nginx\|redis\|db_postgres\|sandbox\|ssrf_proxy\|plugin_daemon\|weaviate\|worker_beat\)-[0-9]*$//')
  echo "Detected Docker project: $PROJECT_NAME"
else
  echo "No running Dify containers found. Will use default compose behavior."
  PROJECT_NAME=""
fi
```

### Step 7: Rebuild Containers

```bash
cd "$DOCKER_DIR"

if [ -n "$PROJECT_NAME" ] && [ "$PROJECT_NAME" != "docker" ]; then
  echo "Running: docker compose -p $PROJECT_NAME up -d --build"
  docker compose -p "$PROJECT_NAME" up -d --build
else
  echo "Running: docker compose up -d --build"
  docker compose up -d --build
fi
```

### Step 8: Verify

```bash
cd "$DOCKER_DIR"
sleep 15
docker compose ps 2>/dev/null || docker ps --filter "name=${PROJECT_NAME:-docker}"

# Check web reachability
NGINX_PORT=$(grep -E '^(EXPOSE_NGINX_PORT|NGINX_PORT)=' "$DOCKER_DIR/.env" 2>/dev/null | tail -1 | cut -d= -f2)
NGINX_PORT=${NGINX_PORT:-80}
curl -s -o /dev/null -w "HTTP %{http_code}" "http://localhost:${NGINX_PORT}" 2>/dev/null && echo " — Dify reachable" || echo " — Not reachable yet (may still be starting)"
```

### Step 9: Summary

Print update summary:
- Previous commit → current commit
- Branch and merge source
- New env variables added (count + any requiring attention)
- Conflicts resolved (if any)
- Docker project name used
- Container status
- Rollback command with warning about DB migrations

If stashed earlier: `git stash pop` and show result.
