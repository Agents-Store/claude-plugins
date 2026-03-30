# MCP Tool Call Patterns

## Check Available Tasks

```
Tool: get_current_worker
Input: { "environment": "dev" }
→ Returns worker version, task list with IDs, payload schemas, machine presets
```

## Trigger a Task

```
Tool: trigger_task
Input: {
  "taskId": "process-order",
  "payload": { "orderId": "ORD-123", "items": ["item-1"] },
  "environment": "dev"
}
→ { id: "run_abc123", status: "QUEUED" }
```

## Trigger with Full Options

```
Tool: trigger_task
Input: {
  "taskId": "process-order",
  "payload": { "orderId": "ORD-123" },
  "environment": "prod",
  "options": {
    "tags": ["priority", "vip"],
    "idempotencyKey": "order-ORD-123",
    "machine": "medium-1x",
    "maxAttempts": 5,
    "delay": "5m"
  }
}
```

## Wait for Completion

```
Tool: wait_for_run_to_complete
Input: { "runId": "run_abc123", "timeoutInSeconds": 120 }
→ { status: "COMPLETED", output: { processed: true } }
```

## List Failed Runs

```
Tool: list_runs
Input: {
  "environment": "prod",
  "status": "FAILED",
  "period": "7d",
  "limit": 20
}
```

## Get Run Details with Trace

```
Tool: get_run_details
Input: { "runId": "run_abc123", "environment": "prod", "maxTraceLines": 500 }
→ { status, error, trace: [...], output: {...} }
```

## Deploy to Staging

```
Tool: deploy
Input: { "environment": "staging" }
→ { status: "DEPLOYED", version: "20250225.2" }
```

## Search Documentation

```
Tool: search_docs
Input: { "query": "wait for token human in the loop" }
```

## Full Workflow: Trigger → Wait → Report

```
1. get_current_worker(environment="dev")
   → Find task ID and verify payload schema

2. trigger_task(taskId="hello-world", payload={"name": "Claude"})
   → Get run_xxx ID

3. wait_for_run_to_complete(runId="run_xxx", timeoutInSeconds=60)
   → Get final status and output
```

## Full Workflow: Debug Failed Run

```
1. list_runs(status="FAILED", period="1d", limit=5)
   → Get list of failed run IDs

2. get_run_details(runId="run_xxx", maxTraceLines=500)
   → Read error message and stack trace

3. search_docs(query="<error message keywords>")
   → Find relevant documentation
```
