# stack-directus-nextjs-trigger

Directus + Next.js + Trigger.dev architecture plugin for Agents Store. It describes how Directus (content, files, access), a Next.js App Router frontend and self-hosted Trigger.dev (durable and scheduled work) fit together: who holds which token, how the cache is invalidated when content or a task changes it, how a Directus change reaches a task and the result reaches the page, who owns the user session, and what to check before production. It names its parts in `dependencies`; what one tool does and how to drive it is taught by that tool's own plugin.

## Architecture

| Layer | Service | Role |
|-------|---------|------|
| Data | Directus | Content, REST API, file storage, users and policies, Flows |
| Interface + Logic | Next.js | App Router, Server Components, Server Actions, Route Handlers |
| Work | Trigger.dev (self-hosted) | Durable tasks: retries, schedules, AI calls, long-running and bulk work, on its own workers |

Next.js keeps the synchronous work (rendering, actions, webhook receivers). Anything slow, flaky or scheduled leaves it as a task that retries, can be observed, and writes its result back to Directus.

The boundaries between them are what this plugin owns:

| Boundary | Rule |
|----------|------|
| Token | The Next.js server holds a service token of a dedicated Directus user; a task holds the token of its **own** Directus user; the browser holds nothing of Directus |
| Cache | Every Directus read is tagged with its collection; a Directus Flow (or a task) expires the tag through a Route Handler |
| Assets | A file URL never carries a token: public files, or a server route that adds the token |
| Types | `types/directus.ts` follows the Directus schema, the tasks import it too, and `tsc` is the drift check |
| Session | One owner of the end-user session, chosen once (see `authentication`) |
| Task payload | Ids and `requestedBy`, never a token and never a copy of the item |
| Task environment | A task sees only the variables of its Trigger.dev project, never the Next.js host's |
| Browser to task | Only the run-scoped public token and the server address; never `TRIGGER_SECRET_KEY` |

Deployment of the Next.js app is handled by a separate plugin (for example `dokploy-dev`, `vercel-dev`); tasks deploy separately with the Trigger.dev CLI.

## Dependencies

Declared in `plugin.json` and installed together with the stack. They hold the tool-level knowledge:

| Plugin | Teaches |
|--------|---------|
| `directus-dev` | Directus MCP tools, REST API, `@directus/sdk` (`sdk-patterns`, including server-side use), local Docker Compose (`docker-local-dev`), Flows (`flow-automation`, including the Flow that sends item keys to a worker), schema design |
| `nextjs-dev` | App Router, data fetching and caching (`data-fetching`), authentication (`auth-patterns`), `proxy.ts`, images, Cache Components |
| `trigger-dev` | Tasks, retries, queues, debounce and idempotency (`task-development`), schedules (`scheduled-tasks`), tokens and hooks for the browser (`realtime`), deploys and CI (`deployment`), CLI, MCP tools, self-hosted infrastructure |

`nextjs-provision` (shadcn/ui setup) is optional: install it separately if you want it. Pick the plugin that matches your hosting for deployment (`dokploy-dev`, `vercel-dev`).

More from `trigger-dev` that fits this stack once the basics work: a human approval step in a pipeline (`wait.createToken` plus a status field in Directus, completed from the browser with `useWaitToken`; `realtime`), AI chat agents as tasks (`ai-chat-agents`), and run and cost analysis with TRQL (`observability`).

## Prerequisites

- Directus 12 (MCP needs 11.12 or later and is switched on in Settings → AI)
- Next.js 16, `next@^16.3.8`
- Node.js 22 or later (`@directus/sdk` 26 requires it)
- A self-hosted Trigger.dev 4.x server (webapp and supervisor running); `@trigger.dev/sdk`, `@trigger.dev/react-hooks` and the `trigger.dev` CLI at the **version of the server**
- Docker, for a local Directus

## Installation

```bash
claude plugin install stack-directus-nextjs-trigger@agents-store-claude-plugins
```

The three technology plugins above come with it. Copies installed under the plugin's former name move to this one through the marketplace `renames` map; update `enabledPlugins` entries and any skill reference that still uses the old name (see `LEARNINGS.md`).

## MCP Servers

This plugin's `.mcp.json` connects Claude to Directus and to Trigger.dev. Tools are named `mcp__plugin_stack-directus-nextjs-trigger_directus__<tool>` and `mcp__plugin_stack-directus-nextjs-trigger_trigger-dev__<tool>`.

| Server | Transport | Address |
|--------|-----------|---------|
| `directus` | HTTP | `${NEXT_PUBLIC_DIRECTUS_URL}/mcp` with `Bearer ${DIRECTUS_ADMIN_TOKEN}` |
| `trigger-dev` | stdio | `npx trigger.dev@${TRIGGER_CLI_VERSION:-latest} mcp --dev-only --project-ref ${TRIGGER_PROJECT_REF}`, with `TRIGGER_ACCESS_TOKEN` and `TRIGGER_API_URL` |

