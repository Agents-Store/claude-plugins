---
description: Diagnose a Chatwoot API / CLI / webhook problem — run read-only connectivity, auth, and scope checks against the configured instance and report the fix.
argument-hint: [optional: the error or symptom you're seeing]
allowed-tools: [Read, Bash, Grep]
---

Diagnose this Chatwoot problem: **$ARGUMENTS**

Run the read-only checks below (all GETs — safe), interpret the results, and recommend a fix.
Load the `troubleshoot` skill for the full symptom → cause → fix tables.

1. **Env vars present?**
   ```bash
   for v in CHATWOOT_BASE_URL CHATWOOT_API_KEY CHATWOOT_ACCOUNT_ID; do
     [ -n "${!v}" ] && echo "$v: set" || echo "$v: MISSING"
   done
   ```
   If any are missing, stop and point the user to the `setup` skill.

2. **Base URL reachable?**
   ```bash
   curl -sI "${CHATWOOT_BASE_URL}" | head -1
   ```

3. **Token valid + identity?** (401 ⇒ bad token or wrong header; remember it's
   `api_access_token`, not `Authorization: Bearer`)
   ```bash
   curl -s -o /dev/null -w "profile HTTP %{http_code}\n" \
     -H "api_access_token: ${CHATWOOT_API_KEY}" "${CHATWOOT_BASE_URL}/api/v1/profile"
   curl -s -H "api_access_token: ${CHATWOOT_API_KEY}" \
     "${CHATWOOT_BASE_URL}/api/v1/profile" | jq '{id, name, role}' 2>/dev/null
   ```

4. **Account scope resolves?** (404 ⇒ wrong `account_id` or base URL)
   ```bash
   curl -s -o /dev/null -w "conversations HTTP %{http_code}\n" \
     -H "api_access_token: ${CHATWOOT_API_KEY}" \
     "${CHATWOOT_BASE_URL}/api/v1/accounts/${CHATWOOT_ACCOUNT_ID}/conversations"
   ```

5. **CLI installed/authenticated?** (optional)
   ```bash
   command -v chatwoot >/dev/null && chatwoot auth status 2>&1 | head -5 || echo "chatwoot CLI not installed"
   ```

6. Map the observed status codes to the fix using the `troubleshoot` skill:
   401 → token/header or wrong API family · 403 → insufficient role · 404 → account_id/base
   URL · 422 → request body · 429 → rate limit/backoff. For webhook signature mismatches,
   verify the HMAC is computed over the **raw** body as `"{timestamp}.{raw_body}"`.

Report what passed, what failed, and the single most likely fix.
