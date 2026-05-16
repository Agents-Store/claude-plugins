---
description: Update OpenClaw instance from official GitHub repo — fetch latest tag, merge into dev preserving local changes, rebuild Docker containers
allowed-tools: ["Read", "Bash", "Glob", "Grep"]
argument-hint: "[tag-or-version]"
---

# Instance Update

Update an OpenClaw instance from the official GitHub repository. Fetches the latest release tag (or a specified tag), merges it into the local `dev` branch preserving local customizations, and rebuilds Docker containers.

## Arguments

- `$ARGUMENTS` — optional tag/version (e.g., `v1.5.0`, `1.5.0`). If empty, update to the latest tag.

## Process

### Step 1: Verify Working Directory

The command targets `$OPENCLAW_PROJECT_DIR` when set, otherwise the current directory (e.g., `/docker/openclaw-pitline/`). The target must be a git repo cloned from the official OpenClaw repo and contain `docker-compose.yaml`.

```bash
PROJECT_DIR="${OPENCLAW_PROJECT_DIR:-$(pwd)}"
cd "$PROJECT_DIR" || { echo "ERROR: cannot access $PROJECT_DIR"; exit 1; }

if [ ! -d ".git" ]; then
  echo "ERROR: Not a git repository. Run this from (or set OPENCLAW_PROJECT_DIR to) the OpenClaw project root (e.g., /docker/openclaw-pitline/)"
  exit 1
fi

if [ ! -f "docker-compose.yaml" ] && [ ! -f "docker-compose.yml" ]; then
  echo "ERROR: No docker-compose.yaml found in $PROJECT_DIR. Expected to be in the OpenClaw project root."
  exit 1
fi

COMPOSE_FILE=$([ -f "docker-compose.yaml" ] && echo "docker-compose.yaml" || echo "docker-compose.yml")
INSTANCE_NAME=$(basename "$PROJECT_DIR")
echo "Instance: $INSTANCE_NAME"
echo "Directory: $PROJECT_DIR"
echo "Compose file: $COMPOSE_FILE"
```

### Step 2: Pre-flight Checks

```bash
# Current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "Branch: $CURRENT_BRANCH"

# Verify origin
ORIGIN_URL=$(git remote get-url origin 2>/dev/null)
echo "Origin: $ORIGIN_URL"

# Current position
PRE_UPDATE_COMMIT=$(git rev-parse --short HEAD)
PRE_UPDATE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "none")
echo "Current commit: $PRE_UPDATE_COMMIT"
echo "Current tag: $PRE_UPDATE_TAG"

# Uncommitted changes
git status --short
```

**Branch check**: If `CURRENT_BRANCH` is not `dev`, warn the user. Ask whether to switch to `dev` or abort. The `dev` branch is the local customization branch — all merges happen here.

**Origin check**: If `ORIGIN_URL` does not contain `openclaw/openclaw`, warn the user. Ask whether to continue or abort.

**Dirty working tree**: If `git status --short` shows changes, ask user:
1. **Commit changes first** — `git add -A && git commit -m "WIP: local changes before update to $TARGET_TAG"`
2. **Stash changes** — `git stash push -m "pre-update stash $(date +%Y-%m-%d-%H%M)"`
3. **Abort update**

If stashing, remember to restore in Step 11.

### Step 3: Backup docker-compose

```bash
cp "$COMPOSE_FILE" "${COMPOSE_FILE}.pre-update.bak"
echo "Backed up $COMPOSE_FILE → ${COMPOSE_FILE}.pre-update.bak"

# Also backup .env if present
[ -f ".env" ] && cp .env .env.pre-update.bak && echo "Backed up .env → .env.pre-update.bak"
```

### Step 4: Fetch Upstream

```bash
git fetch origin --tags
echo "Fetched latest from origin (including all tags)"
```

### Step 5: Determine Target Tag

**If `$ARGUMENTS` is empty (update to latest):**

```bash
LATEST_TAG=$(git tag --sort=-version:refname | head -1)
if [ -z "$LATEST_TAG" ]; then
  echo "ERROR: No tags found after fetch. Verify origin is correct."
  exit 1
fi
echo "Latest available tag: $LATEST_TAG"
```

If `PRE_UPDATE_TAG` equals `LATEST_TAG`:
```
Already on the latest tag ($LATEST_TAG). No update needed.
Recent tags:
$(git tag --sort=-version:refname | head -5)
```
Stop here — clean up backup files and exit.

**If `$ARGUMENTS` is provided:**

```bash
TAG="$ARGUMENTS"

# Try exact match, then with 'v' prefix
if ! git tag -l "$TAG" | grep -q .; then
  if git tag -l "v$TAG" | grep -q .; then
    TAG="v$TAG"
    echo "Found tag: $TAG (added v prefix)"
  else
    echo "ERROR: Tag '$TAG' not found after fetching."
    echo "Available recent tags:"
    git tag --sort=-version:refname | head -10
  fi
fi
```

