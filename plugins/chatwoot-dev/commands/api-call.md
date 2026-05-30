---
description: Build (and optionally run) an authenticated Chatwoot REST API request — picks the correct API family and auth header, reads GETs freely, and confirms before any write.
argument-hint: [resource or action, e.g. "list open conversations in inbox 5"]
allowed-tools: [Read, Bash, Grep]
---

Construct a correct, authenticated Chatwoot API request for: **$ARGUMENTS**

Follow these steps:

1. **Pick the API family** from the request:
   - Account/agent work (conversations, messages, contacts, inboxes, teams, reports,
     automation, webhooks, help center) → **Application API**
     `${CHATWOOT_BASE_URL}/api/v1/accounts/${CHATWOOT_ACCOUNT_ID}/...`
   - Installation provisioning (accounts, users, account-users, agent bots) → **Platform API**
     `${CHATWOOT_BASE_URL}/platform/api/v1/...` (uses the platform app token)
   - Customer/widget-facing → **Public/Client API**
     `${CHATWOOT_BASE_URL}/public/api/v1/inboxes/{inbox_identifier}/...` (no token)

2. **Find the exact endpoint** in the bundled specs before composing the request — do not
   guess paths or field names:
   ```bash
   D="${CLAUDE_PLUGIN_ROOT}/skills/api-reference/references/openapi"
   jq -r '.paths | keys[]' "$D/application_swagger.json" | grep -i <keyword>
   jq '.paths["<path>"]' "$D/application_swagger.json"
   ```
   The human-readable endpoint tables are in
   `${CLAUDE_PLUGIN_ROOT}/skills/api-reference/references/{application,platform,client}-api.md`.

3. **Build the curl** with the right auth header (`api_access_token`, never Bearer):
   ```bash
   curl -s -H "api_access_token: ${CHATWOOT_API_KEY}" \
     "${CHATWOOT_BASE_URL}/api/v1/accounts/${CHATWOOT_ACCOUNT_ID}/<path>" | jq .
   ```

4. **Run vs. confirm:**
   - If the request is a **GET** (read-only), you may run it.
   - If it is a **POST / PATCH / PUT / DELETE**, or any operation that sends a message or
     changes shared state, **show the exact command and ask for explicit confirmation before
     running it**. A sent message cannot be unsent.

5. If credentials are missing, point the user to the `setup` skill rather than inventing
   values. Never print or hardcode the token — reference `${CHATWOOT_API_KEY}`.
