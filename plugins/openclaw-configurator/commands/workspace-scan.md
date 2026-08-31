---
description: Quick health check of OpenClaw instance — scans all categories (A–J), checks sizes, detects inline secrets, identifies missing components, verifies language
allowed-tools: ["Read", "Bash", "Glob", "Grep"]
argument-hint: "[quick|full|security]"
---

# Workspace Scan

Perform a quick health check of the current OpenClaw instance.

**Path resolution (in priority order):**
1. `$OPENCLAW_INSTANCE_DIR` — runtime workspace dir (holds `openclaw.json`, `workspace/`, `agents/`, etc.). Standard: `~/.openclaw/`, Docker multi-instance: `~/.openclaw-{name}/`.
2. `$OPENCLAW_PROJECT_DIR` — git/docker-compose project dir; used as a fallback only when `OPENCLAW_INSTANCE_DIR` is unset AND it happens to also be the instance root.
3. `$(pwd)` — current directory.

`OPENCLAW_INSTANCE_DIR` and `OPENCLAW_PROJECT_DIR` are distinct concepts and usually live in **different** places (e.g. project `<compose-root>/openclaw-<name>/`, instance `~/.openclaw-<name>/`). Workspace commands like this one always target the **instance** dir.

## Process

### 1. Resolve and verify instance dir
```bash
INSTANCE_DIR="${OPENCLAW_INSTANCE_DIR:-${OPENCLAW_PROJECT_DIR:-$(pwd)}}"
cd "$INSTANCE_DIR" || { echo "ERROR: cannot access $INSTANCE_DIR"; exit 1; }
[ -f ./openclaw.json ] && echo "openclaw.json: OK" || echo "WARNING: not in an OpenClaw instance root ($INSTANCE_DIR)"
[ -d ./workspace ] && echo "workspace/: OK" || echo "WARNING: workspace/ not found"
echo "Instance dir: $INSTANCE_DIR"
```

### 2. Scan auto-injected workspace files (Cat A — 7 core files)

Only these 7 files are auto-injected into the agent's context every session:
```bash
for f in AGENTS.md SOUL.md USER.md IDENTITY.md TOOLS.md HEARTBEAT.md MEMORY.md; do
  if [ -f "./workspace/$f" ]; then
    CHARS=$(wc -c < "./workspace/$f")
    WORDS=$(wc -w < "./workspace/$f")
    MOD=$(stat -f "%Sm" -t "%Y-%m-%d" "./workspace/$f" 2>/dev/null || stat -c "%y" "./workspace/$f" 2>/dev/null | cut -d' ' -f1)
    echo "OK  $f  ${CHARS}c  ${WORDS}w  $MOD"
  else
    echo "MISSING  $f"
  fi
done
```

### 2b. Check special lifecycle files (BOOT.md, BOOTSTRAP.md)

BOOTSTRAP.md IS auto-injected when present (on new workspaces, deleted after bootstrap). BOOT.md is NOT auto-injected — it runs via hook on gateway restart only.
```bash
# BOOT.md — optional persistent startup script (executed via hook, not injected)
if [ -f "./workspace/BOOT.md" ]; then
  echo "OK  BOOT.md  $(wc -c < "./workspace/BOOT.md")c  $(wc -w < "./workspace/BOOT.md")w  (optional startup script)"
else
  echo "—   BOOT.md  not configured (optional)"
fi

# BOOTSTRAP.md — one-time first-run ritual (deleted after completion)
if [ -f "./workspace/BOOTSTRAP.md" ]; then
  echo "WARN  BOOTSTRAP.md  PRESENT — bootstrap has not completed yet"
else
  echo "OK  BOOTSTRAP.md  absent (bootstrap completed)"
fi
```

### 2c. Detect extra files in workspace/ root

