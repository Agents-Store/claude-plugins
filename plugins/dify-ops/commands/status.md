---
description: Show current Dify instance status — git branch, version, container health, .env sync state
allowed-tools: ["Read", "Bash", "Glob", "Grep"]
---

# Dify Status

Show current state of a self-hosted Dify instance without making any changes.

## Process

### Step 1: Detect Working Directory

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
fi
```

### Step 2: Git Status

```bash
cd "$DIFY_ROOT"
echo "=== Git Status ==="
echo "Branch: $(git branch --show-current)"
echo "Commit: $(git rev-parse --short HEAD)"
echo "Date:   $(git log -1 --format=%ci)"

# Check for uncommitted changes
DIRTY=$(git status --porcelain)
[ -z "$DIRTY" ] && echo "Working tree: clean" || echo "Working tree: dirty ($(echo "$DIRTY" | wc -l | tr -d ' ') files)"

# Check how far behind upstream
git fetch origin --quiet 2>/dev/null
BEHIND=$(git rev-list --count HEAD..origin/main 2>/dev/null)
[ "$BEHIND" -gt 0 ] && echo "Behind origin/main: $BEHIND commits" || echo "Up to date with origin/main"

# Latest tag info
LATEST_TAG=$(git tag --sort=-creatordate 2>/dev/null | head -1)
CURRENT_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "none")
echo "Current tag: $CURRENT_TAG"
echo "Latest tag:  $LATEST_TAG"
```

### Step 3: .env Sync Check

```bash
cd "$DOCKER_DIR"
echo ""
echo "=== Environment Status ==="

if [ ! -f ".env" ]; then
  echo ".env: MISSING — run /dify-ops:update to create"
else
  grep -E '^[A-Z_][A-Z0-9_]*=' .env.example | cut -d= -f1 | sort > /tmp/dify-example-keys
  grep -E '^[A-Z_][A-Z0-9_]*=' .env | cut -d= -f1 | sort > /tmp/dify-env-keys
  NEW_COUNT=$(comm -23 /tmp/dify-example-keys /tmp/dify-env-keys | wc -l | tr -d ' ')
  REMOVED_COUNT=$(comm -13 /tmp/dify-example-keys /tmp/dify-env-keys | wc -l | tr -d ' ')

  echo ".env: exists"
  [ "$NEW_COUNT" -gt 0 ] && echo "Missing vars: $NEW_COUNT (run /dify-ops:update to add)" || echo "Missing vars: 0 — in sync"
  [ "$REMOVED_COUNT" -gt 0 ] && echo "Extra vars:   $REMOVED_COUNT (may be deprecated or custom)"

  rm -f /tmp/dify-example-keys /tmp/dify-env-keys
fi
```

### Step 4: Docker Container Status

```bash
echo ""
echo "=== Container Status ==="

CONTAINER=$(docker ps --format '{{.Names}}' 2>/dev/null | grep -E '-(api|web|worker)-' | head -1)
if [ -n "$CONTAINER" ]; then
  PROJECT_NAME=$(echo "$CONTAINER" | sed 's/-\(api\|web\|worker\|nginx\|redis\|db_postgres\|sandbox\|ssrf_proxy\|plugin_daemon\|weaviate\|worker_beat\)-[0-9]*$//')
  echo "Docker project: $PROJECT_NAME"
  cd "$DOCKER_DIR"
  docker compose ps 2>/dev/null || docker ps --filter "name=$PROJECT_NAME" --format "table {{.Names}}\t{{.Status}}"
else
  echo "No running Dify containers detected"
fi
```

### Step 5: Health Check

```bash
NGINX_PORT=$(grep -E '^(EXPOSE_NGINX_PORT|NGINX_PORT)=' "$DOCKER_DIR/.env" 2>/dev/null | tail -1 | cut -d= -f2)
NGINX_PORT=${NGINX_PORT:-80}
echo ""
echo "=== Health ==="
curl -s -o /dev/null -w "Web UI (port $NGINX_PORT): HTTP %{http_code}" "http://localhost:${NGINX_PORT}" 2>/dev/null || echo "Web UI: not reachable"
```
