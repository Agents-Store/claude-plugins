---
description: Get detailed status and trace of a specific run
allowed-tools: mcp__trigger_dev__tds-get_run_details
argument-hint: <run-id>
---

# Run Status

Get the full details, trace, and logs for a specific run.

## Arguments
- run-id: The run ID (starts with run_)

## Process

1. **Get run details:**
   ```
   tds-get_run_details(
     runId="$ARGUMENTS",
     maxTraceLines=500
   )
   ```

2. **Display results:**
   - Run ID and status
   - Task identifier
   - Start time and duration
   - Execution trace with timestamps
   - Output (if completed)
   - Error details (if failed)

## Example Usage
```
/run-status run_abc123
```

## Output Format
```
Run: run_abc123
Task: process-order
Status: COMPLETED
Started: 2025-02-25T10:30:00Z
Duration: 2.3s
Environment: prod

Trace:
  10:30:00.000 | Starting order processing
  10:30:00.500 | Fetching order ORD-123
  10:30:01.200 | Processing 3 items
  10:30:02.300 | Order completed

Output: {"processed": true, "items": 3}
```

## Notes
- Run ID must start with run_
- Use maxTraceLines to control trace length
- Failed runs include error details and stack traces
