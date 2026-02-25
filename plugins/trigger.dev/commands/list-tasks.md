---
description: List all tasks deployed in an environment
allowed-tools: mcp__trigger_dev__tds-get_current_worker
argument-hint: [environment]
---

# List Tasks

Show all tasks deployed to an environment with their payload schemas.

## Arguments
- environment: dev, staging, prod, or preview (default: dev)

## Process

1. **Get current worker:**
   ```
   tds-get_current_worker(environment="$ARGUMENTS" or "dev")
   ```

2. **Display results:**
   Show table with:
   - Task ID/slug
   - Payload schema summary
   - Machine preset
   - Queue configuration (if any)
   - Worker version

## Example Usage
```
/list-tasks
/list-tasks prod
/list-tasks staging
```

## Output Format
```
Environment: prod | Version: 20250225.3

Task ID            | Machine   | Queue
-------------------|-----------|------------------
hello-world        | micro     | -
process-order      | small-1x  | order-processing (concurrency: 10)
send-email         | micro     | email-queue (concurrency: 5)
daily-report       | small-2x  | - (scheduled: 0 9 * * *)
```

## Notes
- Default environment is dev
- Shows deployed tasks only (must deploy first)
- Payload schemas help you construct correct payloads for /trigger-task