- Directus MCP acts with the permissions of the token's user, so a token of a dedicated user with a narrow policy also narrows what the model can change.
- Trigger.dev MCP runs with `--dev-only`: every tool that takes an environment answers only for `dev`, and `deploy` and the deploy and preview-branch listings are refused. It keeps `trigger_task`, so the agent can start a test run. Drop the flag to reach production, or add `--readonly` to hide the write tools (`trigger_task` included).
- Set `TRIGGER_CLI_VERSION` to the version of your server so the MCP server runs the matching CLI; the default is `latest`.
- `${VAR}` in `.mcp.json` is expanded from the environment Claude Code runs in (your shell, or the `env` block of `.claude/settings.local.json`), not from `.env.local`.

## Environment Variables

Copy `templates/.env.example` to your project root as `.env.local` (Next.js), and `templates/.env.trigger.example` to `.env.trigger.local` (the tasks, for `trigger dev`):

| Variable | Purpose | Client-side |
|----------|---------|-------------|
| `NEXT_PUBLIC_DIRECTUS_URL` | Directus address | Yes |
| `DIRECTUS_ADMIN_TOKEN` | Static token of a dedicated Directus user (the name is historical; an administrator token is for local development only) | No |
| `DIRECTUS_URL`, `DIRECTUS_TOKEN`, `NEXT_PUBLIC_CMS_URL` | The names the `directus-dev` and `nextjs-dev` recipes read. In `.env.local` they expand to the two variables above (`DIRECTUS_URL=${NEXT_PUBLIC_DIRECTUS_URL}`, `DIRECTUS_TOKEN=${DIRECTUS_ADMIN_TOKEN}`, `NEXT_PUBLIC_CMS_URL=${NEXT_PUBLIC_DIRECTUS_URL}`); without them the NextAuth login calls `undefined/auth/login` and the images config fails | `NEXT_PUBLIC_CMS_URL`: yes |
| `NEXT_PUBLIC_SITE_URL` | Address of this site (RSS, metadata, the call a task makes to `/api/revalidate`) | Yes |
| `NEXTAUTH_URL`, `NEXTAUTH_SECRET` | NextAuth (NextAuth path only) | No |
| `REVALIDATION_SECRET` | Shared secret for `/api/revalidate`, sent in a header by a Directus Flow and by tasks that call the route | No |
| `DIRECTUS_WEBHOOK_SECRET` | Shared secret for `/api/directus-webhook/*`, sent in a header by the Flow that starts a task. A different value from `REVALIDATION_SECRET` | No |
| `PUBLIC_ASSET_FOLDER_ID` | Directus folder whose files the asset proxy may serve (proxy path only) | No |
| `TRIGGER_API_URL` | Address of the self-hosted server. Set wherever `tasks.trigger()` runs: without it the SDK falls back to Trigger.dev Cloud | No |
| `TRIGGER_SECRET_KEY` | Environment secret key (`tr_dev_...` for dev). The SDK in the Next.js server triggers tasks with it | No |
| `TRIGGER_ACCESS_TOKEN` | Personal Access Token (`tr_pat_...`) for the MCP server and `trigger deploy` | No |
| `TRIGGER_PROJECT_REF` | Project ref (`proj_...`) | No |
| `NEXT_PUBLIC_TRIGGER_API_URL` | The server address for browser hooks (`baseURL`); expands to `${TRIGGER_API_URL}` in `.env.local` | Yes |
| `TRIGGER_CLI_VERSION` | Optional: the version of your server, for the MCP server's CLI | No |

> **Two Trigger.dev credentials.** `TRIGGER_SECRET_KEY` is the environment secret key the SDK uses to trigger tasks. `TRIGGER_ACCESS_TOKEN` is a Personal Access Token (dashboard → Account → Personal Access Tokens) for the MCP server and the CLI: the MCP server's account-level tools reject environment keys. The PAT's user must be a member of the organization that owns `TRIGGER_PROJECT_REF`.

> **Tasks have their own variables.** `.env.trigger.local` (for `trigger dev`) and the Trigger.dev project environment (deployed) hold `DIRECTUS_URL`, `DIRECTUS_TOKEN` (the task user's token), and any third-party key. The Trigger.dev CLI loads dotenv files but does not expand `${VAR}`, so the `.env.local` aliases would reach a task as literal text.

## Skills

| Skill | Description |
|-------|-------------|
| `init-project` | Versions, environment, dependencies, client and types, the Trigger.dev project, verification of the three connections |
| `directus-to-nextjs` | The Directus to Next.js boundary: token, cache, assets, types |
| `authentication` | Who owns the user session and the tokens; three paths; why a user's token never goes into a task |
| `deployment` | Local run, the four pipelines, environment variables per service, task deploys, production checklist |
| `background-tasks` | The Next.js to Trigger.dev boundary: what to offload, what crosses, starting a task from an action, handing the run to the browser, closing the loop |
| `directus-to-trigger` | Directus Flow to receiver to task to write-back: the Flow's values, the receiver, the task-side client, loop guards |
| `full-feature` | Step-by-step recipe for building a feature across the three layers |
| `examples` | Scenario walkthroughs (blog, product catalog, AI enrichment pipeline, scheduled data sync) |

## Agent

**stack-orchestrator**: Coordinates work across Directus, Next.js and Trigger.dev: content pages, the session, revalidation, tasks started by users, Directus changes or the clock, and cross-service debugging.
