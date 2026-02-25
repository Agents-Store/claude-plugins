---
description: List all preview branches with deployments
allowed-tools: mcp__trigger_dev__tds-list_preview_branches
---

# Preview Branches

List all branches that have preview deployments.

## Arguments
None

## Process

1. **List preview branches:**
   ```
   tds-list_preview_branches()
   ```

2. **Display results:**
   - Branch name
   - Deployment status
   - Last deployed date

## Example Usage
```
/preview-branches
```

## Output Format
```
Preview Branches
================

Branch                    | Status   | Last Deploy
--------------------------|----------|---------------------
feature/new-task          | DEPLOYED | 2025-02-25 10:30:00
feature/ai-summarizer     | DEPLOYED | 2025-02-24 15:00:00
fix/payment-retry         | FAILED   | 2025-02-23 12:00:00
```

## Notes
- Use /deploy preview --branch <name> to deploy a new preview
- Preview branches allow isolated testing of features
- Each branch gets its own environment
