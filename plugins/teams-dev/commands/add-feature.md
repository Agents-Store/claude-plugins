---
description: Add a feature (message handler, Adaptive Card, dialog, message extension, tab, AI agent, MCP plugin, SSO, Graph call) to an existing Microsoft Teams app
argument-hint: <feature>
allowed-tools: ["Bash", "Read", "Write", "Edit", "Grep", "Glob", "Skill"]
---

# /teams-dev:add-feature

Adds an incremental feature to an existing Microsoft Teams app built on `@microsoft/teams.*`. The argument selects the feature to add.

## Feature router

Match `$ARGUMENTS` (case-insensitive, hyphens and spaces interchangeable):

| Argument | Skill to invoke | Outcome |
|---|---|---|
| `message`, `message-handler`, `bot` | `messaging` | New `app.on('message', …)` handler with reply/typing patterns |
| `card`, `adaptive-card` | `adaptive-cards` | Build a card with `AdaptiveCard` + `cardAttachment('adaptive', card)` |
| `dialog`, `task-module` | `dialogs` | `dialog.open.<id>` + `dialog.submit.<id>` handlers |
| `message-extension`, `compose-extension`, `me` | `message-extensions` | `message.ext.query` and/or `submit` handlers + manifest changes |
| `tab`, `static-tab` | `tabs` | `app.tab('name', path)` and client-side SDK wiring |
| `ai`, `ai-agent`, `chat-prompt` | `ai-agents` | `ChatPrompt` + `OpenAIChatModel` and message-handler integration |
| `mcp`, `mcp-server`, `mcp-client` | `mcp-plugin` | `@microsoft/teams.mcp` server registration or client config |
| `sso`, `auth`, `signin` | `authentication` | Token-exchange + verify-state handlers, manifest scope update |
| `graph`, `microsoft-graph` | `graph-integration` | `api.graph.*` call with user-or-app token |

If no argument matches, ask the user which of these to add — do not guess.

## Steps

1. Glob the project: `Read` `package.json`, `src/index.ts` (or `src/main.ts`), and `appPackage/manifest.json`.
2. Invoke the matching skill from the table.
3. Propose a minimal diff. Do not refactor untouched code.
4. After applying the diff, run `npx tsc --noEmit` to catch type errors before suggesting `npm run dev`.

## Notes

- Always re-read `src/index.ts` before editing — the user may have customised `new App({ … })` options.
- For features that touch the manifest (`bot`, `message-extension`, `tab`, `sso`), update `appPackage/manifest.json` and remind the user that sideloading must be re-run with `teams app update`.
- Streaming responses only work in 1:1 chats; in channels/groups, emit the full response at the end. Flag this when adding `ai-agent`.
