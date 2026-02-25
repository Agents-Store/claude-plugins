---
name: task-execution
description: Triggering tasks, monitoring runs, debugging failures, and managing run lifecycle. Use when triggering tasks or inspecting runs.
---

# Task Execution

This skill covers triggering tasks, monitoring runs, and debugging.

## Available Tools

| Tool | Description |
|------|-------------|
| `tds-get_current_worker` | List available tasks and their payload schemas |
| `tds-trigger_task` | Trigger a task with payload and options |
| `tds-list_runs` | List and filter runs |
| `tds-get_run_details` | Get run trace, logs, and output |
| `tds-wait_for_run_to_complete` | Wait for a run to finish |
| `tds-cancel_run` | Cancel a running/queued run |

## Triggering Tasks

### Step 1: Find Available Tasks
```
Tool: tds-get_current_worker
Input: {"environment": "dev"}

Returns task list with IDs and payload schemas.
```

### Step 2: Trigger a Task
```
Tool: tds-trigger_task
Input: {
  "taskId": "hello-world",
  "payload": {"name": "Claude"},
  "environment": "dev"
}

Returns run ID (run_xxx).
```

### With Full Options
```
Tool: tds-trigger_task
Input: {
  "taskId": "process-order",
  "payload": {"orderId": "ORD-123", "items": ["item-1"]},
  "environment": "prod",
  "options": {
    "tags": ["priority", "vip-customer"],
    "machine": "medium-1x",
    "maxAttempts": 5,
    "maxDuration": 300,
    "delay": "5m",
    "ttl": "30m",
    "idempotencyKey": "order-ORD-123",
    "queue": {"name": "high-priority"}
  }
}
```

### Trigger Options Reference

| Option | Type | Description |
|--------|------|-------------|
| `delay` | string/datetime | Delay before execution ("5m", "2h", ISO datetime) |
| `tags` | string[] | Up to 5 tags, each < 128 chars |
| `machine` | enum | Machine preset (micro to large-2x) |
| `maxAttempts` | integer | Max retry attempts |
| `maxDuration` | number | Max run duration in seconds |
| `ttl` | string/integer | Time-to-live before auto-cancel (default "10m") |
| `idempotencyKey` | string | Prevent duplicate runs |
| `queue` | object | Override queue name |

## Monitoring Runs

### List Recent Runs
```
Tool: tds-list_runs
Input: {
  "environment": "prod",
  "limit": 20
}
```

### Filter Runs by Status
```
Tool: tds-list_runs
Input: {
  "environment": "prod",
  "status": "FAILED",
  "period": "7d"
}
```

### Filter by Task
```
Tool: tds-list_runs
Input: {
  "taskIdentifier": "process-order",
  "environment": "prod",
  "period": "1d"
}
```

### Filter by Tag
```
Tool: tds-list_runs
Input: {
  "tag": "vip-customer",
  "environment": "prod"
}
```

### Run Status Values

| Status | Description |
|--------|-------------|
| PENDING_VERSION | Waiting for deployment |
| QUEUED | In queue, waiting to execute |
| DEQUEUED | Picked up, about to execute |
| EXECUTING | Currently running |
| WAITING | Paused (wait.for, triggerAndWait) |
| COMPLETED | Finished successfully |
| CANCELED | Manually cancelled |
| FAILED | Task threw an error |
| CRASHED | Unexpected crash |
| SYSTEM_FAILURE | Infrastructure issue |
| DELAYED | Waiting for delay to expire |
| EXPIRED | TTL expired before execution |
| TIMED_OUT | Exceeded maxDuration |

### Run Filters Reference

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | enum | Filter by status |
| `taskIdentifier` | string | Filter by task ID |
| `tag` | string | Filter by tag |
| `version` | string | Filter by version (e.g. "20250808.3") |
| `machine` | enum | Filter by machine preset |
| `period` | string | Time range ("1d", "7d", "30d") |
| `from` / `to` | ISO datetime | Custom time range |
| `limit` | integer | Results per page (max 100) |
| `cursor` | string | Pagination cursor (run_xxx) |

## Debugging Runs

### Get Run Details with Trace
```
Tool: tds-get_run_details
Input: {
  "runId": "run_abc123",
  "environment": "prod",
  "maxTraceLines": 500
}

Returns:
- Run status and metadata
- Full execution trace with timing
- Console logs and output
- Error details if failed
```

### Wait for Completion
```
Tool: tds-wait_for_run_to_complete
Input: {
  "runId": "run_abc123",
  "timeoutInSeconds": 120
}

Returns current state when completed or when timeout expires.
```

### Cancel a Run
```
Tool: tds-cancel_run
Input: {
  "runId": "run_abc123",
  "environment": "prod"
}
```

## Common Workflows

### Trigger and Monitor
```
1. tds-get_current_worker() -> Find task and payload schema
2. tds-trigger_task(taskId, payload) -> Get run_xxx ID
3. tds-wait_for_run_to_complete(runId, timeoutInSeconds=120)
   OR
   tds-get_run_details(runId) -> Check status and logs
```

### Debug Failed Runs
```
1. tds-list_runs(status="FAILED", period="1d")
2. For each failed run:
   tds-get_run_details(runId) -> Read error trace
3. Identify pattern (common error, specific task, etc.)
```

### Retry Pattern (Manual)
```
1. tds-get_run_details(runId) -> Get original payload
2. tds-trigger_task(taskId, payload) -> Re-trigger with same payload
3. tds-wait_for_run_to_complete(newRunId)
```

## Best Practices

1. **Always check task schema first** with tds-get_current_worker before triggering
2. **Use idempotencyKey** for operations that should not duplicate
3. **Set appropriate TTL** - don't let stale runs execute
4. **Use tags** for filtering and organizing runs
5. **Monitor FAILED runs** regularly
6. **Use maxDuration** to prevent runaway tasks
