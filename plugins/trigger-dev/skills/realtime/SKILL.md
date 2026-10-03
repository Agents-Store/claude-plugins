---
name: realtime
description: Subscribe to Trigger.dev task runs in real-time from frontend and backend. Use when the user asks to "show task progress in UI", "stream AI responses", "use trigger.dev React hooks", "subscribe to runs", "build a progress indicator", "use useRealtimeRun", or needs live task status in a React application.
---

# Trigger.dev Realtime

Subscribe to task runs and stream data in real-time from frontend and backend.

## When to Use

- Building progress indicators for long-running tasks
- Creating live dashboards showing task status
- Streaming AI/LLM responses to the UI
- React components that trigger and monitor tasks
- Waiting for user approval in tasks (human-in-the-loop)

## Authentication

### Create Public Access Token (Backend)

```ts
import { auth } from "@trigger.dev/sdk";

const publicToken = await auth.createPublicToken({
  scopes: {
    read: {
      runs: ["run_123"],
      tasks: ["my-task"],
    },
  },
  expirationTime: "1h",
});
```

### Create Trigger Token (for frontend triggering)

```ts
const triggerToken = await auth.createTriggerPublicToken("my-task", {
  expirationTime: "30m",
});
```

## React Hooks

### Installation

```bash
npm add @trigger.dev/react-hooks
```

### Trigger Task from React

```tsx
"use client";
import { useRealtimeTaskTrigger } from "@trigger.dev/react-hooks";
import type { myTask } from "../trigger/tasks";

function TaskTrigger({ accessToken }: { accessToken: string }) {
  const { submit, run, isLoading } = useRealtimeTaskTrigger<typeof myTask>(
    "my-task",
    { accessToken }
  );

  return (
    <div>
      <button onClick={() => submit({ data: "value" })} disabled={isLoading}>
        Start Task
      </button>
      {run && (
        <div>
          <p>Status: {run.status}</p>
          <p>Progress: {run.metadata?.progress}%</p>
          {run.output && <p>Result: {JSON.stringify(run.output)}</p>}
        </div>
      )}
    </div>
  );
}
```

### Subscribe to Existing Run

```tsx
import { useRealtimeRun } from "@trigger.dev/react-hooks";

function RunStatus({ runId, accessToken }: { runId: string; accessToken: string }) {
  const { run, error } = useRealtimeRun<typeof myTask>(runId, {
    accessToken,
    onComplete: (run) => console.log("Completed:", run.output),
  });

  if (error) return <div>Error: {error.message}</div>;
  if (!run) return <div>Loading...</div>;

  return <p>Status: {run.status} — Progress: {run.metadata?.progress || 0}%</p>;
}
```

### Subscribe to Tagged Runs

```tsx
import { useRealtimeRunsWithTag } from "@trigger.dev/react-hooks";

function UserTasks({ userId, accessToken }: Props) {
  const { runs } = useRealtimeRunsWithTag(`user-${userId}`, { accessToken });
  return (
    <ul>{runs.map(run => <li key={run.id}>{run.id}: {run.status}</li>)}</ul>
  );
}
```

### From a Next.js App with Self-Hosted Trigger.dev

Server code triggers and hands the run id and its token to the browser; a Client Component subscribes. Three details decide whether it works against a self-hosted server.

```ts
// app/orders/actions.ts
"use server";
import { auth, tasks } from "@trigger.dev/sdk";
import type { processOrder } from "@/trigger/process-order"; // type only: keeps the task code out of the bundle

export async function startOrder(orderId: string) {
  const handle = await tasks.trigger<typeof processOrder>(
    "process-order",
    { orderId },
    { idempotencyKey: `order-${orderId}` },
    { publicAccessToken: { expirationTime: "1h" } }, // lifetime of the token on the returned handle
  );
  return { runId: handle.id, publicAccessToken: handle.publicAccessToken };
}

// Called by the browser when the token runs out before the run ends
export async function refreshRunToken(runId: string): Promise<string> {
  // Authorize first: this action mints a read token for any run id it is given.
  // Check that the signed-in user owns `runId` (your own table, or a run tag) before minting.
  return auth.createPublicToken({ scopes: { read: { runs: [runId] } }, expirationTime: "15m" });
}
```

