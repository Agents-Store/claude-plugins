# LEARNINGS — teams-dev

Accumulated fixes and discoveries for the `teams-dev` plugin.

## 2026-05-18 — initial scaffold

**Note:** The five reference guides under `skills/{authentication,deployment,troubleshoot}/references/` and `skills/getting-started/SKILL.md` were originally inspired by the public reference guides shipped in `microsoft/teams-sdk@main/plugins/teams-sdk` (MIT). Content has been rewritten for the Agents Store style, restricted to TypeScript only (no C#/Python sections), and synchronised with the official SDK reference at `https://microsoft.github.io/teams-sdk/llms_docs/llms_typescript_full.txt`.

## 2026-10-03 — whole plugin: rebuilt on the official `microsoft/teams-sdk` skill (2.0.0)

**Problem:** The plugin taught the early v2 preview. Against Teams SDK 2.1.0 / CLI 3.0.3 it was wrong in almost every file: five AI/MCP/A2A packages (`teams.ai`, `teams.openai`, `teams.mcp`, `teams.mcpclient`, `teams.a2a`) and `teams.dev` are deprecated on npm; Node 18+ instead of 22.12+; `@preview` CLI install; `teams auth login`, `teams doctor`, `teams logs`, `teams app delete`, `teams app credentials rotate` do not exist in CLI 3; `BOT_ID`/`BOT_PASSWORD` instead of `CLIENT_ID`/`CLIENT_SECRET`/`TENANT_ID`; card builders (`addBody`, `addActions`, `fromJSON`, `new TextInput('id')`), `addAttachment`, `Mention`, `api.graph`, `api.tokens`, `OAuthCard`, `ExpressAdapter` from a sub-path, `FastifyAdapter`, `app.handler`, `app.use((ctx, next))` and the cloud presets from `teams.apps` all fail to compile against 2.1.0.
**Fix:** Owner decision of 2026-10-02: rebase on the official plugin. `scripts/sync-teams-sdk-skills.sh` vendors `plugins/teams-sdk/skills/*` of `microsoft/teams-sdk` (MIT, upstream commit 5d99377) as `skills/teams-sdk-*` and copies the licence to `LICENSE-teams-sdk`. The hand-written skills were kept only where upstream does not cover them and were rewritten against the published 2.1.0 types (every `ts` snippet was type-checked with `tsc --noEmit` against `@microsoft/teams.apps|api|cards|graph|graph-endpoints|client` 2.1.0, `openai`, `@modelcontextprotocol/sdk`, `@a2a-js/sdk`).
**Root cause:** The plugin froze an LLM reference of 2026-05-18 and carried no versions, so nothing flagged the drift.
**Severity:** Critical

Covered by upstream, removed: `setup` (CLI install, login, prerequisites), `getting-started` (scaffold, tunnel, run, install), `deployment/references/bot-infra-setup.md` (bot registration), `authentication/references/sso-setup.md` (Azure-side SSO; the CLI-driven guide replaces the manual portal steps), `api-reference/references/llms-typescript-full.md` (pointer to the same llms.txt URLs the upstream skill lists).

Not covered by upstream, kept and rewritten: `sdk-patterns`, `messaging`, `adaptive-cards`, `dialogs`, `message-extensions`, `tabs`, `ai-agents`, `authentication` (code side), `graph-integration`, `deployment` (the upstream skill states it does not cover hosting), `cli-recipes`, `troubleshoot` (code-level triage), `api-reference`, `examples`, the commands and the agent.

Renamed: `devtools` → `agents-playground` (the DevTools plugin is deprecated; the Microsoft 365 Agents Playground replaces it), `mcp-plugin` → `mcp-a2a` (there is no MCP plugin any more).

### Discoveries worth keeping

- **`teams project new typescript` templates.** The CLI docs list `ai, echo, graph, mcp, mcpclient, tab`, but the 3.0.3 package and the 3.1.0-preview.4 package both ship only `echo`, `graph` and `tab` under `templates/typescript` (checked in the npm tarballs); `-t ai` fails with "Unknown template". The skills tell the reader to trust `teams project new typescript --help`. The shipped `graph` template still uses the 2.0-style `oauth.defaultConnectionName` and `userGraph`.
- **Scaffolded projects have no manifest file.** `teams app create` keeps the manifest in the Developer Portal; edits go through `teams app manifest download|upload|update` and `teams app update`.
- **The unauthenticated-requests option.** Docs and the quickstart still say `skipAuth`; the 2.1.0 types mark it deprecated in favour of `dangerouslyAllowUnauthenticatedRequests` (env `DANGEROUSLY_ALLOW_UNAUTHENTICATED_REQUESTS`). With credentials configured the flag still bypasses token validation (the SDK logs a warning).
- **Socket Mode is not in 2.1.0.** The research notes of 2026-10-02 list `new App({ socketMode: true })`; the published `@microsoft/teams.apps` 2.1.0 has no such option (the code only hints at "connection-authenticated transports"). Not documented; re-check when it ships.
- **`@a2a-js/sdk` moved on.** The Teams docs page shows protocol 0.3 shapes; the `examples/a2a` sample and the current package (1.3.0) use protobuf-style messages. `mcp-a2a` documents the wiring only and tells the reader to pin a major and copy shapes from the sample.
- **`app.start()` reports start-up failures through the `error` event** instead of rejecting its promise (it stops the app and emits `error`); `.catch(console.error)` alone does not show them.
- **Graph endpoint bodies are strictly typed.** Nested complex types need an `'@odata.type'`, and `sendMail` takes its body under `Message`. Old snippets with plain objects do not compile.
- **Routes that do not exist in 2.1.0:** `message.reaction` (it is `messageReaction`), `message.update`, `message.delete`, `conversation.update`, `members.added`, `members.removed`, `message.ext.fetch-task` (it is `message.ext.open`), `task.complete`. Conversation updates are routed by `channelData.eventType` names (`teamMemberAdded`, …); message edits as `editMessage`, `undeleteMessage`, `softDeleteMessage`.
- **Cloud presets** (`US_GOV`, `US_GOV_DOD`, `CHINA`, `withOverrides`) are exported by `@microsoft/teams.api`, not `@microsoft/teams.apps`; a `cloud` in code beats the `CLOUD` variable.
- **Teams-managed bots cannot do OAuth or SSO**; `teams app bot migrate` moves them to Azure without changing client id, secret or tenant.

### Pending upstream (vendored `teams-sdk-teams-dev`)

- `references/guide-create-bot-app.md` lists the templates `echo`, `ai` and `graph`; the 3.0.x CLI ships `echo`, `graph` and `tab`.
- `references/guide-setup-sso.md` carries two public Teams client application ids, which the publication gate flags (baselined in `scripts/scrub-allow.txt`, never edited in the vendored file).

### Owner to verify

- `teams project new typescript <name> -t echo` and `-t graph`, then `npm install && npx tsc --noEmit` on Node 22.12+ with a real login (this session verified the shipped templates against 2.1.0 instead of running the CLI).
- The `graph` and `tab` templates against a real tenant, SSO end to end (`teams app doctor`), and the Agents Playground against a running bot.
- Streaming behaviour and the two-minute window in a Teams client; targeted messages in a group chat.
