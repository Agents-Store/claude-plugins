---
description: List recent deployments
allowed-tools: mcp__trigger_dev__tds-list_deploys
argument-hint: [environment] [--status <status>] [--period <period>]
---

# List Deploys

Show recent deployments for an environment.

## Arguments
Optional (parsed from "$ARGUMENTS"):
- environment: staging, prod, preview (default: prod)
- --status: DEPLOYED, FAILED, BUILDING, etc.
- --period: Time range (1d, 7d, 30d)

## Process

1. **Parse filters**

2. **List deployments:**
   ```
   tds-list_deploys(
     environment=<env or "prod">,
     status=<status if provided>,
     period=<period if provided>,
     limit=10
   )
   ```

3. **Display results** as table.

## Example Usage
```
/list-deploys
/list-deploys staging
/list-deploys prod --status FAILED --period 7d
```

## Output Format
```
Environment: prod | Showing: 10 deploys

Version      | Status   | Date                 | Duration
-------------|----------|----------------------|---------
20250225.3   | DEPLOYED | 2025-02-25 10:30:00 | 45s
20250224.1   | DEPLOYED | 2025-02-24 15:00:00 | 52s
20250223.2   | FAILED   | 2025-02-23 12:00:00 | 30s
```

## Notes
- Default environment is prod
- Failed deploys include error details
