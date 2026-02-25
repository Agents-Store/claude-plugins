---
description: Trigger a task with a payload
allowed-tools: mcp__trigger_dev__tds-get_current_worker, mcp__trigger_dev__tds-trigger_task, mcp__trigger_dev__tds-wait_for_run_to_complete
argument-hint: <task-id> [payload-json]
---

# Trigger Task

Trigger a task and optionally wait for the result.

## Arguments
Format: `<task-id> [payload-json]`
- task-id: The task identifier (e.g., "hello-world")
- payload-json: JSON payload matching the task schema (optional)

Parse from "$ARGUMENTS".

## Process

1. **Get task schema:**
   ```
   tds-get_current_worker(environment="dev")
   ```
   Find the matching task and its payload schema.

2. **Trigger the task:**
   ```
   tds-trigger_task(
     taskId=<task-id>,
     payload=<parsed_payload>,
     environment="dev"
   )
   ```

3. **Ask if user wants to wait for result.**

4. **If yes, wait:**
   ```
   tds-wait_for_run_to_complete(
     runId=<run_id>,
     timeoutInSeconds=60
   )
   ```

5. **Report result:**
   - Run ID
   - Status
   - Output (if completed)
   - Duration

## Example Usage
```
/trigger-task hello-world {"name": "Claude"}
/trigger-task process-order {"orderId": "ORD-123", "items": ["item-1"]}
/trigger-task send-email
```

## Notes
- Payload must match the task's expected schema
- If no payload provided and task requires one, prompt user
- Default environment is dev
- Run ID starts with run_