Agents can create arbitrary files in workspace/ during sessions. These are NOT auto-injected and don't count toward character limits:
```bash
for f in ./workspace/*.md; do
  [ -f "$f" ] || continue
  BASENAME=$(basename "$f")
  case "$BASENAME" in
    AGENTS.md|SOUL.md|USER.md|IDENTITY.md|TOOLS.md|HEARTBEAT.md|MEMORY.md|BOOT.md|BOOTSTRAP.md) continue ;;
    *) echo "EXTRA: $BASENAME ($(wc -c < "$f") chars) — not auto-injected, not counted toward limits" ;;
  esac
done
```
If extra files are found, note: "These files were created by the agent during sessions. They don't consume context tokens. If they contain reference material the agent needs, consider moving them to `workspace/docs/` and adding a reference in AGENTS.md."

### 3. Check character limits (auto-injected files only)

Limits apply to the 7 auto-injected files plus BOOTSTRAP.md while present. BOOT.md and agent-created files are NOT counted:
- Per-file limit: 20,000 chars (default). Flag files exceeding this.
- Total limit: 150,000 chars across all auto-injected files.
```bash
TOTAL=0
for f in AGENTS.md SOUL.md USER.md IDENTITY.md TOOLS.md HEARTBEAT.md MEMORY.md; do
  if [ -f "./workspace/$f" ]; then
    CHARS=$(wc -c < "./workspace/$f")
    TOTAL=$((TOTAL + CHARS))
    [ "$CHARS" -gt 15000 ] && echo "WARNING: $f is ${CHARS}c — approaching 20K truncation limit. Consider moving infrequently-used sections to docs/"
    [ "$CHARS" -gt 20000 ] && echo "CRITICAL: $f is ${CHARS}c — EXCEEDS 20K limit, content will be truncated!"
  fi
done
echo "Auto-injected total: $TOTAL chars (limit: 150,000)"
```

If any auto-injected file is near the limit, recommend: "Use the 50% rule — if content is needed in less than 50% of sessions, move it to `workspace/docs/` and reference from AGENTS.md. See subfolder-patterns for templates."

### 4. Check openclaw.json (Cat E)
```bash
if [ -f ./openclaw.json ]; then
  echo "openclaw.json: $(wc -c < ./openclaw.json) bytes"
else
  echo "openclaw.json: NOT FOUND"
fi
```

### 5. Secret detection in openclaw.json
```bash
# Check for potential inline secrets
grep -n -E '"[A-Za-z0-9_:.-]{20,}"' ./openclaw.json 2>/dev/null | grep -vi '"source"\|"provider"\|"id"\|"model"\|"profile"\|"mode"\|"workspace"\|"description"\|"name"'
```

If matches found, warn user:
- Inline secrets are a security risk
- Recommend SecretRef pattern: `{ "source": "env", "provider": "default", "id": "ENV_VAR_NAME" }`
- `openclaw doctor` SecretRef resolution errors outside gateway runtime are safe to ignore

### 6. Check workspace subfolders (Cat B, C, D, J)
```bash
echo "--- Memory Logs (Cat B) ---"
ls ./workspace/memory/ 2>/dev/null | wc -l

echo "--- Instance Skills (Cat C) ---"
find ./workspace/skills/ -name "SKILL.md" -type f 2>/dev/null | wc -l

echo "--- Docs (Cat D) ---"
find ./workspace/docs/ -name "*.md" -type f 2>/dev/null | wc -l

echo "--- Workflows (Cat D) ---"
find ./workspace/workflows/ -name "*.prose" -type f 2>/dev/null | wc -l

echo "--- Canvas (Cat J) ---"
ls ./workspace/canvas/ 2>/dev/null | wc -l

echo "--- Standing Orders ---"
ls ./workspace/docs/standing-orders/ 2>/dev/null | wc -l
```

### 7. Check sessions (Cat F)
```bash
echo "--- Sessions ---"
ls ./agents/main/sessions/*.jsonl 2>/dev/null | wc -l
[ -f ./agents/main/sessions/sessions.json ] && echo "sessions.json: $(jq length ./agents/main/sessions/sessions.json 2>/dev/null) entries" || echo "sessions.json: MISSING"
```

