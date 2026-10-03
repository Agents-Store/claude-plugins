---
name: ai-chat-agents
description: Build durable AI chat agents on Trigger.dev with chat.agent, sessions and the useTriggerChatTransport React transport (requires server 4.5.0 or newer and AI SDK 5+). Use when the user asks about "chat.agent", "trigger.dev chat agent", "AI chat on trigger.dev", "useTriggerChatTransport", "trigger.dev sessions", "start_agent_chat", "human in the loop chat", or migrating a streamText route to Trigger.dev.
---

# AI Chat Agents (chat.agent)

A `chat.agent` runs a whole conversation as one long-lived Trigger.dev task: it wakes when a message arrives, is suspended when none do, and keeps its state across page refreshes, deploys and idle gaps. There are no API routes: the browser talks to the agent through a transport, history accumulates server-side, and the client sends only the new message each turn.

> **Version requirements (decision D8: the plugin baseline stays server 4.4.4).** Chat agents and Sessions need **server ≥ 4.5.0** (the Session tables first appeared in 4.4.5) and `@trigger.dev/sdk` ≥ 4.5.0. They work with the Vercel AI SDK `ai` v5, v6 or v7 only (v4 is not supported). 4.6.x changes: Zod 4 by default (peer `^3.25.56 || ^4`), reading a session's `.in` stream needs the secret key (public tokens get 403), `hydrateMessages` is deprecated in favour of `loadContext` / transcript storage, and 4.6.0-4.6.3 have a warm-start defect with Zod 3 (use 4.6.4 or later). Self-hosted: realtime streams run on the bundled `s2` service (see the **deployment** skill). Model ids below are placeholders.

## 1. Define the agent

```ts
// trigger/chat.ts
import { chat } from "@trigger.dev/sdk/ai";
import { stepCountIs } from "ai"; // helpers come from "ai"; streamText does not
import { anthropic } from "@ai-sdk/anthropic";

export const myChat = chat.agent({
  id: "my-chat",
  // Take `streamText` from the run argument, NOT from "ai" (see Common mistakes)
  run: async ({ messages, signal, streamText }) =>
    streamText({
      model: anthropic("<model id>"),
      messages,
      abortSignal: signal,        // makes the Stop button actually stop generation
      stopWhen: stepCountIs(15),
    }),
});
```

`messages` arrive already converted to `ModelMessage[]`. Returning the `StreamTextResult` pipes it to the frontend; when `streamText` is called deep in a helper, call `await chat.pipe(result)` instead.

Add `trigger.config.ts` with `maxDuration` like any task; an agent is a task and deploys the same way.

## 2. Two server actions

Both run on your server so the browser never holds the environment secret key. Per-user authorization goes here.

```ts
// app/actions.ts
"use server";
import { auth } from "@trigger.dev/sdk";
import { chat } from "@trigger.dev/sdk/ai";

// Creates the Session and its first run; idempotent per (environment, chatId)
export const startChatSession = chat.createStartSessionAction("my-chat");

// The transport calls this to refresh an expired token
export async function mintChatAccessToken(chatId: string) {
  return auth.createPublicToken({
    scopes: { read: { sessions: chatId }, write: { sessions: chatId } },
    expirationTime: "1h",
  });
}
```

## 3. Frontend

```tsx
"use client";
import { useChat } from "@ai-sdk/react";
import { useTriggerChatTransport } from "@trigger.dev/sdk/chat/react";
import type { myChat } from "@/trigger/chat";
import { mintChatAccessToken, startChatSession } from "@/app/actions";

export function Chat() {
  const transport = useTriggerChatTransport<typeof myChat>({
    task: "my-chat",
    accessToken: ({ chatId }) => mintChatAccessToken(chatId),
    startSession: ({ chatId, clientData }) => startChatSession({ chatId, clientData }),
  });
  const { messages, sendMessage, stop, status } = useChat({ transport });
  // render messages; sendMessage({ text }); a Stop button calling stop() while status === "streaming"
}
```

## Tools

Declare tools on the config and pass the typed set back, so each tool's `toModelOutput` is re-applied when history is converted on later turns. A Trigger.dev task can be the tool: `tool({ description, inputSchema, execute: ai.toolExecute(task) })` (see **ai-agent-patterns**, `references/ai-tool.md`).

```ts
export const myChat = chat.agent({
  id: "my-chat",
  tools,   // declared once
  run: async ({ messages, tools, signal, streamText }) =>
    streamText({ model, messages, tools, abortSignal: signal, stopWhen: stepCountIs(15) }),
});
```

## Lifecycle

Per turn the hooks fire in order: `onValidateMessages`, storage load, `onChatStart` (first message only), `onTurnStart`, `run()`, `onBeforeTurnComplete`, `onTurnComplete`, storage save. `onBoot` fires once per worker process (put `chat.local`, DB connections there). Options include `maxTurns` (100), `turnTimeout` (`"1h"`), `idleTimeoutInSeconds` (30). `chat.agent` runs with `maxAttempts: 1`; there is no generic `retry`.

Managed prompts plug in with `chat.prompt.set(await myPrompt.resolve(vars))` in `onChatStart` and `...chat.toStreamTextOptions({ registry })` (see **managed-prompts**).

## Sessions, concurrency and MCP

- A **Session** is a stateful execution of an agent with a durable input stream (`.in`) and output stream (`.out`); one Session can span many runs. `chat.agent` is built on them; `sessions.start()`, `sessions.open(id)`, `session.in.send/wait`, `session.out.append/read` are the raw primitives.
- Per-tenant concurrency for chats (server ≥ 4.7.0): pass `concurrencyKey` (chat or tenant id) through `chat.createStartSessionAction("my-chat", { triggerConfig: { concurrencyKey: userId } })`. Without a key a session shares the task's keyless pool.
- From an MCP client use `list_agents`, `start_agent_chat`, `send_agent_message`, `close_agent_chat` and, for side channels, `read_session_channel` / `write_session_channel` (see **mcp-patterns**). Chats started that way live in the MCP server process.

## Common mistakes

- **Calling the `streamText` imported from `ai`.** It silently skips compaction, mid-turn steering, background injection, the managed system prompt, registry model resolution and telemetry. Use the one on the `run` argument, or spread `chat.toStreamTextOptions()` in a custom agent.
- **Not forwarding `signal`.** Without `abortSignal: signal`, Stop updates the UI but the model keeps generating.
- **Tools only on `streamText`.** Also declare them on `chat.agent({ tools })`.
- **Initialising `chat.local` in `onChatStart`.** Do it in `onBoot`; continuation runs skip `onChatStart`.
- **Minting tokens in the browser.** Only the two server actions touch the secret key.
- **Returning the raw error from `uiMessageStreamOptions.onError`.** It leaks internals; return a sanitized string.

## Sources

The SDK package ships version-exact docs and skills: `node_modules/@trigger.dev/sdk/docs/ai-chat/` and `node_modules/@trigger.dev/sdk/skills/` (`npx trigger.dev@latest skills` installs them as agent skills: trigger-authoring-chat-agent, trigger-chat-agent-advanced, ...). Online: https://trigger.dev/docs/ai-chat/overview and `/quick-start`.
