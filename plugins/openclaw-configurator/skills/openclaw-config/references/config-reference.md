# openclaw.json Key Fields Reference

Complete reference for the most important openclaw.json configuration fields.

---

## agents.defaults

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `workspace` | string | `./workspace` | Agent workspace path (relative to instance root) |
| `model` | string/object | — | Primary LLM model. Object: `{ primary, fallbacks[] }` |
| `imageModel` | string/object | — | Model for image analysis |
| `bootstrapMaxChars` | number | 20000 | Max chars per workspace file |
| `bootstrapTotalMaxChars` | number | 150000 | Max total chars across all files |
| `userTimezone` | string | — | e.g., `"Europe/Kyiv"` |
| `timeFormat` | string | `"auto"` | `"auto"` / `"12"` / `"24"` |
| `timeoutSeconds` | number | 600 | Session timeout |
| `maxConcurrent` | number | 3 | Max parallel sessions |
| `thinkingDefault` | string | — | `"off"` / `"minimal"` / `"low"` / `"medium"` / `"high"` / `"adaptive"` |
| `contextTokens` | number | 200000 | Context window size |
| `skipBootstrap` | boolean | false | Skip workspace file loading |

## agents.defaults.heartbeat

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `every` | string | — | Interval: `"5m"`, `"10m"`, `"1h"` |
| `model` | string | — | Model for heartbeats (use cheap one) |
| `lightContext` | boolean | — | Minimal context loading |
| `isolatedSession` | boolean | — | Separate session for heartbeats |
| `prompt` | string | — | Custom heartbeat prompt |

## agents.defaults.compaction

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `mode` | string | — | Compaction strategy |
| `reserveTokensFloor` | number | — | Reserved tokens before compaction |
| `memoryFlush` | boolean | — | Enable memory flush before compaction |

## agents.list[]

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Stable agent identifier (required) |
| `default` | boolean | Is this the default agent? |
| `name` | string | Display name |
| `workspace` | string | Override workspace path |
| `model` | string/object | Override model |
| `identity` | object | `{ name, theme, emoji, avatar }` |
| `sandbox` | object | `{ mode }` for sandboxing |

---

## channels.telegram

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | — | Enable Telegram channel |
| `botToken` | string | — | Bot token (or `tokenFile`) |
| `dmPolicy` | string | — | `"pairing"` / `"allowlist"` / `"open"` / `"disabled"` |
| `allowFrom` | string[] | — | User IDs: `["tg:549422805"]` |
| `groups` | object | — | Per-group config (see below) |
| `historyLimit` | number | 50 | Messages to load per session |
| `streaming` | string | — | `"off"` / `"partial"` / `"block"` / `"progress"` |

### channels.telegram.groups[groupId]

| Field | Type | Description |
|-------|------|-------------|
| `requireMention` | boolean | Only respond when @mentioned |
| `allowFrom` | string[] | Allowed users in this group |
| `systemPrompt` | string | Group-specific system prompt |
| `topics` | object | Per-topic configuration |

## channels.discord

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | — | Enable Discord |
| `token` | string | — | Bot token |
| `dmPolicy` | string | — | Same as Telegram |
| `allowFrom` | string[] | — | User IDs |
| `guilds` | object | — | Per-guild config |
| `historyLimit` | number | 20 | Messages per session |
| `textChunkLimit` | number | 2000 | Max message length |

## channels.whatsapp

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `dmPolicy` | string | — | Access policy |
| `allowFrom` | string[] | — | Phone numbers: `["+15555550123"]` |
| `groupPolicy` | string | — | `"allowlist"` / `"open"` / `"disabled"` |
| `textChunkLimit` | number | 4000 | Max message length |

---

## tools

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `profile` | string | — | `"minimal"` / `"coding"` / `"messaging"` / `"full"` |
| `allow` | string[] | — | Allowed tools (wildcards ok) |
| `deny` | string[] | — | Denied tools |

### tools.exec

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `timeoutSec` | number | 1800 | Execution timeout |
| `backgroundMs` | number | 10000 | Background task timeout |

### tools.loopDetection

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | false | Enable loop detection |
| `warningThreshold` | number | 10 | Warning trigger count |
| `criticalThreshold` | number | 20 | Critical stop count |

---

## plugins

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | true | Enable plugin system |
| `allow` | string[] | — | Plugin allowlist |
| `deny` | string[] | — | Plugin blocklist |
| `load.paths` | string[] | — | Additional plugin load paths |

### plugins.entries[pluginId]

| Field | Type | Description |
|-------|------|-------------|
| `enabled` | boolean | Enable/disable this plugin |
| `config` | object | Plugin-specific configuration |
| `env` | object | Plugin-scoped environment variables |

---

## session

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `dmScope` | string | — | `"main"` / `"per-peer"` / `"per-channel-peer"` |
| `reset.mode` | string | — | Session reset strategy |
| `reset.idleMinutes` | number | — | Idle timeout for reset |
| `resetTriggers` | string[] | — | Commands that reset session: `["/new", "/reset"]` |

---

## skills

| Field | Type | Description |
|-------|------|-------------|
| `allowBundled` | string[] | Which bundled skills to enable |
| `load.extraDirs` | string[] | Additional skill directories |
| `entries` | object | Per-skill configuration |
