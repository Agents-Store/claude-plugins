# NocoBase API — UI Schemas, Authentication, Users, Roles, API Keys & Authenticators

All endpoints use base URL `${NOCOBASE_URL}/api/` with header `Authorization: Bearer ${NOCOBASE_API_KEY}`.

---

## UI Schemas (9 endpoints)

UI Schemas define the layout and configuration of NocoBase's frontend interface.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/uiSchemas:getJsonSchema/{uid}` | Get the full JSON schema tree for a UI node |
| GET | `/api/uiSchemas:getProperties/{uid}` | Get properties (children) of a UI schema node |
| POST | `/api/uiSchemas:insert` | Insert a new UI schema node |
| POST | `/api/uiSchemas:remove/{uid}` | Remove a UI schema node |
| POST | `/api/uiSchemas:patch` | Patch (partial update) a UI schema node |
| POST | `/api/uiSchemas:batchPatch` | Batch patch multiple UI schema nodes |
| POST | `/api/uiSchemas:insertAdjacent/{uid}` | Insert a schema node adjacent to an existing node |
| POST | `/api/uiSchemas:saveAsTemplate` | Save a UI schema as a reusable template |
| POST | `/api/uiSchemas:clearAncestor/{uid}` | Clear inherited schema from ancestor |

### Get JSON Schema

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/uiSchemas:getJsonSchema/abc123"
```

Returns the full schema tree including all nested children. The `{uid}` is the unique identifier of the UI schema node (x-uid).

### Get Properties

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/uiSchemas:getProperties/abc123"
```

Returns only the direct properties (children) of the specified schema node.

### Insert Schema

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/uiSchemas:insert" \
  -d '{
    "schema": {
      "type": "void",
      "x-component": "Grid",
      "x-uid": "custom-grid-1",
      "properties": {
        "row1": {
          "type": "void",
          "x-component": "Grid.Row"
        }
      }
    }
  }'
```

### Remove Schema

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/uiSchemas:remove/abc123"
```

### Patch Schema

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/uiSchemas:patch" \
  -d '{
    "x-uid": "abc123",
    "x-component-props": { "title": "Updated Title" }
  }'
```

### Batch Patch

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/uiSchemas:batchPatch" \
  -d '[
    { "x-uid": "abc123", "x-component-props": { "title": "Title A" } },
    { "x-uid": "def456", "x-component-props": { "title": "Title B" } }
  ]'
```

### Insert Adjacent

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/uiSchemas:insertAdjacent/abc123?position=afterEnd" \
  -d '{
    "schema": {
      "type": "void",
      "x-component": "Grid.Row"
    }
  }'
```

**Query parameter:** `position` — `beforeBegin`, `afterBegin`, `beforeEnd`, `afterEnd`

### Save as Template

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/uiSchemas:saveAsTemplate" \
  -d '{
    "uid": "abc123",
    "name": "My Block Template",
    "key": "my-block-template"
  }'
```

### Clear Ancestor

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/uiSchemas:clearAncestor/abc123"
```

---

## Authentication (5 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/auth:check` | Check if the current token is valid |
| POST | `/api/auth:signIn` | Sign in and obtain a token |
| POST | `/api/auth:signUp` | Register a new user account |
| POST | `/api/auth:signOut` | Sign out (invalidate token) |
| POST | `/api/auth:changePassword` | Change the current user's password |

### Check Token

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/auth:check"
```

Returns the current user object if the token is valid, or an error if expired/invalid.

### Sign In

```bash
curl -X POST -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/auth:signIn" \
  -d '{
    "account": "admin@example.com",
    "password": "your-password"
  }'
```

**Response includes:** `data.token` — use this as the Bearer token for subsequent requests.

**Optional query parameter:** `authenticator` — specify which authenticator to use (default: `basic`).

### Sign Up

```bash
curl -X POST -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/auth:signUp" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "secure-password"
  }'
```

### Sign Out

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/auth:signOut"
```

### Change Password

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/auth:changePassword" \
  -d '{
    "oldPassword": "old-password",
    "newPassword": "new-secure-password"
  }'
```

---

## SSO — Single Sign-On (2 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/oidc:getAuthUrl` | Get the OIDC (OpenID Connect) login URL |
| GET | `/api/saml:getAuthUrl` | Get the SAML login URL |

### Get OIDC Auth URL

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/oidc:getAuthUrl?authenticator=oidc-provider-1"
```

**Query parameter:** `authenticator` — name of the OIDC authenticator configuration.

**Response:** `{ "data": "https://provider.com/authorize?client_id=...&redirect_uri=..." }`

### Get SAML Auth URL

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/saml:getAuthUrl?authenticator=saml-provider-1"
```

---

## Users (5 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users:list` | List all users |
| GET | `/api/users:get?filterByTk={id}` | Get user details |
| POST | `/api/users:create` | Create a new user |
| POST | `/api/users:update?filterByTk={id}` | Update user details |
| POST | `/api/users:destroy?filterByTk={id}` | Delete a user |