If tag not found, stop and ask user to select a valid tag.

### Step 6: Show Update Plan and Confirm

```bash
TARGET_TAG="${TAG:-$LATEST_TAG}"

echo ""
echo "=== Update Plan ==="
echo "Instance:  $INSTANCE_NAME"
echo "Current:   $PRE_UPDATE_TAG ($PRE_UPDATE_COMMIT)"
echo "Target:    $TARGET_TAG"
echo ""
echo "Commits to merge:"
git log --oneline "$PRE_UPDATE_COMMIT..$TARGET_TAG" 2>/dev/null | head -20
COMMIT_COUNT=$(git rev-list --count "$PRE_UPDATE_COMMIT..$TARGET_TAG" 2>/dev/null || echo "?")
echo ""
echo "Total: $COMMIT_COUNT commits"
echo "Changelog: https://github.com/openclaw/openclaw/releases"
```

Ask user to confirm before proceeding with the merge.

### Step 7: Merge Tag into dev

```bash
git checkout dev
git merge "$TARGET_TAG" -m "Merge $TARGET_TAG into dev"
```

**If merge succeeds cleanly** — proceed to Step 8.

**If merge conflicts occur:**

```bash
echo "Merge conflicts detected:"
git diff --name-only --diff-filter=U
```

Resolution strategy — **preserve local customizations**:

| File pattern | Strategy | Reason |
|---|---|---|
| `docker-compose.yaml` / `docker-compose.yml` | **Manual merge** — show conflicts to user, preserve local ports/volumes/services, accept upstream additions | User's custom configuration lives here |
| `.env` / `.env.example` | Accept theirs, then restore custom values | Template should match upstream |
| Source code / other files | Accept theirs | We want upstream code changes |

For **docker-compose conflicts**:
1. Show the conflicted sections to the user
2. User's customizations (ports, volumes, environment overrides, added services) must be **kept**
3. Upstream changes (new services, updated image tags, new env vars) should be **accepted**
4. Help merge manually, then `git add $COMPOSE_FILE`

For **non-docker-compose conflicts**:
```bash
CONFLICTS=$(git diff --name-only --diff-filter=U)
for f in $CONFLICTS; do
  case "$f" in
    docker-compose.yaml|docker-compose.yml|.env)
      echo "MANUAL: $f — needs user review"
      ;;
    *)
      git checkout --theirs "$f"
      git add "$f"
      echo "AUTO: $f — accepted upstream version"
      ;;
  esac
done
```

After all conflicts resolved:
```bash
git commit -m "Merge $TARGET_TAG into dev — conflicts resolved"
```

**CRITICAL**: Never push the `dev` branch. This is the user's local-only customization branch.

### Step 8: Validate docker-compose

```bash
docker compose config --quiet 2>&1 && echo "docker-compose: valid syntax" || echo "WARNING: docker-compose has syntax errors — review before rebuilding"
```

If syntax errors detected, show the error and ask user to fix before proceeding. The backup is available at `${COMPOSE_FILE}.pre-update.bak`.

### Step 9: Rebuild Containers

Ask for confirmation before rebuilding.

```bash
echo "Rebuilding containers..."
docker compose up -d --build
```

If build fails:
1. Show the error output
2. Offer options:
   - Fix the issue and retry
   - **Rollback**: `git merge --abort` (if merge not committed) or `git reset --hard $PRE_UPDATE_COMMIT` then `docker compose up -d --build`

### Step 10: Verify Containers

```bash
sleep 10
echo "=== Container Status ==="
docker compose ps
```

If not all containers are running:
1. Show failed services: `docker compose ps | grep -v "running\|Up"`
2. Show logs: `docker compose logs --tail=50 <failed_service>`
3. Offer to retry or roll back

### Step 11: Restore Stashed Changes

If changes were stashed in Step 2:

```bash
git stash pop
echo "Restored stashed changes"
```

If stash pop has conflicts, show them and help resolve.

### Step 12: Summary

```
=== OpenClaw Instance Update Complete ===

Instance:         $INSTANCE_NAME ($PROJECT_DIR)
Previous version: $PRE_UPDATE_TAG ($PRE_UPDATE_COMMIT)
Updated to:       $TARGET_TAG ($(git rev-parse --short HEAD))
Branch:           dev (local only — NOT pushed)
Conflicts:        [None / N resolved]
Backups:          ${COMPOSE_FILE}.pre-update.bak
Containers:       [docker compose ps summary]

Rollback:  git reset --hard $PRE_UPDATE_COMMIT && docker compose up -d --build
Backup:    cp ${COMPOSE_FILE}.pre-update.bak $COMPOSE_FILE
Releases:  https://github.com/openclaw/openclaw/releases
```

Ask user if they want to keep or remove backup files:
```bash
rm -f "${COMPOSE_FILE}.pre-update.bak" .env.pre-update.bak
echo "Backup files removed"
```
