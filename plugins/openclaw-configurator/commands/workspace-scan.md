---
description: Quick health check of OpenClaw instance — scans all categories (A–J), checks sizes, detects inline secrets, identifies missing components, verifies language
allowed-tools: ["Read", "Bash", "Glob", "Grep"]
argument-hint: "[quick|full|security]"
---

# Workspace Scan

Perform a quick health check of the current OpenClaw instance. CWD is the instance root (`~/.openclaw-{name}/`).

## Process

### 1. Verify CWD
```bash
[ -f ./openclaw.json ] && echo "openclaw.json: OK" || echo "WARNING: not in an OpenClaw instance root"
[ -d ./workspace ] && echo "workspace/: OK" || echo "WARNING: workspace/ not found"
pwd
```

### 2. Scan workspace files (Cat A)
```bash
for f in AGENTS.md SOUL.md USER.md IDENTITY.md TOOLS.md HEARTBEAT.md MEMORY.md BOOT.md BOOTSTRAP.md; do
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

### 3. Check character limits
- Per-file limit: 20,000 chars (default). Flag files exceeding this.
- Total limit: 150,000 chars. Sum all file sizes and check.
```bash
echo "TOTAL: $(cat ./workspace/*.md 2>/dev/null | wc -c) chars (limit: 150,000)"
```

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
echo "--- Shared Public Skills ---"
find /root/openclaw-skills/ -name "SKILL.md" -type f 2>/dev/null | wc -l

echo "--- Shared Private Skills ---"
find /root/openclaw-private-skills/ -name "SKILL.md" -type f 2>/dev/null | wc -l

echo "--- Shared Public Plugins ---"
ls /root/openclaw-plugins/packages/ 2>/dev/null | wc -l

echo "--- Shared Private Plugins ---"
ls /root/openclaw-plugins-private/packages/ 2>/dev/null | wc -l
```

### 12. Check for BOOTSTRAP.md
If BOOTSTRAP.md exists, flag it — it means bootstrap never completed.

### 13. Quick security flags
- Does AGENTS.md have a "Red Lines" section?
- Does SOUL.md have a "Boundaries" section?
- Is dmPolicy set to "allowlist" (not "open")?

### 14. Output summary table

```
| File          | Status  | Size    | Words | Last Modified | Issues        |
|---------------|---------|---------|-------|---------------|---------------|
| AGENTS.md     | OK      | 3,200c  | 450w  | 2025-03-15    |               |
| SOUL.md       | OK      | 1,800c  | 280w  | 2025-03-10    |               |
| USER.md       | MISSING | -       | -     | -             | Create this!  |
| ...           | ...     | ...     | ...   | ...           | ...           |

Instance: [CWD]
Total: X/9 files present, Y chars total (limit: 150,000)
Docs: N files | Skills: N | Memory: N daily logs | Workflows: N
Sessions: N JSONL | Cron: [configured/none] | Log errors: N
Memory index: [present/absent] | Canvas: [N files/none]
Shared: N public skills, N private skills, N public plugins, N private plugins
Security: [OK / WARNINGS (details)]
```

### 15. Quick recommendations
List top 3 immediate actions based on scan results.
