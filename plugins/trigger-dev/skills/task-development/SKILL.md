---
name: task-development
description: Writing Trigger.dev tasks, configuration, build extensions, scheduled tasks, and coding patterns. Use when developing or modifying tasks, configuring trigger.config.ts, or asking about task patterns.
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
    return { processed: true };
  },
});
```

## Scheduled / Cron Tasks

```typescript
import { schedules } from "@trigger.dev/sdk/v3";

export const dailyReport = schedules.task({
  id: "daily-report",
  cron: "0 9 * * *",
  run: async (payload) => {
    // payload.timestamp, payload.lastTimestamp, payload.externalId
    console.log("Generating daily report...");
  },
});
```

## Triggering Sub-Tasks

### trigger() — Fire and Forget

```typescript
export const parentTask = task({
  id: "parent-task",
  run: async () => {
    const handle = await helloWorld.trigger({ name: "World" });
    return { runId: handle.id };
  },
});
```

### triggerAndWait() — Wait for Result

```typescript
export const parentTask = task({
  id: "parent-task",
  run: async () => {
    const result = await helloWorld.triggerAndWait({ name: "World" });
    return result;
  },
});
```

### batchTriggerAndWait() — Parallel Processing

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

### wait.for() — Delay Execution

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
export const approvalTask = task({
  id: "approval-task",
  run: async () => {
    const token = await wait.createToken({ timeout: "24h" });
    // Send token.id to external system / human
    const result = await wait.forToken(token);
    return result;
  },
});
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
    // Max 5 concurrent executions
  },
});
```

## Build Extensions

Add to `trigger.config.ts`:

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

Available extensions:
- **prismaExtension** — Prisma ORM support
- **puppeteer** — Headless browser
- **playwright** — Browser automation
- **ffmpeg** — Video/audio processing
- **pythonExtension** — Run Python code
- **aptGet** — Install system packages
- **syncEnvVars** — Sync environment variables
- **syncVercelEnvVars** — Sync from Vercel
- **emitDecoratorMetadata** — TypeScript decorators
- **additionalFiles** — Include extra files
- **additionalPackages** — Include extra npm packages
- **audioWaveform** — Audio waveform generation
- **esbuildPlugin** — Custom esbuild plugins

Search docs for details: `tds-search_docs(query="build extensions configuration")`

## trigger.config.ts Reference

### Minimal

```typescript
import { defineConfig } from "@trigger.dev/sdk/v3";

export default defineConfig({
  project: "proj_xxx",
});
```

### Full Configuration

```typescript
import { defineConfig } from "@trigger.dev/sdk/v3";

export default defineConfig({
  project: "proj_xxx",
  runtime: "node",             // "node" | "bun"
  logLevel: "info",            // "debug" | "info" | "warn" | "error"
  maxDuration: 300,            // Default max seconds
  retries: {
    enabledInDev: false,
    default: {
      maxAttempts: 3,
      factor: 2,
      minTimeoutInMs: 1000,
      maxTimeoutInMs: 30000,
    },
  },
  dirs: ["src/trigger"],       // Task directories
  machine: "small-1x",        // Default machine
  build: {
    extensions: [],
  },
});
```

### Self-Hosted Config

For self-hosted instances, the `triggerUrl` in config is optional — the CLI reads `TRIGGER_API_URL` from environment. But you can set it explicitly:

```typescript
export default defineConfig({
  project: "proj_xxx",
  triggerUrl: process.env.TRIGGER_API_URL,
});
```

## Machine Presets

| Preset | vCPUs | Memory | Use Case |
|--------|-------|--------|----------|
| micro | 0.25 | 0.25 GB | Simple tasks |
| small-1x | 0.5 | 0.5 GB | API calls |
| small-2x | 1 | 1 GB | Data processing |
| medium-1x | 1 | 2 GB | AI inference |
| medium-2x | 2 | 4 GB | Heavy processing |
| large-1x | 2 | 8 GB | Large datasets |
| large-2x | 4 | 8 GB | ML workloads |

## Viewing Deployed Tasks

```
Tool: tds-get_current_worker
Input: {"environment": "dev"}
→ Worker version, tasks with IDs, payload schemas, machine presets, queue config
```

## Best Practices

1. **Use TypeScript** for payload typing and IDE support
2. **Define payload schemas** with Zod for validation
3. **Set sensible retries** — not all tasks should retry (idempotency matters)
4. **Use queues** for rate-limited external APIs
5. **Choose right machine** — start small, scale up if needed
6. **Keep tasks focused** — one task per logical operation
7. **Use sub-tasks** for complex workflows instead of monolithic tasks