### List Users

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/users:list?page=1&pageSize=50&fields=[id,nickname,email,roles]&appends=[roles]"
```

### Get User

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/users:get?filterByTk=1&appends=[roles]"
```

### Create User

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/users:create" \
  -d '{
    "username": "johndoe",
    "nickname": "John Doe",
    "email": "john@example.com",
    "password": "secure-password",
    "phone": "+1234567890"
  }'
```

**Body fields:** `username`, `nickname`, `email`, `password`, `phone`, `systemSettings` (object)

### Update User

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/users:update?filterByTk=5" \
  -d '{ "nickname": "John D.", "phone": "+1987654321" }'
```

### Destroy User

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/users:destroy?filterByTk=5"
```

---

## Roles (7 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/roles:list` | List all roles |
| GET | `/api/roles:get?filterByTk={name}` | Get role details by name |
| POST | `/api/roles:create` | Create a new role |
| POST | `/api/roles:update?filterByTk={name}` | Update role settings |
| POST | `/api/roles:destroy?filterByTk={name}` | Delete a role |
| GET | `/api/roles:check` | Check permissions for the current user's role |
| POST | `/api/roles:setDefaultRole` | Set the default role for new users |

### List Roles

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/roles:list"
```

### Get Role

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/roles:get?filterByTk=admin"
```

The `filterByTk` value is the role `name` (string), not a numeric ID.

### Create Role

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/roles:create" \
  -d '{
    "name": "editor",
    "title": "Editor",
    "description": "Can edit content but not manage settings",
    "strategy": {
      "actions": ["view", "create", "update"]
    }
  }'
```

**Body fields:** `name` (string, required), `title` (string), `description` (string), `strategy` (object), `default` (boolean)

### Update Role

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/roles:update?filterByTk=editor" \
  -d '{ "title": "Content Editor", "strategy": { "actions": ["view", "create", "update", "export"] } }'
```

### Destroy Role

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/roles:destroy?filterByTk=editor"
```

### Check Permissions

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/roles:check"
```

Returns the effective permissions for the current user's active role.

### Set Default Role

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/roles:setDefaultRole" \
  -d '{ "name": "member" }'
```

### List Collection Permissions for a Role

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/roles/admin/collections:list"
```

Returns per-collection permission settings for the specified role.

---

## API Keys (3 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/apiKeys:list` | List all API keys |
| POST | `/api/apiKeys:create` | Create a new API key |
| POST | `/api/apiKeys:destroy?filterByTk={id}` | Revoke/delete an API key |

### List API Keys

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/apiKeys:list"
```

### Create API Key

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/apiKeys:create" \
  -d '{
    "name": "CI/CD Pipeline Key",
    "role": "admin",
    "expiresIn": "30d"
  }'
```

**Body fields:** `name` (string) — descriptive name, `role` (string) — role to assign, `expiresIn` (string) — expiration duration (e.g., `7d`, `30d`, `1y`)

**Response includes:** `data.token` — the API key value (shown only once at creation).

### Destroy API Key

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/apiKeys:destroy?filterByTk=5"
```

---

## Authenticators (7 endpoints)

Authenticators define login methods (email/password, OIDC, SAML, SMS, etc.).

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/authenticators:list` | List all authenticators (admin) |
| GET | `/api/authenticators:get?filterByTk={id}` | Get authenticator details |
| POST | `/api/authenticators:create` | Create a new authenticator |
| POST | `/api/authenticators:update?filterByTk={id}` | Update authenticator config |
| POST | `/api/authenticators:destroy?filterByTk={id}` | Delete an authenticator |
| GET | `/api/authenticators:listTypes` | List available authenticator types |
| GET | `/api/authenticators:publicList` | List authenticators visible on the login page |

### List Authenticators

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/authenticators:list"
```

### Get Authenticator

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/authenticators:get?filterByTk=1"
```

### Create Authenticator

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/authenticators:create" \
  -d '{
    "name": "google-oidc",
    "title": "Sign in with Google",
    "authType": "oidc",
    "enabled": true,
    "options": {
      "issuer": "https://accounts.google.com",
      "clientId": "your-client-id",
      "clientSecret": "your-client-secret"
    }
  }'
```

**Body fields:** `name` (string, required), `title` (string), `authType` (string — `basic`, `oidc`, `saml`, `sms`), `enabled` (boolean), `options` (object — provider-specific config)

### Update Authenticator

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/authenticators:update?filterByTk=2" \
  -d '{ "enabled": false }'
```

### Destroy Authenticator

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/authenticators:destroy?filterByTk=2"
```

### List Authenticator Types

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/authenticators:listTypes"
```

Returns all available authenticator types (depends on installed plugins).

### Public List

```bash
curl "${NOCOBASE_URL}/api/authenticators:publicList"
```

No authentication required. Returns authenticators visible on the login page.
