#!/usr/bin/env bash
# generate-webhook-adapter.sh — emit a webhookCallback adapter for the chosen framework.
# Usage: generate-webhook-adapter.sh <framework> <out-file>
# framework ∈ {express, fastify, hono, cloudflare, https}
#   https  — Node's http/https handler, which is what Vercel Node.js functions expect.
#            grammY has no adapter named after Vercel; `vercel` is accepted as an alias.
# Every adapter reads an optional WEBHOOK_SECRET and hands it to webhookCallback's
# `secretToken` option, which verifies the X-Telegram-Bot-Api-Secret-Token header.
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <express|fastify|hono|cloudflare|https|vercel> <out-file>" >&2
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
const secretToken = process.env.WEBHOOK_SECRET;
app.use(`/${secretPath}`, webhookCallback(bot, "express", { secretToken }));

const port = Number(process.env.PORT) || 3000;
app.listen(port, async () => {
  console.log(`webhook server listening on :${port}`);
  if (process.env.DOMAIN) {
    await bot.api.setWebhook(`https://${process.env.DOMAIN}/${secretPath}`, {
      drop_pending_updates: true,
      secret_token: secretToken,
    });
    console.log("webhook registered");
  }
});
TS
    ;;

  fastify)
    cat > "$out" <<'TS'
import { fastify } from "fastify";
import { webhookCallback } from "grammy";
import { bot } from "./bot.js";

const secretToken = process.env.WEBHOOK_SECRET;

const server = fastify();
server.post(`/${bot.token}`, webhookCallback(bot, "fastify", { secretToken }));

const port = Number(process.env.PORT) || 3000;
await server.listen({ port, host: "0.0.0.0" });
console.log(`webhook server listening on :${port}`);

if (process.env.DOMAIN) {
  await bot.api.setWebhook(`https://${process.env.DOMAIN}/${bot.token}`, {
    drop_pending_updates: true,
    secret_token: secretToken,
  });
  console.log("webhook registered");
}
TS
    ;;

  hono)
    cat > "$out" <<'TS'
import { Hono } from "hono";
import { webhookCallback } from "grammy";
import { bot } from "./bot.js";

const app = new Hono();
app.post(
  `/${bot.token}`,
  webhookCallback(bot, "hono", { secretToken: process.env.WEBHOOK_SECRET }),
);

export default app;
// For Node: import { serve } from "@hono/node-server"; serve({ fetch: app.fetch, port: 3000 });
// For Bun:  export default app; // bun run src/server.ts
TS
    ;;

  cloudflare)
    cat > "$out" <<'TS'
// Needs the Workers runtime types for `ExecutionContext` (npm i -D @cloudflare/workers-types).
import { Bot, type Context, webhookCallback } from "grammy";

export interface Env {
  BOT_TOKEN: string;
  BOT_INFO: string;          // JSON of bot.getMe() — cached to skip cold-start round-trip
  WEBHOOK_SECRET?: string;
}

export default {
  async fetch(request: Request, env: Env, _ctx: ExecutionContext): Promise<Response> {
    const bot = new Bot(env.BOT_TOKEN, { botInfo: JSON.parse(env.BOT_INFO) });

    bot.command("start", (ctx: Context) => ctx.reply("Hello from Cloudflare Workers"));
    bot.on("message:text", (ctx) => ctx.reply(`You said: ${ctx.message.text}`));

    bot.catch((err) => console.error("bot error", err));

    // secretToken makes grammY check X-Telegram-Bot-Api-Secret-Token and answer 401 on mismatch
    return webhookCallback(bot, "cloudflare-mod", {
      secretToken: env.WEBHOOK_SECRET,
    })(request);
  },
};
TS
    ;;

  https|vercel)
    # grammY has no Vercel adapter. Vercel Node.js functions receive Node's (req, res) pair,
    # which is exactly what the "https" adapter handles.
    cat > "$out" <<'TS'
// place this file at api/bot.ts in a Vercel project (Node.js runtime)
import { Bot, webhookCallback } from "grammy";

const token = process.env.BOT_TOKEN;
if (!token) throw new Error("BOT_TOKEN is unset");

const bot = new Bot(token);

bot.command("start", (ctx) => ctx.reply("Hello from Vercel"));
bot.on("message:text", (ctx) => ctx.reply(`You said: ${ctx.message.text}`));
bot.catch((err) => console.error("bot error", err));

export default webhookCallback(bot, "https", {
  secretToken: process.env.WEBHOOK_SECRET,
});
TS
    ;;

  *)
    echo "error: unknown framework '$framework'. valid: express, fastify, hono, cloudflare, https, vercel" >&2
    exit 2
    ;;
esac

echo "Wrote $out (framework: $framework)"
echo "Next:"
case "$framework" in
  cloudflare)   echo "  wrangler secret put BOT_TOKEN && wrangler secret put BOT_INFO && wrangler deploy" ;;
  https|vercel) echo "  vercel deploy   # then setWebhook to https://<your-app>.vercel.app/api/bot" ;;
  *)            echo "  curl \"https://api.telegram.org/bot\$BOT_TOKEN/setWebhook?url=https://\$DOMAIN/\$BOT_TOKEN\"" ;;
esac
echo "  # if you set WEBHOOK_SECRET, pass the same value as secret_token to setWebhook"
