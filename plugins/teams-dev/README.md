# teams-dev

Microsoft Teams SDK dev plugin for Agents Store. TypeScript knowledge for building Teams bots, message extensions, tabs, dialogs and AI agents with **Teams SDK 2.1** (`@microsoft/teams.*` 2.1) and the **Teams Developer CLI 3** (`@microsoft/teams.cli`).

Version 2.0 is a rebuild: the plugin vendors the official `teams-dev` skill of [`microsoft/teams-sdk`](https://github.com/microsoft/teams-sdk) (MIT) for everything the CLI does — scaffold, bot registration, SSO setup, CLI troubleshooting — and keeps hand-written skills for the code, the deployment and the debugging that the official skill leaves to the docs.

## What's inside

- **17 skill directories**: 1 vendored official skill and 16 hand-written ones.
- **1 agent** (`teams-developer`) — routes multi-skill requests such as "AI bot with SSO that reads Graph data".
- **2 commands**:
  - `/teams-dev:scaffold <project> [echo|graph|tab]` — wraps `teams project new typescript`.
  - `/teams-dev:add-feature <feature>` — adds a message handler, card, dialog, extension, tab, AI agent, MCP or A2A, SSO, Graph call or turn state to an existing project.

## Official skill (vendored)

`skills/teams-sdk-teams-dev/` is a verbatim mirror of `plugins/teams-sdk/skills/teams-dev` in `microsoft/teams-sdk`, refreshed by `scripts/sync-teams-sdk-skills.sh` (weekly workflow `sync-teams-sdk-skills.yml`). Do not edit it here; the licence is in `LICENSE-teams-sdk`.

| Guide | Covers |
|---|---|
| [`references/guide-create-bot-app.md`](skills/teams-sdk-teams-dev/references/guide-create-bot-app.md) | Scaffold with `teams project new`, run, install, test |
| [`references/guide-create-bot-infra.md`](skills/teams-sdk-teams-dev/references/guide-create-bot-infra.md) | CLI install and login, tunnel, `teams app create`, verification |
| [`references/guide-integrate-existing-server.md`](skills/teams-sdk-teams-dev/references/guide-integrate-existing-server.md) | Adding Teams to an existing server |
| [`references/guide-setup-sso.md`](skills/teams-sdk-teams-dev/references/guide-setup-sso.md) | Azure bot migration, Entra app, OAuth connection, `webApplicationInfo` |
| [`references/troubleshooting.md`](skills/teams-sdk-teams-dev/references/troubleshooting.md) | Sideloading, login, SSO and migration errors |

## Skills

| Skill | When it triggers |
|---|---|
| `teams-sdk-teams-dev` | Official: CLI-driven scaffold, registration, SSO setup, CLI troubleshooting |
| `sdk-patterns` | `App`, turn state, routing, middleware, plugins, adapters, logging, Agent 365 telemetry |
| `messaging` | Send/reply/quote, targeted messages, quoted replies, streaming and its limits, proactive messages, files, reactions |
| `adaptive-cards` | Cards with the 2.x builders, `SubmitData` routing, validation, dynamic search (plus `references/card-builders.md`) |
| `dialogs` | `OpenDialogData`, `dialog.open.<id>`, `dialog.submit.<action>`, card and web dialogs, multi-step flows |
| `message-extensions` | Search and action commands, link unfurling, item selection, settings |
| `tabs` | `app.tab()`, `app.function()`, `@microsoft/teams.client`, TeamsJS, Nested App Authentication |
| `ai-agents` | The `openai` SDK with `runTools()`, streaming, history, clarification cards, AI label, feedback, citations |
| `mcp-a2a` | MCP client and server on `@modelcontextprotocol/sdk`, A2A hand-off on `@a2a-js/sdk` |
| `authentication` | App credentials and managed identity, `addOAuthFlow`, callbacks, several connections, manifest |
| `graph-integration` | `app.graph.call(endpoints…)`, a user-token `GraphClient`, beta endpoints, paging |
| `deployment` | Runtime configuration, endpoint, install and rollout, hosting, secret rotation, sovereign clouds |
| `cli-recipes` | The CLI 3 command tree, `--json` scripting, manifest and RSC edits |
| `agents-playground` | Local testing with the Microsoft 365 Agents Playground |
| `troubleshoot` | No reply, 401/403, install errors, SSO failures, cards, streaming, manifest checks |
| `examples` | Echo bot, AI quote agent, card form, message-extension search, SSO + Graph |
| `api-reference` | Packages, `App` options, routes (explicit invocation only — `disable-model-invocation: true`) |

## What's new in Teams SDK 2.1

Each item points to where this plugin covers it.

1. **Per-turn state** — `new App({ state: true })` gives every handler a conversation and a user scope; no more module-level `Map`s for histories and references. `sdk-patterns` (section 2), used by `messaging` and `ai-agents`.
2. **`app.addOAuthFlow(name)`** — several OAuth connections in one app, sign-in callbacks, resuming the original request. `authentication`; the Azure side is the vendored `guide-setup-sso.md`.
3. **Targeted messages and quoted replies** — `withRecipient(user, true)`, `reply`/`quote`, `addQuote`; streaming limits (1:1 only, one stream per chat, two minutes) with a hand-off to message updates. `messaging`.
4. **Socket Mode** — announced as experimental, but not present in the published `@microsoft/teams.apps` 2.1.0 (checked against the package). Not documented here until it ships.
5. **Agent 365, agentic identity and OpenTelemetry** — `app.getAgenticIdentity()`, the `telemetry` option, `app.tokenProvider`; receiving files with `contentUrl`; `@microsoft/teams.m365extensions`. `sdk-patterns` (section 7), `messaging`, `api-reference`.

## Prerequisites

- **Node 22.12 or newer.**
- A Microsoft 365 tenant that allows custom app upload (a Developer Program tenant is the easiest route). `teams status` shows the tenant and user policy.
- The CLI, stable line: `npm install -g @microsoft/teams.cli`. Update with `teams self-update`.
- A tunnel for Teams to reach localhost: Dev Tunnels (`devtunnel`), ngrok or Cloudflare. Not needed with the Agents Playground.
- Optional: Azure CLI (`az`) and a subscription for Azure bots, OAuth and SSO; an `OPENAI_API_KEY` or `AZURE_OPENAI_*` settings for the AI skills.

## Changed in 2.0

- Rebuilt for Teams SDK 2.1 and CLI 3; Node 22.12 or newer.
- Skills `setup`, `getting-started` and the bot-infrastructure and SSO reference files are replaced by the vendored official skill. `devtools` became `agents-playground`; `mcp-plugin` became `mcp-a2a`.
- No Teams SDK AI, MCP, A2A or DevTools packages — they are deprecated; the skills teach the `openai`, `@modelcontextprotocol/sdk` and `@a2a-js/sdk` packages directly and the Agents Playground.
- Credentials are `CLIENT_ID`, `CLIENT_SECRET` and `TENANT_ID`.

## Installation

Install through the Agents Store marketplace (`/plugin marketplace …`) or clone this repository and enable the plugin locally.

## Credits

The skill `teams-sdk-teams-dev` is © Microsoft Corporation, MIT licence (`LICENSE-teams-sdk`). The other skills draw on the official documentation of the Teams SDK, `https://microsoft.github.io/teams-sdk/llms_docs/llms_typescript_full.txt`.
