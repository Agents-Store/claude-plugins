# grammy-dev

Claude Code plugin that turns Claude into a **grammY** specialist for building Telegram bots in Node.js, Deno, or TypeScript.

grammY is the modern Telegram Bot framework — see https://grammy.dev. This plugin gives Claude authoritative knowledge of grammY's bot core, filter-query DSL, middleware system, all official `@grammyjs/*` plugins, and deployment patterns across every supported hosting platform.

## What you get

**15 skills** (auto-trigger from natural-language requests):

| Skill | Triggers on |
|---|---|
| `setup` | "install grammY", "create my first Telegram bot", "verify bot token" |
| `sdk-patterns` | "use grammY Bot class", "send a message", "context object" |
| `filter-queries` | "bot.on filter", "listen for photos", "filter query DSL" |
| `middleware` | "bot.use", "Composer", "middleware ordering" |
| `error-handling` | "bot.catch", "GrammyError", "error boundary" |
| `commands-and-keyboards` | "slash command", "inline keyboard", "callback query" |
| `sessions` | "session plugin", "store user state", "Redis session", "lazy session" |
| `conversations` | "@grammyjs/conversations", "multi-step wizard", "form input" |
| `files-and-media` | "send photo", "InputFile", "download file" |
| `plugins-catalog` | "grammY plugins list", "hydrate", "i18n", "menu plugin" |
| `scaling-runner` | "@grammyjs/runner", "throttler", "auto-retry", "concurrency" |
| `deployment-hosting` | "webhook vs polling", "deploy to Cloudflare Workers", "Vercel", "VPS" |
| `payments-business-games` | "Telegram Stars", "sendInvoice", "Business connection", "games" |
| `api-reference` (manual) | curated Bot API method reference, opens on explicit ask |
| `troubleshoot` | "401 Unauthorized", "Conflict", "bot not responding" |
| `examples` | "show a complete grammY example" — opens scenario library |

**1 agent**: `grammy-developer` — invokes when the user wants help writing actual grammY code (`/start` handlers, webhook adapters, plugin integration).

**2 bundled scripts** (under `scripts/`):

- `init-bot.sh <dir>` — scaffolds a fresh TypeScript grammY project (`package.json`, `tsconfig.json`, `src/bot.ts`, `.env.example`, `.gitignore`).
- `generate-webhook-adapter.sh <framework> <out-file>` — emits a `webhookCallback` adapter for `express`, `fastify`, `hono`, `cloudflare`, or `vercel`.

## Install

This plugin lives in the **AGENTS.STORE Public Plugins** marketplace.

```text
/plugin install grammy-dev
```

No environment variables. No `.mcp.json`. Pure knowledge plugin.

## Prerequisites

- Node.js 18+ (or Deno 1.40+) for actually running a bot you build.
- A bot token from [@BotFather](https://t.me/BotFather) for your bot.

Claude doesn't need either to give you grammY code — the prerequisites are for your bot, not the plugin.

## Out of scope

- This plugin teaches Claude how to *build* a Telegram bot. To *operate* a Telegram user account programmatically (read DMs, send messages from a user phone number), use the `tg-client` plugin instead.
- This plugin does not bundle any MCP server. grammY is a code framework — it does not run a hosted service Claude can call.

## License

MIT.
