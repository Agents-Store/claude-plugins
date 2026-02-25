---
description: Cancel a running or queued task run
allowed-tools: mcp__trigger_dev__tds-cancel_run, mcp__trigger_dev__tds-get_run_details
argument-hint: <run-id>
---

# Cancel Run

Cancel a task run that is currently executing or queued.

## Arguments
- run-id: The run ID to cancel (starts with run_)

## Process

1. **Check current status:**
   ```
   tds-get_run_details(runId="$ARGUMENTS")
   ```
   If already completed/failed/cancelled, inform user.

2. **Cancel the run:**
   ```
   tds-cancel_run(runId="$ARGUMENTS")
   ```

3. **Confirm cancellation:**
   - Show run ID and new status
   - Show task identifier

## Example Usage
```
/cancel-run run_abc123
```

## Notes
- Only works on QUEUED, EXECUTING, WAITING, DELAYED runs
- Cannot cancel already completed or failed runs
- Cancelled runs cannot be resumed
