# payloadcms-dev

Developer plugin for **PayloadCMS v3**. Packages Payload knowledge — collections, fields, hooks, access control, queries, adapters, Lexical, jobs queue, plugin development, Next.js integration, CLI, migrations, and end-to-end scenarios — so Claude Code can build with Payload confidently in any session.

## What's Inside

### 16 Skills

| Skill | When Claude triggers it |
| --- | --- |
| `setup` | Initial scaffolding, `payload.config.ts`, DB adapter selection, type generation. |
| `collections` | Designing `CollectionConfig` — slug, admin, auth, upload, versions, drafts, live preview. |
| `fields` | All field types, validation, virtual, conditional, blocks, join, with reference catalog. |
| `hooks` | Collection/field/global hooks, context flag, req threading, Next.js revalidation. |
| `access-control` | Collection/field/global access, RBAC, row-level Where filters, multi-tenant patterns. |
| `queries` | Operators, depth, populate, sort, AND/OR, Local/REST/GraphQL. |
| `adapters` | Postgres / MongoDB / SQLite, S3 / R2 / Vercel Blob, Resend / Nodemailer + transactions. |
| `lexical-editor` | Rich text customization — features, blocks, links/uploads, custom nodes, JSX rendering. |
| `jobs-queue` | Tasks, workflows, retries, cron schedules, in-process autoRun, external triggers. |
| `nextjs-integration` | App Router fetch, route groups, draft mode, live preview, ISR + revalidation, server actions. |
| `plugin-development` | Authoring `payload-plugin-*` packages: SWC build, hook preservation, multi-entry exports. |
| `cli-recipes` | `payload migrate`, `generate:types`, `generate:importmap`, `migrate:create/down/refresh`. |
| `troubleshoot` | Access bypass, hook loops, transaction breaks, type-gen failures, import-map errors. |
| `cms-migration` | Config-first workflow: WordPress / Contentful / Strapi / Sanity / Webflow → Payload. |
| `api-reference` | Local API method signatures, REST endpoints, GraphQL schema rules. (`disable-model-invocation`) |
| `examples` | 5 end-to-end scenarios: blog CMS, e-commerce, auth-only API, jobs worker, multi-tenant SaaS. |

### 1 Agent

**`payloadcms-developer`** — A Payload v3 specialist. Use it for multi-step work: designing collections + access + hooks together, debugging production issues across skills, authoring third-party plugins.

### 1 Command

**`/payloadcms-dev:scaffold [project-name]`** — Bootstraps a new Payload v3 project. Walks the user through DB adapter, template, and package manager, runs `create-payload-app`, then explains the generated `.env` and admin-first-user flow.

## Installation

This plugin lives in the AGENTS.STORE public marketplace. From any Claude Code session:

```
/plugin install payloadcms-dev
```

Or add the marketplace and install:
```
/plugin marketplace add https://github.com/AGENTS-STORE/claude-public-plugins
/plugin install payloadcms-dev@agents-store-claude-plugins
```

## Prerequisites

Once a Payload project is created with this plugin's `/scaffold` command, you'll need:

- **Node.js 20.9.0+** (LTS).
- **pnpm 9+**, npm 10+, yarn 4+, or bun 1+.
- A database: PostgreSQL, MongoDB (replica set for transactions), or SQLite/libSQL.
- Optional: object storage (S3 / R2 / Vercel Blob / Azure / UploadThing) for production uploads.
- Optional: an email provider (Resend, SMTP-compatible service via Nodemailer).

## Quick Start

Inside a Claude Code session with this plugin enabled:

```
/payloadcms-dev:scaffold my-payload-app
```

Then prompt-driven work:

- "Help me design collections for a blog with categories, tags, and authors."
- "Add a beforeChange hook that auto-slugifies titles."
- "Write access control so authors only see their own drafts."
- "Build a complete payload-plugin-cloudinary package."
- "My afterChange hook is firing in a loop — fix it."

Each prompt triggers the relevant topic skill automatically based on quoted phrases in the user's request.

## Architecture Notes

- **No `.mcp.json`** — PayloadCMS is self-hosted per-project. No public SaaS MCP exists, and stuffing a self-hosted URL into a shared plugin wouldn't work for other users. Each developer wires their own Payload instance via `pnpm dev`.
- **No `userConfig`** — Payload secrets like `PAYLOAD_SECRET`, `DATABASE_URI`, `S3_*`, `RESEND_API_KEY` belong in the project's `.env`, not in plugin-level config. They vary per project and per environment.
- **Knowledge-only plugin** — file-based skills, an agent, and one scaffolding command. No external services, no auto-running code.

## Source Material & Credits

This plugin adapts MIT-licensed content from the official [PayloadCMS skills repo](https://github.com/payloadcms/skills), then expands with material drawn from [payloadcms.com/docs](https://payloadcms.com/docs) and the [llms-full.txt](https://payloadcms.com/llms-full.txt) Payload provides for AI assistants. Adapted topics are re-organized into Agents Store's narrow-skill convention so each topic is independently triggerable.

## License

This plugin's structure and original prose: AGENTS.STORE conventions.
Adapted reference material from `payloadcms/skills`: MIT (see [LICENSE](https://github.com/payloadcms/skills/blob/main/LICENSE) upstream).

## Support

- Report skill issues or improvements: open an issue at the AGENTS.STORE marketplace repo or use `/plugin-creator:feedback`.
- Payload itself: [payloadcms.com](https://payloadcms.com) / [GitHub](https://github.com/payloadcms/payload) / [Discord](https://discord.com/invite/payload).
