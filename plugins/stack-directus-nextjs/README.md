# stack-directus-nextjs

Directus + Next.js architecture plugin for Agents Store. It describes how Directus (content, files, access) and a Next.js App Router frontend fit together: who holds which token, how the cache is invalidated when content changes, how assets and types cross the boundary, who owns the user session, and what to check before production. It names its parts in `dependencies`; what one tool does and how to drive it is taught by that tool's own plugin.

## Architecture

| Layer | Service | Role |
|-------|---------|------|
| Data | Directus | Content, REST API, file storage, users and policies |
| Interface + Logic | Next.js | App Router, Server Components, Server Actions, Route Handlers |

The boundary between them is what this plugin owns:

| Boundary | Rule |
|----------|------|
| Token | The server holds a service token of a dedicated Directus user; the browser holds nothing of Directus |
| Cache | Every Directus read is tagged with its collection; a Directus Flow expires the tag through a Route Handler |
| Assets | A file URL never carries a token: public files, or a server route that adds the token |
| Types | `types/directus.ts` follows the Directus schema, and `tsc` is the drift check |
| Session | One owner of the end-user session, chosen once (see `authentication`) |

Deployment is handled by a separate plugin (for example `dokploy-dev`, `vercel-dev`).

## Dependencies

Declared in `plugin.json` and installed together with the stack. They hold the tool-level knowledge:

| Plugin | Teaches |
|--------|---------|
| `directus-dev` | Directus MCP tools, REST API, `@directus/sdk` (`sdk-patterns`, including server-side use), local Docker Compose (`docker-local-dev`), flows (`flow-automation`), schema design |
| `nextjs-dev` | App Router, data fetching and caching (`data-fetching`), authentication (`auth-patterns`), `proxy.ts`, images, Cache Components |

`nextjs-provision` (shadcn/ui setup) is optional: install it separately if you want it. Pick the plugin that matches your hosting for deployment (`dokploy-dev`, `vercel-dev`).

## Prerequisites

- Directus 12 (MCP needs 11.12 or later and is switched on in Settings → AI)
- Next.js 16, `next@^16.3.8`
- Node.js 22 or later (`@directus/sdk` 26 requires it)
- Docker, for a local Directus

## Installation

```bash
claude plugin install stack-directus-nextjs@agents-store-claude-plugins
```

The two technology plugins above come with it.

## MCP Server

This plugin's `.mcp.json` connects Claude to Directus. Tools are named `mcp__plugin_stack-directus-nextjs_directus__<tool>` (`schema`, `collections`, `fields`, `items`, `files`, `flows` and the rest of the Directus MCP surface).

| Server | Transport | Address |
|--------|-----------|---------|
| `directus` | HTTP | `${NEXT_PUBLIC_DIRECTUS_URL}/mcp` with `Bearer ${DIRECTUS_ADMIN_TOKEN}` |

MCP acts with the permissions of the token's user, so a token of a dedicated user with a narrow policy also narrows what the model can change.

## Environment Variables

Copy `templates/.env.example` to your project root as `.env.local`:

| Variable | Purpose | Client-side |
|----------|---------|-------------|
| `NEXT_PUBLIC_DIRECTUS_URL` | Directus address | Yes |
| `DIRECTUS_ADMIN_TOKEN` | Static token of a dedicated Directus user (the name is historical; an administrator token is for local development only) | No |
| `NEXTAUTH_URL` | NextAuth base URL (NextAuth path only) | No |
| `NEXTAUTH_SECRET` | NextAuth encryption secret (NextAuth path only) | No |
| `REVALIDATION_SECRET` | Shared secret for `/api/revalidate`, sent by a Directus Flow in a header | No |
| `PUBLIC_ASSET_FOLDER_ID` | Directus folder whose files the asset proxy may serve (proxy path only) | No |

## Skills

| Skill | Description |
|-------|-------------|
| `init-project` | Versions, environment, dependencies, client and types, verification |
| `directus-to-nextjs` | The boundary: token, cache, assets, types |
| `authentication` | Who owns the user session and the tokens; three paths |
| `deployment` | Local development pointers, the revalidation pipeline, production checklist |
| `full-feature` | Step-by-step recipe for building a feature across both layers |
| `examples` | Scenario walkthroughs (blog, product catalog) |

## Agent

**stack-orchestrator** — Coordinates work across Directus and Next.js: content pages, the session, revalidation, and cross-service debugging.
