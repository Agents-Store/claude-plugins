---
description: Add a feature (message handler, Adaptive Card, dialog, message extension, tab, AI agent, MCP server or client, A2A, SSO, Graph call, turn state) to an existing Microsoft Teams app on Teams SDK 2.1
argument-hint: <feature>
allowed-tools: ["Bash", "Read", "Write", "Edit", "Grep", "Glob", "Skill"]
---

# /teams-dev:add-feature

Adds an incremental feature to an existing Microsoft Teams app built on the `@microsoft/teams.*` 2.1 packages. The argument selects the feature.

## Feature router

Match `$ARGUMENTS` case-insensitively, hyphens and spaces interchangeable:

| Argument | Skill to invoke | Outcome |
|---|---|---|
| `message`, `message-handler`, `bot`, `proactive`, `stream` | `messaging` | A message handler with `send`/`reply`, streaming, targeted or proactive messages |
| `card`, `adaptive-card` | `adaptive-cards` | A card built with the 2.x builders and a `card.action.<action>` handler |
| `dialog`, `task-module` | `dialogs` | `dialog.open.<id>` and `dialog.submit.<action>` handlers |
| `message-extension`, `compose-extension`, `me` | `message-extensions` | `message.ext.*` handlers plus the manifest command |
| `tab`, `static-tab`, `function` | `tabs` | `app.tab()`, `app.function()` and the browser client |
| `ai`, `ai-agent`, `openai`, `llm` | `ai-agents` | The `openai` SDK with `runTools()`, streaming and history in turn state |
| `mcp`, `mcp-server`, `mcp-client`, `a2a` | `mcp-a2a` | `@modelcontextprotocol/sdk` or `@a2a-js/sdk` mounted next to the bot |
| `sso`, `auth`, `signin`, `oauth` | `authentication` | `app.addOAuthFlow()`, callbacks, manifest `webApplicationInfo` |
| `graph`, `microsoft-graph` | `graph-integration` | A Graph client with the app's or the user's token |
| `state`, `memory` | `sdk-patterns` (section 2) | `new App({ state: true })` and the conversation and user scopes |
| `test`, `playground` | `agents-playground` | Local testing without a registration |

If no argument matches, ask the user which of these to add — do not guess.

## Steps

1. Read `package.json` and `src/index.ts` (or `src/main.ts`). Confirm Node 22.12 or newer and `@microsoft/teams.apps` 2.1 or newer; if the project is on an older 2.0 preview line, say that the 2.x APIs in these skills need the upgrade first (`npm install @microsoft/teams.apps@latest` and the sibling packages).
2. Invoke the matching skill from the table; follow its code, not a remembered older API.
3. Propose a minimal diff. Do not refactor code the feature does not touch.
4. Type-check before suggesting a run:

   ```bash
   npx tsc --noEmit
   ```

5. Tell the user how to try it: the Agents Playground for message-level features (`agents-playground`), the Teams client for tabs, dialogs, extensions and sign-in.

## Notes

- Re-read `src/index.ts` before editing; the user may have customised `new App({ … })`.
- Features that touch the manifest (`message-extension`, `tab`, `sso`, dialogs that open web pages) change it through the CLI — `teams app manifest download|upload|update`, `teams app update` — not through a manifest file, because the scaffolded project has none (`Skill: cli-recipes`). The user reinstalls the app in Teams afterwards when the manifest changed.
- Streaming works in 1:1 chats only, one stream per chat, for two minutes from the first chunk. Flag this when adding `ai`.
- Add credentials and keys to `.env`, never to code, and keep `.env` out of git.
- SSO and OAuth need an Azure-managed bot; check with `teams app bot get <teamsAppId>` and offer `teams app bot migrate` if it is Teams-managed.
