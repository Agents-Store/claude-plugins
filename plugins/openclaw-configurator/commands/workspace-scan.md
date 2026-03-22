---
description: Quick health check of OpenClaw instance — scans all standard files, sessions, cron, logs, shared skills/plugins, checks sizes, identifies missing components
allowed-tools: ["Read", "Bash", "Glob", "Grep"]
argument-hint: ""
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

### 2. Scan workspace files (target 1)
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
cat ./workspace/*.md 2>/dev/null | wc -c
```

### 4. Check openclaw.json (target 5)
```bash
if [ -f ./openclaw.json ]; then
  echo "openclaw.json: $(wc -c < ./openclaw.json) bytes"
else
  echo "openclaw.json: NOT FOUND"
fi
```

### 5. Check workspace subfolders (targets 2, 3, 6)
```bash
echo "--- Docs (target 2) ---"
find ./workspace/docs/ -name "*.md" -type f 2>/dev/null | wc -l

echo "--- Instance Skills (target 3) ---"
find ./workspace/skills/ -name "SKILL.md" -type f 2>/dev/null | wc -l

echo "--- Memory Logs (target 6) ---"
ls ./workspace/memory/ 2>/dev/null | wc -l

echo "--- Standing Orders ---"
ls ./workspace/docs/standing-orders/ 2>/dev/null | wc -l
```

### 6. Check sessions (target 4)
```bash
echo "--- Sessions ---"
ls ./agents/main/sessions/*.jsonl 2>/dev/null | wc -l
[ -f ./agents/main/sessions/sessions.json ] && echo "sessions.json: $(jq length ./agents/main/sessions/sessions.json 2>/dev/null) entries" || echo "sessions.json: MISSING"
```

### 7. Check cron jobs (target 7)
```bash
echo "--- Cron Jobs ---"
ls ./cron/ 2>/dev/null || echo "cron/: NOT FOUND"
```

### 8. Check logs (target 8)
```bash
echo "--- Logs ---"
if [ -f ./logs/openclaw.log ]; then
  echo "openclaw.log: $(wc -l < ./logs/openclaw.log) lines"
  echo "Recent errors: $(grep -ci 'error\|fatal' ./logs/openclaw.log 2>/dev/null)"
else
  echo "openclaw.log: NOT FOUND"
fi
```

### 9. Check shared skills & plugins (targets 9-11)
```bash
echo "--- Shared Public Skills (target 9) ---"
find /root/openclaw-skills/ -name "SKILL.md" -type f 2>/dev/null | wc -l

echo "--- Shared Private Skills (target 10) ---"
find /root/openclaw-private-skills/ -name "SKILL.md" -type f 2>/dev/null | wc -l

echo "--- Shared Public Plugins (target 11a) ---"
ls /root/openclaw-plugins/packages/ 2>/dev/null | wc -l

echo "--- Shared Private Plugins (target 11b) ---"
ls /root/openclaw-plugins-private/packages/ 2>/dev/null | wc -l
```

### 10. Check for BOOTSTRAP.md
If BOOTSTRAP.md exists, flag it — it means bootstrap never completed.

### 11. Output summary table

```
| File          | Status  | Size    | Words | Last Modified | Issues        |
|---------------|---------|---------|-------|---------------|---------------|
| AGENTS.md     | OK      | 3,200c  | 450w  | 2025-03-15    |               |
| SOUL.md       | OK      | 1,800c  | 280w  | 2025-03-10    |               |
| USER.md       | MISSING | -       | -     | -             | Create this!  |
| ...           | ...     | ...     | ...   | ...           | ...           |

Instance: [CWD]
Total: X/9 files present, Y chars total (limit: 150,000)
Docs: N files | Skills: N | Memory: N daily logs
Sessions: N JSONL | Cron: N jobs | Log errors: N
Shared: N public skills, N private skills, N public plugins, N private plugins
```

### 12. Quick recommendations
List top 3 immediate actions based on scan results.
