---
name: sdk-patterns
description: This skill should be used when the user asks about "trigger.dev SDK", "@trigger.dev/sdk", "trigger.dev client library", "trigger.dev npm package", "how to use trigger.dev in code", "trigger.dev TypeScript", or needs code patterns for integrating Trigger.dev into a project.
---

# Trigger.dev SDK Patterns

Code patterns for using the Trigger.dev SDK v3 in your project.

## Installation

```bash
npm install @trigger.dev/sdk
# or
pnpm add @trigger.dev/sdk
# or
yarn add @trigger.dev/sdk
```

For self-hosted instances, also set the API URL:

```bash
# .env
TRIGGER_API_URL=https://trigger.your-domain.com
TRIGGER_SECRET_KEY=tr_dev_xxxxxxxxxxxxxx
```

## Core Imports

```typescript
// Task definition
import { task, schedules, wait, queue } from "@trigger.dev/sdk/v3";

// Configuration
import { defineConfig } from "@trigger.dev/sdk/v3";

// Build extensions
import { prismaExtension } from "@trigger.dev/build/extensions/prisma";
import { syncEnvVars } from "@trigger.dev/build/extensions";

// React hooks (frontend)
import { useRealtimeRun, useRealtimeBatch } from "@trigger.dev/react-hooks";
```

## Task Definition

### Basic Task

```typescript
import { task } from "@trigger.dev/sdk/v3";

export const myTask = task({
  id: "my-task",
  run: async (payload: { input: string }) => {
    return { result: payload.input.toUpperCase() };
  },
});
```

### Task with Full Config

```typescript
import { task } from "@trigger.dev/sdk/v3";

export const processOrder = task({
  id: "process-order",
  retry: {
    maxAttempts: 3,
    factor: 2,
    minTimeoutInMs: 1000,
    maxTimeoutInMs: 30000,
  },
  machine: "small-1x",
  queue: {
    name: "order-processing",
    concurrencyLimit: 10,
  },
  run: async (payload: { orderId: string; items: string[] }) => {
    // Process order
    return { processed: true };
  },
});
```

### Task with Zod Validation

```typescript
import { task } from "@trigger.dev/sdk/v3";
import { z } from "zod";

const PayloadSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1),
  template: z.enum(["welcome", "reset", "invoice"]),
});

export const sendEmail = task({
  id: "send-email",
  run: async (payload: z.infer<typeof PayloadSchema>) => {
    const validated = PayloadSchema.parse(payload);
    // Send email
    return { sent: true, to: validated.email };
  },
});
```

## Scheduled Tasks

```typescript
import { schedules } from "@trigger.dev/sdk/v3";

export const dailyReport = schedules.task({
  id: "daily-report",
  cron: "0 9 * * *", // Every day at 9 AM
  run: async (payload) => {
    // payload.timestamp — scheduled time
    // payload.lastTimestamp — previous run time
    // payload.externalId — schedule external ID
    console.log(`Running at: ${payload.timestamp}`);
  },
});
```

Common cron expressions:

| Schedule | Cron |
|----------|------|
| Every minute | `* * * * *` |
| Every hour | `0 * * * *` |
| Daily at midnight | `0 0 * * *` |
| Monday 9 AM | `0 9 * * 1` |
| 1st of month | `0 0 1 * *` |

## Triggering Tasks

### trigger() — Fire and Forget

```typescript
const handle = await myTask.trigger({ input: "hello" });
// Returns immediately with run handle
console.log(handle.id); // run_xxx
```

### triggerAndWait() — Wait for Result

```typescript
const result = await myTask.triggerAndWait({ input: "hello" });
// Blocks until task completes
console.log(result); // { result: "HELLO" }
```

### batchTrigger() — Trigger Multiple

```typescript
const handles = await myTask.batchTrigger([
  { payload: { input: "alice" } },
  { payload: { input: "bob" } },
]);
```

### batchTriggerAndWait() — Trigger Multiple and Wait

```typescript
const results = await myTask.batchTriggerAndWait([
  { payload: { input: "alice" } },
  { payload: { input: "bob" } },
]);
// Returns all results when all complete
```

## Queues and Concurrency

```typescript
import { task, queue } from "@trigger.dev/sdk/v3";

const emailQueue = queue({
  name: "email-sending",
  concurrencyLimit: 5,
});

export const sendEmail = task({
  id: "send-email",
  queue: emailQueue,
  run: async (payload: { to: string; subject: string }) => {
    // Max 5 concurrent email sends
  },
});
```

## Wait Patterns

### wait.for() — Delay

```typescript
import { task, wait } from "@trigger.dev/sdk/v3";

export const delayedTask = task({
  id: "delayed-task",
  run: async () => {
    await wait.for({ seconds: 30 });
    // or: { minutes: 5 }, { hours: 1 }, { days: 1 }
  },
});
```

### wait.forToken() — Human-in-the-Loop

```typescript
import { task, wait } from "@trigger.dev/sdk/v3";

export const approvalTask = task({
  id: "approval-task",
  run: async (payload: { requestId: string }) => {
    const token = await wait.createToken({ timeout: "24h" });

    // Send token.id to external system (Slack, email, webhook)
    await notifyApprover(token.id, payload.requestId);

    // Execution pauses here until token is completed
    const result = await wait.forToken<{ approved: boolean }>(token);

    return result;
  },
});
```

Complete the token externally via API:
```bash
curl -X POST "${TRIGGER_API_URL}/api/v1/tokens/${TOKEN_ID}/complete" \
  -H "Authorization: Bearer ${TRIGGER_SECRET_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"data": {"approved": true}}'
```

## Realtime API (Frontend)

### useRealtimeRun Hook

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

### useRealtimeBatch Hook

```typescript
import { useRealtimeBatch } from "@trigger.dev/react-hooks";

function BatchProgress({ batchId }: { batchId: string }) {
  const { runs } = useRealtimeBatch(batchId);

  const completed = runs.filter(r => r.status === "COMPLETED").length;
  return <p>Progress: {completed}/{runs.length}</p>;
}
```

## Machine Presets

| Preset | vCPUs | Memory |
|--------|-------|--------|
| micro | 0.25 | 0.25 GB |
| small-1x | 0.5 | 0.5 GB |
| small-2x | 1 | 1 GB |
| medium-1x | 1 | 2 GB |
| medium-2x | 2 | 4 GB |
| large-1x | 2 | 8 GB |
| large-2x | 4 | 8 GB |

## Error Handling

```typescript
import { task } from "@trigger.dev/sdk/v3";

export const resilientTask = task({
  id: "resilient-task",
  retry: {
    maxAttempts: 3,
    factor: 2,
    minTimeoutInMs: 1000,
    maxTimeoutInMs: 30000,
  },
  run: async (payload: { url: string }) => {
    const response = await fetch(payload.url);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      // Will be retried up to maxAttempts times
    }
    return await response.json();
  },
});
```

## Best Practices

1. **Use TypeScript** for payload typing and IDE support
2. **Define payload schemas** with Zod for runtime validation
3. **Set sensible retries** — not all tasks should retry (idempotency matters)
4. **Use queues** for rate-limited external APIs
5. **Choose the right machine** — start with micro/small, scale up as needed
6. **Keep tasks focused** — one task per logical operation
7. **Use sub-tasks** for complex workflows instead of monolithic tasks
8. **Store credentials in environment variables**, never in code
9. **Use `idempotencyKey`** for operations that should not duplicate
10. **Set `maxDuration`** to prevent runaway tasks
