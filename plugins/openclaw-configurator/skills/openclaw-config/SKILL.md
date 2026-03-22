---
name: openclaw-config
description: OpenClaw openclaw.json configuration guide. Use when the user needs to understand or modify their openclaw.json — agents, channels, tools, plugins, session, and model settings. Triggers on "openclaw.json", "configure OpenClaw", "channel setup", "model configuration", "tools profile", "plugin configuration", "agent routing".
---

# openclaw.json Configuration Guide

`openclaw.json` is the central gateway configuration file, located at `./openclaw.json` (relative to instance root `~/.openclaw-{name}/`). It controls models, channels, tools, plugins, sessions, and agent routing. Separate from workspace files — this is infrastructure configuration.

## Key Sections

### agents — Agent Configuration

```json
{
  "agents": {
    "defaults": {
      "workspace": "./workspace",
      "model": "claude-sonnet-4-20250514",
      "bootstrapMaxChars": 20000,
      "bootstrapTotalMaxChars": 150000,
      "userTimezone": "Europe/Kyiv",
      "timeFormat": "24",
      "timeoutSeconds": 600,
      "maxConcurrent": 3,
      "heartbeat": {
        "every": "5m",
        "model": "gpt-4o-mini",
        "lightContext": true
      }
    },
    "list": [
      {
        "id": "main",
        "default": true,
        "name": "Main Agent",
        "identity": { "name": "Nova", "emoji": "star" }
      }
    ]
  }
}
```

**Key fields:**
- `model` — primary LLM (string or `{ primary, fallbacks[] }`)
- `bootstrapMaxChars` / `bootstrapTotalMaxChars` — workspace file limits
- `heartbeat.every` — heartbeat interval ("5m", "10m", "1h")
- `heartbeat.model` — cheaper model for heartbeats to save tokens
- `maxConcurrent` — parallel session limit

### channels — Communication Platforms

#### Telegram
```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "botToken": "$TELEGRAM_BOT_TOKEN",
      "dmPolicy": "allowlist",
      "allowFrom": ["tg:549422805"],
      "groups": {
        "-1001234567890": {
          "requireMention": true,
          "allowFrom": ["tg:549422805", "tg:123456789"]
        }
      }
    }
  }
}
```

#### Discord
```json
{
  "channels": {
    "discord": {
      "enabled": true,
      "token": "$DISCORD_BOT_TOKEN",
      "dmPolicy": "allowlist",
      "allowFrom": ["discord:USER_ID"],
      "guilds": {
        "GUILD_ID": {
          "requireMention": true
        }
      }
    }
  }
}
```

#### WhatsApp
```json
{
  "channels": {
    "whatsapp": {
      "dmPolicy": "allowlist",
      "allowFrom": ["+15555550123"],
      "groupPolicy": "allowlist"
    }
  }
}
```

**Common channel fields:**
- `dmPolicy` — "pairing" | "allowlist" | "open" | "disabled"
- `allowFrom` — user ID allowlist (format: `"tg:ID"`, `"discord:ID"`, phone number)
- `groups` — per-group configuration with `requireMention`, `allowFrom`

### tools — Tool Access Control

```json
{
  "tools": {
    "profile": "full",
    "allow": ["*"],
    "deny": ["dangerous_tool"],
    "exec": {
      "timeoutSec": 1800,
      "backgroundMs": 10000
    },
    "loopDetection": {
      "enabled": false,
      "warningThreshold": 10,
      "criticalThreshold": 20
    }
  }
}
```

**Profiles:** `"minimal"` | `"coding"` | `"messaging"` | `"full"`

### plugins — Plugin Management

```json
{
  "plugins": {
    "enabled": true,
    "allow": ["plugin-a", "plugin-b"],
    "deny": [],
    "load": { "paths": ["/custom/plugin/path"] },
    "entries": {
      "my-plugin": {
        "enabled": true,
        "config": { "apiKey": "$PLUGIN_API_KEY" }
      }
    }
  }
}
```

### session — Session Behavior

```json
{
  "session": {
    "dmScope": "main",
    "reset": {
      "mode": "idle",
      "idleMinutes": 60
    },
    "resetTriggers": ["/new", "/reset"]
  }
}
```

**dmScope options:** `"main"` | `"per-peer"` | `"per-channel-peer"`

## Relationship to Workspace Files

| openclaw.json | Informs Which Workspace File |
|---------------|------------------------------|
| `agents.defaults.model` | TOOLS.md (model-specific tool notes) |
| `channels.telegram.groups` | AGENTS.md (group chat rules per group) |
| `channels.*.allowFrom` | USER.md (map IDs to user names) |
| `tools.profile` | TOOLS.md (available tool categories) |
| `plugins.entries` | AGENTS.md (plugin-specific behavior rules) |
| `agents.defaults.heartbeat` | HEARTBEAT.md (aligns with heartbeat config) |
| `agents.defaults.userTimezone` | USER.md (timezone), HEARTBEAT.md (quiet hours) |

## What to Check When Optimizing

1. **Model selection** — is the primary model appropriate for the domain?
2. **Channel configuration** — are all active channels properly configured?
3. **User allowlists** — do they match the users in USER.md?
4. **Heartbeat settings** — interval appropriate? Using cheap model?
5. **Tool profile** — "full" vs "minimal" based on agent's needs?
6. **Plugin entries** — are all needed plugins enabled?
7. **Bootstrap limits** — workspace files staying under limits?

See `references/config-reference.md` for the complete field reference.

## Best Practices

1. Keep secrets (tokens, API keys) in env vars, not inline
2. Use `allowlist` dmPolicy for production agents
3. Set `heartbeat.model` to a cheap model
4. Configure `userTimezone` to match primary user
5. Enable `loopDetection` for production stability
6. Review `maxConcurrent` based on usage patterns
