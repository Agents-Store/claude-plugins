---
description: Trigger a Directus automation flow
argument-hint: <flow-name-or-id> <collection> [--keys <id1,id2>] [--data <json>]
---

# Trigger Flow

## Arguments

- `flow-name-or-id` (required) — Flow name (partial match) or UUID
- `collection` (required) — Collection context
- `--keys <id1,id2>` — Item IDs (required if flow needs selection)
- `--data <json>` — JSON payload passed as `$trigger.body`

## Process

1. **Find the flow:**
   - Call `flows` tool with `action: "read"` to list all flows
   - Match by name (partial, case-insensitive) or by UUID
   - If multiple matches, ask user to clarify

2. **Read flow definition:**
   - Call `flows` tool with `action: "read"` and `key: "<flow-uuid>"`
   - Check trigger type (must be manual or webhook for programmatic triggering)
   - Check if `requireSelection` is set (if yes, `--keys` is required)
   - Show flow details to user before triggering

3. **Trigger the flow:**
   ```json
   {
     "id": "<flow-uuid>",
     "collection": "<collection>",
     "keys": ["<id1>", "<id2>"],
     "data": { "custom": "payload" }
   }
   ```

4. Display the flow execution result

## Example

Input: `"Welcome Email" contacts --keys abc-123 --data {"send_now": true}`

## Important

- Always read the flow definition before triggering
- Verify the flow is active (status: "active")
- Check trigger type compatibility
- Warn user before triggering flows with side effects (emails, webhooks, deletions)
