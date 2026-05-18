# teams-dev

Microsoft Teams SDK dev plugin for Agents Store. TypeScript-first knowledge plugin for building Teams bots, message extensions, tabs, dialogs, and AI agents using the official `@microsoft/teams.*` packages.

## What's inside

- **17 skills** covering setup, getting started, the SDK API surface, messaging, Adaptive Cards, dialogs, message extensions, tabs, AI agents, MCP/A2A, authentication, Microsoft Graph, deployment, the `teams` CLI, DevTools, troubleshooting, and end-to-end scenarios.
- **1 agent** (`teams-developer`) — routes complex multi-skill requests (e.g. "AI bot with SSO that reads Graph data").
- **2 commands**:
  - `/teams-dev:scaffold <project> [template]` — wraps `teams project new typescript`.
  - `/teams-dev:add-feature <feature>` — adds a message handler, card, dialog, extension, tab, AI agent, MCP plugin, SSO, or Graph call to an existing project.

## Skills

| Skill | When it triggers |
|---|---|
| `setup` | Verifying Node/Teams CLI installs, prerequisites |
| `getting-started` | First Teams project, `teams project new`, running locally |
| `api-reference` | Quick lookup of `@microsoft/teams.*` packages, classes, methods (explicit invocation only — `disable-model-invocation: true`) |
| `sdk-patterns` | App boot, plugin registration, middleware, activity routing |
| `messaging` | Send/reply, typing indicators, mentions, threads, streaming, proactive messages |
| `adaptive-cards` | Building cards with the TS builders; integrating with the Adaptive Card Designer |
| `dialogs` | Task module dialogs (`dialog.open.*`, `dialog.submit.*`) — card and web variants |
| `message-extensions` | Search and action commands, link unfurling, item selection |
| `tabs` | Static-hosted tabs via `app.tab()`, Teams client-side SDK |
| `ai-agents` | `ChatPrompt`, `OpenAIChatModel`, function calling, streaming, A2A |
| `mcp-plugin` | `@microsoft/teams.mcp` server + client, integrating MCP into chats |
| `authentication` | App auth, user auth (OAuth/SSO), Nested App Authentication, MSAL |
| `graph-integration` | Calling Microsoft Graph through `api.graph` with the right token |
| `deployment` | Sideloading, devtunnel/ngrok, sovereign clouds, production hosts |
| `cli-recipes` | `teams` CLI commands: `project new`, `app list/get/update`, `status`, `self-update` |
| `devtools` | `DevtoolsPlugin`, the `:3979/devtools` inspector, debugging activities |
| `troubleshoot` | Sideload errors, auth failures, SSO mismatches, endpoint mismatches |
| `examples` | End-to-end scenario walkthroughs: echo bot, AI quote agent, card form, MX search, SSO+Graph |

## Prerequisites

- Node 18+ (Node 20+ recommended).
- A Microsoft 365 tenant with sideloading allowed (a Developer Program tenant is the easiest route).
- `@microsoft/teams.cli` (preview): `npm i -g @microsoft/teams.cli@preview`.
- A devtunnel or ngrok account (for HTTPS callbacks to localhost during development).
- Optional: Azure subscription (for SSO / Graph), `OPENAI_API_KEY` or `AZURE_OPENAI_*` env vars (for AI skills).

## Installation

Install via the Agents Store marketplace (`/plugin marketplace …`) or clone this repo and enable the plugin locally.

## Credits

Initial reference guides inspired by the public `microsoft/teams-sdk` MIT plugin and the SDK's own LLM reference at `https://microsoft.github.io/teams-sdk/llms_docs/llms_typescript_full.txt`.
