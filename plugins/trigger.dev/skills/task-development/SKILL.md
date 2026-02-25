---
name: task-development
description: Writing trigger.dev tasks, configuration, build extensions, scheduled tasks, and coding patterns. Use when developing or modifying tasks.
---

# Task Development

This skill covers writing Trigger.dev tasks, configuring them, and using build extensions.

## Available Tools

| Tool | Description |
|------|-------------|
| `tds-search_docs` | Search docs for task APIs and patterns |
| `tds-get_current_worker` | Get worker info, task list, and payload schemas |

## Task Basics

### Simple Task
```typescript
import { task } from "@trigger.dev/sdk/v3";

export const helloWorld = task({
  id: "hello-world",
  run: async (payload: { name: string }) => {
    console.log(`Hello, ${payload.name}!`);
    return { message: `Hello, ${payload.name}!` };
  },
});
```

### Task with Full Configuration
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
    // Task implementation
    return { processed: true };
  },
});
```

## Scheduled / Cron Tasks

```typescript
import { schedules } from "@trigger.dev/sdk/v3";

export const dailyReport = schedules.task({
  id: "daily-report",
  cron: "0 9 * * *", // Every day at 9 AM
  run: async (payload) => {
    // payload includes: timestamp, lastTimestamp, externalId, etc.
    console.log("Generating daily report...");
  },
});
```

Search docs for advanced scheduling:
```
Tool: tds-search_docs
Input: {"query": "scheduled tasks cron schedules"}
```

## Triggering Sub-Tasks

### trigger() - Fire and forget
```typescript
import { helloWorld } from "./hello-world";

export const parentTask = task({
  id: "parent-task",
  run: async () => {
    const handle = await helloWorld.trigger({ name: "World" });
    // Returns immediately with run handle
    return { runId: handle.id };
  },
});
```

### triggerAndWait() - Wait for result
```typescript
export const parentTask = task({
  id: "parent-task",
  run: async () => {
    const result = await helloWorld.triggerAndWait({ name: "World" });
    // Waits for child task to complete
    return result;
  },
});
```

### batchTrigger() and batchTriggerAndWait()
```typescript
export const batchParent = task({
  id: "batch-parent",
  run: async () => {
    const results = await helloWorld.batchTriggerAndWait([
      { payload: { name: "Alice" } },
      { payload: { name: "Bob" } },
      { payload: { name: "Charlie" } },
    ]);
    return results;
  },
});
```

## Wait Patterns

### wait.for() - Delay execution
```typescript
import { task, wait } from "@trigger.dev/sdk/v3";

export const delayedTask = task({
  id: "delayed-task",
  run: async () => {
    await wait.for({ seconds: 30 });
    // or: await wait.for({ minutes: 5 });
    // or: await wait.for({ hours: 1 });
    // Continues after delay
  },
});
```

### wait.forToken() - Human-in-the-loop
```typescript
export const approvalTask = task({
  id: "approval-task",
  run: async () => {
    const token = await wait.createToken({
      timeout: "24h",
    });
    // Send token.id to external system / human
    const result = await wait.forToken(token);
    // result contains the data passed when completing the token
    return result;
  },
});
```

Search docs for advanced wait patterns:
```
Tool: tds-search_docs
Input: {"query": "wait for token human in the loop"}
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
  run: async (payload: { to: string; subject: string; body: string }) => {
    // Only 5 runs execute concurrently
  },
});
```

## Build Extensions

Trigger.dev supports 13+ build extensions. Add them to `trigger.config.ts`:

```typescript
import { defineConfig } from "@trigger.dev/sdk/v3";
import { prismaExtension } from "@trigger.dev/build/extensions/prisma";
import { puppeteer } from "@trigger.dev/build/extensions/puppeteer";
import { ffmpeg } from "@trigger.dev/build/extensions/ffmpeg";

export default defineConfig({
  project: "proj_xxx",
  build: {
    extensions: [
      prismaExtension({ version: "5.x" }),
      puppeteer(),
      ffmpeg(),
    ],
  },
});
```

Available extensions (search docs for details):
- **prismaExtension** - Prisma ORM support
- **puppeteer** - Headless browser
- **playwright** - Browser automation
- **ffmpeg** - Video/audio processing
- **pythonExtension** - Run Python code
- **aptGet** - Install system packages
- **syncEnvVars** - Sync environment variables
- **syncVercelEnvVars** - Sync from Vercel
- **emitDecoratorMetadata** - TypeScript decorators
- **additionalFiles** - Include extra files
- **additionalPackages** - Include extra npm packages
- **audioWaveform** - Audio waveform generation
- **esbuildPlugin** - Custom esbuild plugins

```
Tool: tds-search_docs
Input: {"query": "build extensions configuration"}
```

## Viewing Deployed Tasks

To see what tasks are deployed and their schemas:
```
Tool: tds-get_current_worker
Input: {
  "environment": "dev"
}

Returns worker version, tasks list with:
- Task ID/slug
- Payload JSON schema
- Machine preset
- Queue configuration
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

## Best Practices

1. **Use TypeScript** for payload typing and IDE support
2. **Define payload schemas** with Zod for validation
3. **Set sensible retries** - not all tasks should retry (idempotency matters)
4. **Use queues** for rate-limited external APIs
5. **Choose right machine** - start small, scale up if needed
6. **Keep tasks focused** - one task per logical operation
7. **Use sub-tasks** for complex workflows instead of monolithic tasks
