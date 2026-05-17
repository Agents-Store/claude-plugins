#!/usr/bin/env bash
# init-bot.sh — scaffold a fresh TypeScript grammY project.
# Usage: init-bot.sh <project-dir>
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $0 <project-dir>" >&2
  exit 2
fi

target="$1"

if [[ -e "$target" ]] && [[ -n "$(ls -A "$target" 2>/dev/null || true)" ]]; then
  echo "error: $target already exists and is not empty" >&2
  exit 1
fi

mkdir -p "$target/src"
cd "$target"

cat > package.json <<'JSON'
{
  "name": "grammy-bot",
  "private": true,
  "type": "module",
  "scripts": {
    "dev":   "tsx watch src/bot.ts",
    "start": "node --import tsx src/bot.ts",
    "check": "tsc --noEmit"
  },
  "dependencies": {
    "grammy": "^1.42.0",
    "dotenv": "^16.4.5"
  },
  "devDependencies": {
    "tsx": "^4.19.0",
    "typescript": "^5.6.0",
    "@types/node": "^22.0.0"
  }
}
JSON

cat > tsconfig.json <<'JSON'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ES2022",
    "moduleResolution": "Bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "outDir": "dist"
  },
  "include": ["src/**/*"]
}
JSON

cat > .env.example <<'ENV'
# Get a bot token from @BotFather on Telegram
BOT_TOKEN=123456:ABC-replace-me
ENV

cat > .gitignore <<'GIT'
node_modules
dist
.env
*.log
.DS_Store
GIT

cat > src/bot.ts <<'TS'
import "dotenv/config";
import { Bot, GrammyError, HttpError } from "grammy";

const bot = new Bot(process.env.BOT_TOKEN!);

bot.command("start", (ctx) => ctx.reply("Hi! I'm alive."));

bot.on("message:text", (ctx) =>
  ctx.reply(`You said: ${ctx.message.text}`)
);

bot.catch((err) => {
  const ctx = err.ctx;
  console.error(`Error while handling update ${ctx.update.update_id}:`);
  const e = err.error;
  if (e instanceof GrammyError)        console.error("Bot API:", e.description);
  else if (e instanceof HttpError)     console.error("Network:", e);
  else                                  console.error("Unknown:", e);
});

bot.start();
TS

cat > README.md <<'MD'
# grammy-bot

Bootstrapped with `grammy-dev` plugin's `init-bot.sh`.

## Quick start

```bash
cp .env.example .env   # paste your BOT_TOKEN
npm install
npm run dev
```

Send `/start` to your bot in Telegram.
MD

echo "Scaffolded $target"
echo "Next:"
echo "  cd $target"
echo "  cp .env.example .env  # then paste your BOT_TOKEN"
echo "  npm install"
echo "  npm run dev"
