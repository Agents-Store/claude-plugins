# Task Code Templates

Ready-to-use task templates for common Trigger.dev patterns.

## Basic Task

```typescript
import { task } from "@trigger.dev/sdk/v3";

export const myTask = task({
  id: "my-task",
  run: async (payload: { input: string }) => {
    return { result: payload.input.toUpperCase() };
  },
});
```

## Task with Retries and Machine

```typescript
import { task } from "@trigger.dev/sdk/v3";

export const reliableTask = task({
  id: "reliable-task",
  retry: {
    maxAttempts: 5,
    factor: 2,
    minTimeoutInMs: 1000,
    maxTimeoutInMs: 60000,
  },
  machine: "small-1x",
  run: async (payload: { url: string }) => {
    const response = await fetch(payload.url);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  },
});
```

## Scheduled / Cron Task

```typescript
import { schedules } from "@trigger.dev/sdk/v3";

export const cronJob = schedules.task({
  id: "hourly-sync",
  cron: "0 * * * *",
  run: async (payload) => {
    console.log(`Running at: ${payload.timestamp}`);
    console.log(`Last run: ${payload.lastTimestamp}`);
  },
});
```

## Queue with Concurrency Limit

```typescript
import { task, queue } from "@trigger.dev/sdk/v3";

const apiQueue = queue({
  name: "external-api",
  concurrencyLimit: 3,
});

export const apiCall = task({
  id: "api-call",
  queue: apiQueue,
  run: async (payload: { endpoint: string }) => {
    return await fetch(payload.endpoint).then(r => r.json());
  },
});
```

## Parent Task with Sub-Tasks

```typescript
import { task } from "@trigger.dev/sdk/v3";
import { processItem } from "./process-item";

export const batchProcessor = task({
  id: "batch-processor",
  run: async (payload: { items: string[] }) => {
    const results = await processItem.batchTriggerAndWait(
      payload.items.map(item => ({ payload: { item } }))
    );
    return { processed: results.length };
  },
});
```

## Human-in-the-Loop Task

```typescript
import { task, wait } from "@trigger.dev/sdk/v3";

export const approvalFlow = task({
  id: "approval-flow",
  run: async (payload: { request: string; userId: string }) => {
    const token = await wait.createToken({ timeout: "48h" });
    await sendApprovalNotification(token.id, payload);

    const response = await wait.forToken<{ approved: boolean }>(token);

    if (response.approved) {
      return { status: "approved", executedAt: new Date() };
    }
    return { status: "rejected" };
  },
});
```

## AI Agent Task

```typescript
import { task } from "@trigger.dev/sdk/v3";
import { generateText } from "ai";

export const aiAgent = task({
  id: "ai-agent",
  machine: "medium-1x",
  retry: { maxAttempts: 2 },
  run: async (payload: { prompt: string; context?: string }) => {
    const result = await generateText({
      model: "gpt-4",
      prompt: payload.prompt,
      system: payload.context,
    });
    return { response: result.text };
  },
});
```

## Task with Zod Payload Validation

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
    return { sent: true, to: validated.email };
  },
});
```

## Webhook Handler Task

```typescript
import { task } from "@trigger.dev/sdk/v3";

export const webhookHandler = task({
  id: "webhook-handler",
  run: async (payload: { event: string; data: Record<string, unknown> }) => {
    switch (payload.event) {
      case "order.created":
        return await processNewOrder(payload.data);
      case "payment.received":
        return await processPayment(payload.data);
      default:
        console.log(`Unhandled event: ${payload.event}`);
    }
  },
});
```

## File Processing Task

```typescript
import { task } from "@trigger.dev/sdk/v3";

export const processFile = task({
  id: "process-file",
  machine: "medium-1x",
  maxDuration: 600,
  run: async (payload: { fileUrl: string; outputFormat: string }) => {
    const response = await fetch(payload.fileUrl);
    const buffer = await response.arrayBuffer();

    // Process file (e.g., with Sharp, FFmpeg, etc.)
    const result = await transform(buffer, payload.outputFormat);

    return { size: result.byteLength, format: payload.outputFormat };
  },
});
```
