---
description: Configure a NocoDB webhook (HookV3) on a table
argument-hint: [table-name-or-id] [event] [destination]
allowed-tools: [Read, Write, Bash, Skill]
---

# Add Webhook

Configure a HookV3 webhook on a table — fire on insert / update / delete (or bulk variants), evaluate an optional condition, dispatch to URL / Email / Messaging / Script.

## Steps

1. Resolve the target table ID via `mcp__nocodb__getTablesList` or `nc table:list`.
2. Gather the user's intent:
   - **Event**: `record` (default — fires on the chosen `operation`(s) after commit) or `manual` (fires only when explicitly invoked from a Button or Script)
   - **Operations**: array of `insert` / `update` / `delete` (one hook can listen to multiple)
   - **Destination**: URL endpoint / Email / Slack-style messaging / Script
   - **Trigger fields** (optional, for `update`): list of column IDs — fire only when one of these changed
   - **Conditional firing**: there is no top-level `condition` in v3 — gate inside the destination body using `{{record.<Field>}}` or use a `Script` notification
3. Build the payload — see **webhooks** skill for full HookV3Create shape.
4. Snapshot existing hooks first to avoid duplicates:
   ```bash
   nc hook:list <baseId> <tableId>
   ```
5. Run:
   ```bash
   nc hook:create <baseId> <tableId> '<HookV3Create JSON>'
   ```
6. Verify the hook appears in `nc hook:list`. If safe, fire a single test record matching the condition; confirm the destination receives the payload.

## Templating

Body content can reference field values via `{{record.<FieldName>}}`. Field names are case-sensitive and must match the column title exactly.

For bulk operations, the destination receives `records` (array) instead of `record` (single).

## Reference

- `Skill nocodb-dev:webhooks` — full schema + worked examples
- `Skill nocodb-dev:api-reference` — `HookV3Create` schema in `references/nocodb-openapi.json`
- `Skill nocodb-dev:cli-reference` — `nc hook:*` syntax

## Watch Out

- All v3 hooks are async-after-commit — there's no `before`/`after` distinction. NocoDB retries on non-2xx responses, so destinations must tolerate replays.
- The Email notification type requires NocoDB's SMTP plugin to be configured; otherwise emails silently fail.
- For URL hooks, prefer Authorization headers over baking secrets into the body.
- v3 has no top-level `condition` filter on hooks — gate inside the destination, or use a `Script` notification.
