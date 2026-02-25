---
name: ai-agent-patterns
description: AI agent patterns on Trigger.dev - prompt chaining, routing, parallelization, human-in-the-loop, realtime features, and advanced workflow patterns. Use when building AI agents or complex workflows.
---

# AI Agent Patterns

This skill covers building AI agent workflows, realtime features, and advanced patterns on Trigger.dev.

## Available Tools

| Tool | Description |
|------|-------------|
| `tds-search_docs` | Search docs for agent patterns and realtime API |
| `tds-get_current_worker` | View deployed tasks and schemas |
| `tds-trigger_task` | Trigger agent tasks |
| `tds-get_run_details` | Monitor agent run progress |
| `tds-wait_for_run_to_complete` | Wait for agent completion |

## AI Agent Patterns

Trigger.dev is built for running AI agent workflows as background tasks. Search docs for latest patterns:

```
Tool: tds-search_docs
Input: {"query": "AI agent patterns prompt chaining"}
```

### 1. Prompt Chaining

Sequential processing where each step feeds into the next:

```typescript
import { task } from "@trigger.dev/sdk/v3";

export const contentPipeline = task({
  id: "content-pipeline",
  run: async (payload: { topic: string }) => {
    // Step 1: Research
    const research = await researchTopic(payload.topic);

    // Step 2: Outline
    const outline = await generateOutline(research);

    // Step 3: Write
    const article = await writeArticle(outline);

    // Step 4: Edit
    const final = await editArticle(article);

    return { article: final };
  },
});
```

### 2. Routing / Orchestrator

Route to different sub-tasks based on input:

```typescript
export const router = task({
  id: "request-router",
  run: async (payload: { type: string; data: any }) => {
    switch (payload.type) {
      case "image":
        return await imageProcessor.triggerAndWait(payload.data);
      case "text":
        return await textProcessor.triggerAndWait(payload.data);
      case "code":
        return await codeProcessor.triggerAndWait(payload.data);
      default:
        throw new Error(`Unknown type: ${payload.type}`);
    }
  },
});
```

### 3. Parallelization

Process multiple items concurrently:

```typescript
export const parallelProcessor = task({
  id: "parallel-processor",
  run: async (payload: { urls: string[] }) => {
    const results = await processUrl.batchTriggerAndWait(
      payload.urls.map(url => ({ payload: { url } }))
    );
    return results;
  },
});
```

### 4. Human-in-the-Loop

Wait for human approval before continuing:

```typescript
import { task, wait } from "@trigger.dev/sdk/v3";

export const approvalWorkflow = task({
  id: "approval-workflow",
  run: async (payload: { request: string }) => {
    // Process request
    const analysis = await analyzeRequest(payload.request);

    // Create approval token
    const token = await wait.createToken({ timeout: "24h" });

    // Send token to approval system (Slack, email, etc.)
    await notifyApprover(token.id, analysis);

    // Wait for human response
    const approval = await wait.forToken(token);

    if (approval.approved) {
      return await executeRequest(payload.request);
    } else {
      return { status: "rejected", reason: approval.reason };
    }
  },
});
```

### 5. Evaluator Pattern

Iterative refinement with quality checks:

```typescript
export const iterativeWriter = task({
  id: "iterative-writer",
  run: async (payload: { prompt: string }) => {
    let draft = await generateDraft(payload.prompt);
    let score = 0;
    let attempts = 0;

    while (score < 0.8 && attempts < 5) {
      const evaluation = await evaluateDraft(draft);
      score = evaluation.score;

      if (score < 0.8) {
        draft = await improveDraft(draft, evaluation.feedback);
      }
      attempts++;
    }

    return { content: draft, quality: score, iterations: attempts };
  },
});
```

## Realtime API

Trigger.dev provides a Realtime API with React hooks for live updates:

```
Tool: tds-search_docs
Input: {"query": "realtime API React hooks useRealtimeRun"}
```

### React Hook: useRealtimeRun
```typescript
import { useRealtimeRun } from "@trigger.dev/react-hooks";

function RunStatus({ runId }: { runId: string }) {
  const { run, error } = useRealtimeRun(runId);

  if (error) return <div>Error: {error.message}</div>;
  if (!run) return <div>Loading...</div>;

  return (
    <div>
      <p>Status: {run.status}</p>
      <p>Output: {JSON.stringify(run.output)}</p>
    </div>
  );
}
```

### React Hook: useRealtimeBatch
```typescript
import { useRealtimeBatch } from "@trigger.dev/react-hooks";

function BatchStatus({ batchId }: { batchId: string }) {
  const { runs } = useRealtimeBatch(batchId);
  // Display progress of all runs in batch
}
```

## Scheduled Task Patterns

### Recurring Cron Jobs
```typescript
import { schedules } from "@trigger.dev/sdk/v3";

export const dailyCleanup = schedules.task({
  id: "daily-cleanup",
  cron: "0 2 * * *", // 2 AM daily
  run: async (payload) => {
    // payload.timestamp - scheduled time
    // payload.lastTimestamp - previous run time
    await cleanupOldRecords();
  },
});
```

### Common Cron Expressions

| Schedule | Cron | Description |
|----------|------|-------------|
| Every minute | `* * * * *` | Frequent polling |
| Every hour | `0 * * * *` | Hourly tasks |
| Daily at midnight | `0 0 * * *` | Daily cleanup |
| Monday 9 AM | `0 9 * * 1` | Weekly reports |
| 1st of month | `0 0 1 * *` | Monthly billing |

## Best Practices

1. **Break complex agents into sub-tasks** for observability and retry isolation
2. **Use wait.forToken** for human approval rather than polling
3. **Set maxDuration** on agent tasks to prevent infinite loops
4. **Use tags** to track different agent runs (e.g., "agent-v2", "customer-123")
5. **Monitor with Realtime API** for user-facing agent workflows
6. **Use queues with concurrency limits** when calling rate-limited AI APIs
7. **Store intermediate results** so retries resume from last checkpoint
