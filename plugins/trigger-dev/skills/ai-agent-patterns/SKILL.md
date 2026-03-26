---
name: ai-agent-patterns
description: AI agent patterns on Trigger.dev — prompt chaining, routing, parallelization, human-in-the-loop, realtime features, and advanced workflow patterns. Use when building AI agents, complex workflows, or LLM-powered tasks.
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

## 1. Prompt Chaining

Sequential processing where each step feeds into the next:

```typescript
import { task } from "@trigger.dev/sdk/v3";

export const contentPipeline = task({
  id: "content-pipeline",
  machine: "medium-1x",
  run: async (payload: { topic: string }) => {
    const research = await researchTopic(payload.topic);
    const outline = await generateOutline(research);
    const article = await writeArticle(outline);
    const final = await editArticle(article);
    return { article: final };
  },
});
```

## 2. Routing / Orchestrator

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

## 3. Parallelization

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

## 4. Human-in-the-Loop

Wait for human approval before continuing:

```typescript
import { task, wait } from "@trigger.dev/sdk/v3";

export const approvalWorkflow = task({
  id: "approval-workflow",
  run: async (payload: { request: string }) => {
    const analysis = await analyzeRequest(payload.request);

    const token = await wait.createToken({ timeout: "24h" });
    await notifyApprover(token.id, analysis);

    const approval = await wait.forToken(token);

    if (approval.approved) {
      return await executeRequest(payload.request);
    }
    return { status: "rejected", reason: approval.reason };
  },
});
```

## 5. Evaluator / Iterative Refinement

Quality checks with iterative improvement:

```typescript
export const iterativeWriter = task({
  id: "iterative-writer",
  machine: "medium-1x",
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

## 6. Fan-Out / Fan-In

Distribute work, collect results:

```typescript
export const mapReduce = task({
  id: "map-reduce",
  run: async (payload: { documents: string[] }) => {
    // Fan-out: process each document in parallel
    const summaries = await summarizeDoc.batchTriggerAndWait(
      payload.documents.map(doc => ({ payload: { doc } }))
    );

    // Fan-in: combine all summaries
    const combined = await combineSummaries.triggerAndWait({
      summaries: summaries.map(s => s.output),
    });

    return combined;
  },
});
```

## 7. Tool-Calling Agent

Agent that uses tools to accomplish goals:

```typescript
import { task } from "@trigger.dev/sdk/v3";

const tools = {
  search: async (query: string) => { /* web search */ },
  calculate: async (expr: string) => { /* math eval */ },
  database: async (sql: string) => { /* db query */ },
};

export const toolAgent = task({
  id: "tool-agent",
  machine: "medium-1x",
  maxDuration: 300,
  run: async (payload: { goal: string }) => {
    let context = payload.goal;
    let result = null;
    let steps = 0;

    while (!result && steps < 10) {
      const action = await planNextAction(context);

      if (action.type === "done") {
        result = action.answer;
      } else {
        const toolResult = await tools[action.tool](action.input);
        context += `\nTool ${action.tool}: ${toolResult}`;
      }
      steps++;
    }

    return { answer: result, steps };
  },
});
```

## Realtime API

Trigger.dev provides React hooks for live run monitoring.

### useRealtimeRun

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

### useRealtimeBatch

```typescript
import { useRealtimeBatch } from "@trigger.dev/react-hooks";

function BatchProgress({ batchId }: { batchId: string }) {
  const { runs } = useRealtimeBatch(batchId);
  const completed = runs.filter(r => r.status === "COMPLETED").length;
  return <p>Progress: {completed}/{runs.length}</p>;
}
```

## Common Cron Expressions

| Schedule | Cron |
|----------|------|
| Every minute | `* * * * *` |
| Every hour | `0 * * * *` |
| Daily at midnight | `0 0 * * *` |
| Monday 9 AM | `0 9 * * 1` |
| 1st of month | `0 0 1 * *` |

## Best Practices

1. **Break complex agents into sub-tasks** for observability and retry isolation
2. **Use wait.forToken** for human approval rather than polling
3. **Set maxDuration** on agent tasks to prevent infinite loops
4. **Use tags** to track agent runs ("agent-v2", "customer-123")
5. **Monitor with Realtime API** for user-facing agent workflows
6. **Use queues with concurrency limits** for rate-limited AI APIs
7. **Store intermediate results** so retries resume from last checkpoint
8. **Choose appropriate machine** — medium-1x or larger for LLM-heavy tasks
