---
description: Configure a NocoDB webhook (HookV3) on a table
argument-hint: [table-name-or-id] [event] [destination]
allowed-tools: [Read, Write, Bash, Skill]
---

# Add Webhook

Configure a HookV3 webhook on a table — fire on insert / update / delete, optionally scoped to specific fields on update, dispatch to URL / Email / a messaging service / Script.

## Steps

1. Resolve the target table ID via `mcp__plugin_nocodb-dev_nocodb__getTablesList`.
2. Gather the user's intent:
   - **Event**: `record` (default — fires on the chosen `operation`(s) after commit) or `manual` (fires only when explicitly invoked from a Button or Script)
   - **Operations**: array of `insert` / `update` / `delete` (one hook can listen to multiple)
   - **Destination**: URL endpoint / Email / Slack, Discord, Telegram, Whatsapp or Twilio messaging / Script
   - **Trigger fields** (optional, for `update`): list of field IDs — fire only when one of these changed
   - **Conditional firing**: there is no top-level `condition` in v3 — gate inside the destination body using `{{record.<Field>}}` or use a `Script` notification
3. Build the payload — see **webhooks** skill for the full HookV3Create shape (`notification.type` is `URL`, `Email`, `Slack`, `Discord`, `Telegram`, `Whatsapp`, `Twilio` or `Script`).
4. Snapshot existing hooks first to avoid duplicates:
   ```
   mcp__plugin_nocodb-dev_nocodb__listHooks  tableId: <tableId>
   ```
5. Create the hook. On Cloud / licensed: `listTools category: "hooks"`, then `callTool name: "createHook"` with `arguments: { tableId, title, event, operation, notification, active, trigger_fields? }`. On Community Edition (or as a fallback) use REST:
   ```bash
   curl -sS -X POST \
     -H "xc-token: ${NOCODB_TOKEN}" -H "Content-Type: application/json" \
     -d '<HookV3Create JSON>' \
     "${NOCODB_URL}/api/v3/meta/bases/${BASE_ID}/tables/<tableId>/hooks"
   ```
6. Verify the hook appears in `listHooks`. If safe, fire a single test record that should trigger it; confirm the destination receives the payload.

## Templating

Body content can reference field values via `{{record.<FieldName>}}`. Field names are case-sensitive and must match the field title exactly.

For bulk operations, the destination may receive `records` (array) instead of `record` (single) — check the payload your destination actually gets.

## Reference

- `Skill nocodb-dev:webhooks` — full schema + worked examples
- `Skill nocodb-dev:api-reference` — `HookV3Create` schema in `references/nocodb-meta-openapi.json`
- `Skill nocodb-dev:mcp-patterns` — MCP `createHook` / `updateHook` (full replacement) contract

## Watch Out

- Hook APIs need a cloud Business plan or a licensed self-hosted deployment.
- All v3 hooks are async-after-commit — there's no `before`/`after` distinction. NocoDB retries on non-2xx responses, so destinations must tolerate replays.
- The Email notification type requires NocoDB's SMTP plugin to be configured; otherwise emails silently fail.
- Messaging notifications carry only a `body`; the Slack / Discord / … connection is configured in NocoDB, not in the hook payload.
- For URL hooks, prefer Authorization headers over baking secrets into the body.
- v3 has no top-level `condition` filter on hooks — gate inside the destination, or use a `Script` notification.
- The MCP `updateHook` replaces the whole hook: `getHook` first and resend every key you want to keep.
