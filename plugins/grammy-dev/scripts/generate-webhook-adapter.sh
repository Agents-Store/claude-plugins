#!/usr/bin/env bash
# generate-webhook-adapter.sh — emit a webhookCallback adapter for the chosen framework.
# Usage: generate-webhook-adapter.sh <framework> <out-file>
# framework ∈ {express, fastify, hono, cloudflare, vercel}
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <express|fastify|hono|cloudflare|vercel> <out-file>" >&2
  exit 2
fi

framework="$1"
out="$2"

mkdir -p "$(dirname "$out")"

case "$framework" in
  express)
    cat > "$out" <<'TS'
import express from "express";
import { webhookCallback } from "grammy";
import { bot } from "./bot.js";

const app = express();
app.use(express.json());

const secretPath = String(process.env.BOT_TOKEN);
app.use(`/${secretPath}`, webhookCallback(bot, "express"));

const port = Number(process.env.PORT) || 3000;
app.listen(port, async () => {
  console.log(`webhook server listening on :${port}`);
  if (process.env.DOMAIN) {
    await bot.api.setWebhook(`https://${process.env.DOMAIN}/${secretPath}`, {
      drop_pending_updates: true,
    });
    console.log(`webhook set: https://${process.env.DOMAIN}/${secretPath}`);
  }
});
TS
    ;;

  fastify)
    cat > "$out" <<'TS'
import { fastify } from "fastify";
import { webhookCallback } from "grammy";
import { bot } from "./bot.js";

const server = fastify();
server.post(`/${bot.token}`, webhookCallback(bot, "fastify"));

const port = Number(process.env.PORT) || 3000;
await server.listen({ port, host: "0.0.0.0" });
console.log(`webhook server listening on :${port}`);

if (process.env.DOMAIN) {
  await bot.api.setWebhook(`https://${process.env.DOMAIN}/${bot.token}`, {
    drop_pending_updates: true,
  });
  console.log(`webhook set: https://${process.env.DOMAIN}/${bot.token}`);
}
TS
    ;;

  hono)
    cat > "$out" <<'TS'
import { Hono } from "hono";
import { webhookCallback } from "grammy";
import { bot } from "./bot.js";

const app = new Hono();
app.post(`/${bot.token}`, webhookCallback(bot, "hono"));

export default app;
// For Node: import { serve } from "@hono/node-server"; serve({ fetch: app.fetch, port: 3000 });
// For Bun:  export default app; // bun run src/server.ts
TS
    ;;

  cloudflare)
    cat > "$out" <<'TS'
import { Bot, type Context, webhookCallback } from "grammy";

export interface Env {
  BOT_TOKEN: string;
  BOT_INFO: string;          // JSON of bot.getMe() — cached to skip cold-start round-trip
  WEBHOOK_SECRET?: string;
}

export default {
  async fetch(request: Request, env: Env, _ctx: ExecutionContext): Promise<Response> {
    if (env.WEBHOOK_SECRET) {
      const got = request.headers.get("X-Telegram-Bot-Api-Secret-Token");
      if (got !== env.WEBHOOK_SECRET) return new Response("forbidden", { status: 403 });
    }

    const bot = new Bot(env.BOT_TOKEN, { botInfo: JSON.parse(env.BOT_INFO) });

    bot.command("start", (ctx: Context) => ctx.reply("Hello from Cloudflare Workers"));
    bot.on("message:text", (ctx) => ctx.reply(`You said: ${ctx.message.text}`));

    bot.catch((err) => console.error("bot error", err));

    return webhookCallback(bot, "cloudflare-mod")(request);
  },
};
TS
    ;;

  vercel)
    cat > "$out" <<'TS'
// place this file at api/bot.ts in a Vercel project
import { Bot, webhookCallback } from "grammy";

const bot = new Bot(process.env.BOT_TOKEN!);

bot.command("start", (ctx) => ctx.reply("Hello from Vercel"));
bot.on("message:text", (ctx) => ctx.reply(`You said: ${ctx.message.text}`));
bot.catch((err) => console.error("bot error", err));

export default webhookCallback(bot, "vercel");
TS
    ;;

  *)
    echo "error: unknown framework '$framework'. valid: express, fastify, hono, cloudflare, vercel" >&2
    exit 2
    ;;
esac

echo "Wrote $out (framework: $framework)"
echo "Next:"
case "$framework" in
  cloudflare) echo "  wrangler secret put BOT_TOKEN && wrangler secret put BOT_INFO && wrangler deploy" ;;
  vercel)     echo "  vercel deploy" ;;
  *)          echo "  curl \"https://api.telegram.org/bot\$BOT_TOKEN/setWebhook?url=https://\$DOMAIN/\$BOT_TOKEN\"" ;;
esac
