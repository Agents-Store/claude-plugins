---
description: List recent runs with optional filters
allowed-tools: mcp__trigger_dev__tds-list_runs
argument-hint: [status] [--task <task-id>] [--period <period>] [--env <environment>]
---

# List Runs

List recent task runs with optional filters.

## Arguments
Optional filters (parsed from "$ARGUMENTS"):
- status: COMPLETED, FAILED, EXECUTING, QUEUED, etc.
- --task: Filter by task identifier
- --period: Time range (1d, 7d, 30d)
- --tag: Filter by tag
- --env: Environment (default: dev)

## Process

1. **Parse filters from arguments**

2. **List runs:**
   ```
   tds-list_runs(
     environment=<env or "dev">,
     status=<status if provided>,
     taskIdentifier=<task if provided>,
     tag=<tag if provided>,
     period=<period or "1d">,
     limit=20
   )
   ```

3. **Display results:**
   Show table with run ID, task, status, started at, duration.

## Example Usage
```
/list-runs
/list-runs FAILED
/list-runs FAILED --task process-order --period 7d
/list-runs --env prod --period 1d
/list-runs --tag vip-customer
```

## Output Format
```
Environment: prod | Period: 1d | Showing: 20 runs

Run ID         | Task            | Status    | Started              | Duration
---------------|-----------------|-----------|----------------------|---------
run_abc123     | process-order   | COMPLETED | 2025-02-25 10:30:00 | 2.3s
run_def456     | send-email      | FAILED    | 2025-02-25 10:28:00 | 0.5s
run_ghi789     | hello-world     | COMPLETED | 2025-02-25 10:25:00 | 0.1s
```

## Notes
- Default period is 1d, default environment is dev
- Maximum 100 runs per page
- Use run IDs with /run-status for details