### 8. Check memory index (Cat G)
```bash
[ -f ./memory/main.sqlite ] && echo "memory index: $(ls -lh ./memory/main.sqlite | awk '{print $5}')" || echo "memory index: NOT FOUND"
```

### 9. Check cron jobs (Cat H)
```bash
if [ -f ./cron/jobs.json ]; then
  echo "cron/jobs.json: $(wc -c < ./cron/jobs.json) bytes"
else
  ls ./cron/ 2>/dev/null || echo "cron/: NOT FOUND"
fi
```

### 10. Check logs (Cat I)
```bash
if [ -f ./logs/openclaw.log ]; then
  echo "openclaw.log: $(wc -l < ./logs/openclaw.log) lines"
  echo "Recent errors: $(grep -ci 'error\|fatal' ./logs/openclaw.log 2>/dev/null)"
else
  echo "openclaw.log: NOT FOUND"
fi
```

### 11. Check shared skills & plugins
```bash
echo "--- Managed Skills (standard path) ---"
find ~/.openclaw/skills/ -name "SKILL.md" -type f 2>/dev/null | wc -l

echo "--- Shared Public Skills (Docker path) ---"
find /root/openclaw-skills/ -name "SKILL.md" -type f 2>/dev/null | wc -l

echo "--- Shared Private Skills (Docker path) ---"
find /root/openclaw-private-skills/ -name "SKILL.md" -type f 2>/dev/null | wc -l

echo "--- Shared Public Plugins (Docker path) ---"
ls /root/openclaw-plugins/packages/ 2>/dev/null | wc -l

echo "--- Shared Private Plugins (Docker path) ---"
ls /root/openclaw-plugins-private/packages/ 2>/dev/null | wc -l
```

### 12. Bootstrap status
Already checked in step 2b. If BOOTSTRAP.md is present, remind the user that bootstrap hasn't completed — the agent should run it or the file should be deleted.

### 13. Quick security flags
- Does AGENTS.md have a "Red Lines" section?
- Does SOUL.md have a "Boundaries" section?
- Is dmPolicy set to "allowlist" (not "open")?

### 14. Output summary table

```
Auto-injected files (7 core — counted toward context limits):
| File          | Status  | Size    | Words | Last Modified | Issues        |
|---------------|---------|---------|-------|---------------|---------------|
| AGENTS.md     | OK      | 3,200c  | 450w  | 2025-03-15    |               |
| SOUL.md       | OK      | 1,800c  | 280w  | 2025-03-10    |               |
| USER.md       | MISSING | -       | -     | -             | Create this!  |
| ...           | ...     | ...     | ...   | ...           | ...           |

Special lifecycle files (NOT auto-injected):
| File           | Status                          |
|----------------|---------------------------------|
| BOOT.md        | Not configured (optional)       |
| BOOTSTRAP.md   | Absent — bootstrap completed OK |

Extra workspace files (NOT auto-injected, not counted toward limits):
| File                             | Size     | Recommendation                    |
|----------------------------------|----------|-----------------------------------|
| research-agent-marketplaces.md   | 231,000c | Move to docs/ or delete           |

Instance: [CWD]
Core files: X/7 present, Y chars total (limit: 150,000)
BOOT.md: [configured/not configured] | BOOTSTRAP.md: [completed/WARNING: present]
Extra workspace files: N (not auto-injected)
Docs: N files | Skills: N | Memory: N daily logs | Workflows: N
Sessions: N JSONL | Cron: [configured/none] | Log errors: N
Memory index: [present/absent] | Canvas: [N files/none]
Shared: N public skills, N private skills, N public plugins, N private plugins
Security: [OK / WARNINGS (details)]
```

### 15. Quick recommendations
List top 3 immediate actions based on scan results.