```tsx
// components/order-status.tsx
"use client";
import { useRealtimeRun } from "@trigger.dev/react-hooks";
import type { processOrder } from "@/trigger/process-order";
import { refreshRunToken } from "@/app/orders/actions";

export function OrderStatus({ runId, publicAccessToken }: { runId: string; publicAccessToken: string }) {
  const { run, error } = useRealtimeRun<typeof processOrder>(runId, {
    accessToken: publicAccessToken,
    baseURL: process.env.NEXT_PUBLIC_TRIGGER_API_URL, // required when self-hosted
    refreshAccessToken: () => refreshRunToken(runId),
  });

  if (error) return <p>Error: {error.message}</p>;
  if (!run) return <p>Starting...</p>;
  return <p>Status: {run.status}</p>;
}
```

- **`baseURL` is required on self-hosted.** Without it a hook calls Trigger.dev Cloud, because the browser has no `TRIGGER_API_URL` to read: server code gets the address from that variable, a hook gets it only from `baseURL`. Put the address in a `NEXT_PUBLIC_` variable (an address, never a key).
- **A token from the handle is short-lived and read-only for that run.** The docs give 15 minutes by default. Pass `{ publicAccessToken: { expirationTime } }` as the fourth argument of `trigger()` to change it, and give long runs a `refreshAccessToken` callback: a subscription rejected with `401` or `403` then fetches a new token once and reconnects. Without the callback an expired token ends the subscription.
- **Never send `TRIGGER_SECRET_KEY` to the browser.** Only the run-scoped public token travels, and `refreshAccessToken` must call your own server code, which holds the key.

To share one configuration across several hooks, wrap them in the context provider instead of repeating the options. There is no `TriggerProvider` component in `@trigger.dev/react-hooks`:

```tsx
// components/trigger-provider.tsx
"use client";
import { TriggerAuthContext } from "@trigger.dev/react-hooks";
import type { ReactNode } from "react";

export function RunProvider({ accessToken, children }: { accessToken: string; children: ReactNode }) {
  return (
    <TriggerAuthContext.Provider value={{ accessToken, baseURL: process.env.NEXT_PUBLIC_TRIGGER_API_URL }}>
      {children}
    </TriggerAuthContext.Provider>
  );
}
```

Hooks below it can then be called without `accessToken` and `baseURL`.

## Realtime Streams (AI/LLM)

### Define Stream

```ts
// trigger/streams.ts
import { streams } from "@trigger.dev/sdk";
export const aiStream = streams.define<string>({ id: "ai-output" });
```

### Pipe Stream in Task

```ts
import { task } from "@trigger.dev/sdk";
import { aiStream } from "./streams";

export const streamingTask = task({
  id: "streaming-task",
  run: async (payload: { prompt: string }) => {
    const completion = await openai.chat.completions.create({
      model: "gpt-4", messages: [{ role: "user", content: payload.prompt }], stream: true,
    });
    const { waitUntilComplete } = aiStream.pipe(completion);
    await waitUntilComplete();
  },
});
```

### Read Stream in React

```tsx
import { useRealtimeStream } from "@trigger.dev/react-hooks";
import { aiStream } from "../trigger/streams";

function AIResponse({ runId, accessToken }: Props) {
  const { parts, error } = useRealtimeStream(aiStream, runId, {
    accessToken, throttleInMs: 50,
  });
  if (!parts) return <div>Waiting...</div>;
  return <div>{parts.join("")}</div>;
}
```

## Wait Tokens (Human-in-the-loop)

### Complete Token from React

Create the token in your backend with `wait.createToken()`, then pass `token.id` (starts with `waitpoint_`) and `token.publicAccessToken` to the component:

```tsx
import { useWaitToken } from "@trigger.dev/react-hooks";

function ApprovalButton({ tokenId, accessToken }: Props) {
  const { complete } = useWaitToken(tokenId, { accessToken });
  return (
    <div>
      <button onClick={() => complete({ approved: true })}>Approve</button>
      <button onClick={() => complete({ approved: false })}>Reject</button>
    </div>
  );
}
```

## Backend Subscriptions

```ts
import { runs, tasks } from "@trigger.dev/sdk";

const handle = await tasks.trigger("my-task", { data: "value" });

for await (const run of runs.subscribeToRun(handle.id)) {
  console.log(`Status: ${run.status}`);
  if (run.status === "COMPLETED") break;
}
```

## Run Object Properties

| Property | Description |
|----------|-------------|
| `id` | Unique run identifier |
| `status` | QUEUED, EXECUTING, COMPLETED, FAILED, CANCELED |
| `payload` | Task input (typed) |
| `output` | Task result (typed, when completed) |
| `metadata` | Real-time updatable data |
| `createdAt` | Start timestamp |

## Deeper Reference

- @references/realtime-reference.md — complete Realtime API
