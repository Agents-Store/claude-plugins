---
name: auth
description: "Use when the user wants to authenticate to a NocoBase v2 instance, asks \"how do I get an API key for NocoBase\", \"set up OAuth on NocoBase\", \"why is my request returning 401 from NocoBase\", or needs working curl/Node samples that send the bearer token. Covers both supported flows: the API Keys plugin and the IdP: OAuth plugin."
---

# Authentication — NocoBase v2

NocoBase v2 accepts `Authorization: Bearer <token>` for every `/api/` request. The OpenAPI spec declares this as the `api-key` security scheme (HTTP bearer). Two production paths exist for getting that token.

## Path A — API Key (recommended for service-to-service)

### 1. Enable the API Keys plugin

```bash
nb pm enable api-keys
```

The `nocobase-plugin-manage` skill covers `nb pm` semantics, error handling, and listing plugins.

### 2. Create a token in the admin UI

Open NocoBase → `Settings → API keys → Create`:

- **Name** — short identifier (e.g. `agent-bot`).
- **Role** — choose the role whose permissions the key will inherit. The token can do exactly what the role can do; nothing more.
- **Expiration** — pick a date or `Never`.

Copy the token; it is shown only once.

### 3. Send authorised requests

```bash
export NOCOBASE_URL="https://app.example.com"
export NOCOBASE_API_KEY="<token-from-admin-ui>"

# List collections
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
     "${NOCOBASE_URL}/api/collections:list"

# Create a record in the `posts` collection
curl -X POST \
     -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
     -H "Content-Type: application/json" \
     -d '{"title":"hello","body":"first post"}' \
     "${NOCOBASE_URL}/api/posts:create"
```

### 4. Node.js examples

```js
// fetch (Node 18+)
const res = await fetch(`${process.env.NOCOBASE_URL}/api/collections:list`, {
  headers: { Authorization: `Bearer ${process.env.NOCOBASE_API_KEY}` },
});
const data = await res.json();
```

```js
// axios
import axios from "axios";

const nb = axios.create({
  baseURL: `${process.env.NOCOBASE_URL}/api`,
  headers: { Authorization: `Bearer ${process.env.NOCOBASE_API_KEY}` },
});

const { data } = await nb.get("/collections:list");
```

### Rotation and revocation

- Tokens are revoked from the same screen (`Settings → API keys → Delete`).
- Rotation: create the new token first, deploy it, then delete the old one — there is no in-place rotation.
- Tokens inherit the role at the time of issuance. If the role is later restricted, the token is restricted too on the next request.

## Path B — OAuth (IdP: OAuth, recommended for end-user flows)

### 1. Enable the IdP: OAuth plugin

```bash
nb pm enable @nocobase/plugin-oidc-client
```

Plugin name may also appear as `oidc-client` or `idp-oauth` in different builds — `nb pm list` to confirm the actual name on your install.

### 2. Configure the provider in admin UI

`Settings → Authentication → Add → OAuth (OIDC)`:

- **Issuer URL** — your IdP's discovery URL (e.g. Keycloak, Auth0, Google).
- **Client ID / Client Secret** — from the IdP.
- **Redirect URI** — `${NOCOBASE_URL}/api/auth:redirect?authenticator=<your-name>`.
- **Scopes** — typically `openid profile email`.

### 3. Authorisation-code flow

```text
Browser → GET ${NOCOBASE_URL}/api/auth:redirect?authenticator=<name>
       → IdP login screen
       → Browser ← 302 to ${NOCOBASE_URL}/?code=…&state=…
       → POST ${NOCOBASE_URL}/api/auth:signIn?authenticator=<name>
              { code, state } → returns NocoBase access token
```

```bash
# Step 4: use the resulting token the same way as an API key
curl -H "Authorization: Bearer ${OAUTH_ACCESS_TOKEN}" \
     "${NOCOBASE_URL}/api/users:list"
```

### Choosing between the two paths

| Use case | Pick |
|---|---|
| Background script, cron, agent, service-to-service | API Key |
| Human user signing in to a NocoBase-backed UI | OAuth |
| Integration where the third-party already issues OIDC tokens | OAuth |
| You need fine-grained auditing per integration | API Key (one per integration) |

## Common 401 / 403 causes

- Missing or wrong `Authorization` header — the value is exactly `Bearer <token>`, single space, case-sensitive `Bearer`.
- Token expired (API Key with explicit expiration; OAuth access token).
- Role attached to the token has no permission for the requested resource — check `nocobase-acl-manage`.
- Plugin providing the token type is disabled — `nb pm list` to confirm `api-keys` or the OIDC plugin is enabled.
- Calling a multi-app instance — make sure the `X-App` header / hostname matches the app the token was issued for.

## OpenAPI declaration

The full spec at `${CLAUDE_PLUGIN_ROOT}/references/openapi/nocobase.json` declares:

```json
"securitySchemes": {
  "api-key": { "type": "http", "scheme": "bearer" }
}
```

Both API Key and OAuth tokens satisfy this scheme — the server validates the token, not its origin.
