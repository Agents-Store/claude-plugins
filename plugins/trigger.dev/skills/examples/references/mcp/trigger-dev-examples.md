# Trigger.dev End-to-End Examples

Complete workflow examples using Trigger.dev MCP tools.

## Example 1: New Project Setup

```
# 1. Find your org
Tool: tds-list_orgs
Input: {}
-> [{slug: "acme-corp", id: "org_abc"}]

# 2. Initialize project
Tool: tds-initialize_project
Input: {
  "orgParam": "acme-corp",
  "projectName": "email-jobs",
  "cwd": "/Users/dev/my-app"
}
-> Creates trigger.config.ts, src/trigger/example.ts

# 3. Verify setup
Tool: tds-get_current_worker
Input: {"environment": "dev"}
-> {tasks: [{id: "example-task"}]}
```

## Example 2: Trigger Task and Get Result

```
# 1. Check available tasks
Tool: tds-get_current_worker
Input: {"environment": "prod"}
-> {tasks: [{id: "send-welcome-email", payloadSchema: {...}}]}

# 2. Trigger the task
Tool: tds-trigger_task
Input: {
  "taskId": "send-welcome-email",
  "payload": {"userId": "user_123", "email": "john@example.com"},
  "environment": "prod",
  "options": {
    "tags": ["onboarding"],
    "idempotencyKey": "welcome-user_123"
  }
}
-> {id: "run_xyz789"}

# 3. Wait for result
Tool: tds-wait_for_run_to_complete
Input: {"runId": "run_xyz789", "timeoutInSeconds": 30}
-> {status: "COMPLETED", output: {emailSent: true}}
```

## Example 3: Debug Production Failures

```
# 1. Find failed runs in last 24h
Tool: tds-list_runs
Input: {
  "environment": "prod",
  "status": "FAILED",
  "period": "1d",
  "limit": 5
}
-> [{id: "run_fail1", taskIdentifier: "process-payment"}, ...]

# 2. Get detailed trace
Tool: tds-get_run_details
Input: {"runId": "run_fail1", "environment": "prod"}
-> {
     status: "FAILED",
     error: "Stripe API rate limit exceeded",
     trace: [
       {timestamp: "...", message: "Starting payment processing"},
       {timestamp: "...", message: "Calling Stripe API"},
       {timestamp: "...", level: "error", message: "429 Too Many Requests"}
     ]
   }

# 3. Check docs for queue/concurrency solution
Tool: tds-search_docs
Input: {"query": "queue concurrency limit rate limiting"}
```

## Example 4: Staging to Production Deployment

```
# 1. Deploy to staging
Tool: tds-deploy
Input: {"environment": "staging"}
-> {status: "DEPLOYED", version: "20250225.3"}

# 2. Test in staging
Tool: tds-trigger_task
Input: {
  "taskId": "process-order",
  "payload": {"orderId": "TEST-001", "items": ["test"]},
  "environment": "staging"
}
-> {id: "run_staging1"}

# 3. Verify
Tool: tds-wait_for_run_to_complete
Input: {"runId": "run_staging1"}
-> {status: "COMPLETED"}

# 4. Deploy to production
Tool: tds-deploy
Input: {"environment": "prod"}
-> {status: "DEPLOYED", version: "20250225.3"}

# 5. Confirm
Tool: tds-list_deploys
Input: {"environment": "prod", "limit": 1}
-> [{status: "DEPLOYED", version: "20250225.3"}]
```

## Example 5: Preview Branch Testing

```
# 1. Deploy feature branch
Tool: tds-deploy
Input: {
  "environment": "preview",
  "branch": "feature/ai-summarizer"
}

# 2. List preview branches
Tool: tds-list_preview_branches
Input: {}
-> [{branch: "feature/ai-summarizer", ...}]

# 3. Trigger in preview
Tool: tds-trigger_task
Input: {
  "taskId": "ai-summarize",
  "payload": {"text": "Long article text..."},
  "environment": "preview",
  "branch": "feature/ai-summarizer"
}

# 4. Get result
Tool: tds-wait_for_run_to_complete
Input: {"runId": "run_preview1"}
```
