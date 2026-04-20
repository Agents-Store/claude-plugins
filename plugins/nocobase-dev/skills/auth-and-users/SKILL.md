---
name: auth-and-users
description: |
  Authentication, authenticators (SSO/OIDC/SAML), users, roles, RBAC resource scopes, route permissions, API keys, and ACL governance in NocoBase across MCP, CLI, and HTTP. Use when:
  - "sign in"
  - "create users"
  - "manage roles"
  - "generate API keys"
  - "configure SSO"
  - "check permissions"
  - "set up authentication"
  - "NocoBase ACL"
  - "role resource scope"
  - "grant role access"
  - "desktop route access role"
  - "role data source access"
  - "authenticators NocoBase"
  - "users_roles"
  - "available_actions_list"
---

# Auth & Users

Manage authentication, users, roles, ACL scopes, and API keys in NocoBase across three transports. This skill also owns **ACL governance** — the full RBAC surface (23 MCP tools) and the upstream acl-manage playbook for risk-gated permission changes.

## MCP tools

### Session lifecycle
| Task | MCP tool |
|------|----------|
| Sign in | `auth_sign_in` |
| Sign up | `auth_sign_up` |
| Sign out | `auth_sign_out` |
| Verify session | `auth_check` |
| Change password | `auth_change_password` |

### Authenticators (auth provider registry)
| Task | MCP tool |
|------|----------|
| List all authenticators | `authenticators_list` |
| Get one | `authenticators_get` |
| Create new | `authenticators_create` |
| Update | `authenticators_update` |
| Delete | `authenticators_destroy` |
| List types (OIDC, SAML, LDAP, etc.) | `authenticators_list_types` |
| Public list (sign-in page) | `authenticators_public_list` |

### Users
| Task | MCP tool |
|------|----------|
| List users | `users_list` |
| Get one | `users_get` |
| Create | `users_create` |
| Update | `users_update` |
| Delete | `users_destroy` |

### User ↔ role membership
| Task | MCP tool |
|------|----------|
| List a user's roles | `users_roles_list` |
| Add role to user | `users_roles_add` |
| Remove role from user | `users_roles_remove` |

### Roles
| Task | MCP tool |
|------|----------|
| List | `roles_list` |
| Get one | `roles_get` |
| Create | `roles_create` |
| Update | `roles_update` |
| Delete | `roles_destroy` |
| Check current permissions | `roles_check` |
| Set default role for new users | `roles_set_default_role` |
| Switch single-role / multi-role mode | `roles_set_system_role_mode` |
| List users in a role | `roles_users_list` |
| Add users to a role | `roles_users_add` |
| Remove users from a role | `roles_users_remove` |

### Role ↔ resource scopes (ACL)
| Task | MCP tool |
|------|----------|
| List per-resource scopes for a role | `roles_resources_scopes_list` |
| Get one | `roles_resources_scopes_get` |
| Create scope on a data-source resource | `roles_data_source_resources_create` |
| Get it | `roles_data_source_resources_get` |
| Update | `roles_data_source_resources_update` |
| List collections visible to a role in a data source | `roles_data_sources_collections_list` |

### Role ↔ desktop-route access
| Task | MCP tool |
|------|----------|
| List routes a role can access | `roles_desktop_routes_list` |
| Grant route access | `roles_desktop_routes_add` |
| Revoke route access | `roles_desktop_routes_remove` |
| Replace full route-access list | `roles_desktop_routes_set` |

### ACL action registry
| Task | MCP tool |
|------|----------|
| List canonical ACL actions (`view`, `create`, `update`, `destroy`, `export`, `importXlsx`) | `available_actions_list` |

**Call `available_actions_list` before writing any role resource scope** — the action names and aliases come from this authoritative registry.

## ACL governance playbook

Full upstream ACL governance content (risk-gated role changes, permission hierarchies, independent permissions, field/route/system permissions, scopes) lives in `references/acl/`. Highlights:

- `references/acl/scopes.md` — per-role resource-scope design
- `references/acl/field-permissions.md` — per-field ACL
- `references/acl/route-permissions.md` — per-route access
- `references/acl/global-table-permissions.md` — whole-collection grants
- `references/acl/independent-permissions.md` — non-inheritable per-role scopes
- `references/acl/system-permissions.md` — system-level (`view`, `create`, etc.) defaults
- `references/acl/safety-and-debug.md` — debugging ACL denials
- `references/acl/intent-to-tool-map-v1.md` — "user wants X, use tool Y" map
- `references/acl/intent-presets-v1.md` — preset intent handlers
- `references/acl/capability-test-plan.md` — end-to-end capability testing
- `references/acl/configuration.md` — ACL global configuration
- `references/acl/execution-guard-template.md` — risk-gated execution template
- `references/acl/mcp-tool-shapes.md` — MCP tool parameter shapes for ACL
- `references/acl/result-format-v1.md` — expected response shape for ACL ops

**Hard rule:** treat any ACL change as risk-high. Always:
1. Call `available_actions_list` first to confirm action names
2. Use the declarative-apply family (`roles_data_source_resources_create/update`) over building scope trees by hand
3. After writing, verify with `roles_check` in the new role's session

## Authentication (HTTP path)

All HTTP requests require the API key header:

```
Authorization: Bearer ${NOCOBASE_API_KEY}
```

Base URL for all endpoints: `${NOCOBASE_URL}/api/`

## Authentication Flow

### Check Current Auth

Verify whether the current session/token is valid and get the authenticated user's info.

```bash
curl -X GET "${NOCOBASE_URL}/api/auth:check" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Returns the current user object if authenticated, or an error if the token is invalid or expired.

### Sign In

Authenticate with username/email and password to get a session token.

```bash
curl -X POST "${NOCOBASE_URL}/api/auth:signIn" \
  -H "Content-Type: application/json" \
  -d '{
    "account": "admin@example.com",
    "password": "your-password"
  }'
```

The `account` field accepts either an email address or a username, depending on the authenticator configuration.

Returns a token in the response that can be used for subsequent API calls.

### Sign Up

Register a new user account.

```bash
curl -X POST "${NOCOBASE_URL}/api/auth:signUp" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "secure-password"
  }'
```

Sign-up must be enabled in the authenticator configuration. Required fields depend on the authenticator settings.

### Sign Out

End the current session.

```bash
curl -X POST "${NOCOBASE_URL}/api/auth:signOut" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### Change Password

Change the current user's password.

```bash
curl -X POST "${NOCOBASE_URL}/api/auth:changePassword" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "oldPassword": "current-password",
    "newPassword": "new-secure-password"
  }'
```

### X-Authenticator Header

When multiple authenticators are configured (e.g., local + OIDC + SAML), use the `X-Authenticator` header to specify which one to use:

```bash
curl -X POST "${NOCOBASE_URL}/api/auth:signIn" \
  -H "Content-Type: application/json" \
  -H "X-Authenticator: basic" \
  -d '{
    "account": "admin@example.com",
    "password": "password"
  }'
```

Common authenticator names: `basic` (email/password), `sms` (phone verification). Custom authenticator names depend on configuration.

## SSO Endpoints

### OIDC (OpenID Connect)

Get the authorization URL for OIDC-based login.

```bash
curl -X GET "${NOCOBASE_URL}/api/oidc:getAuthUrl" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Returns a URL to redirect the user to the OIDC provider's login page.

### SAML

Get the authorization URL for SAML-based login.

```bash
curl -X GET "${NOCOBASE_URL}/api/saml:getAuthUrl" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Returns a URL for SAML IdP-initiated or SP-initiated login.

## User Management

### List Users

```bash
curl -X GET "${NOCOBASE_URL}/api/users:list?page=1&pageSize=20" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Supports query parameters:
- `filter` — JSON filter (e.g., `{"email": {"$includes": "example.com"}}`)
- `sort` — sort field (e.g., `-createdAt`)
- `page` / `pageSize` — pagination
- `appends` — include related data (e.g., `roles`)

### Get Single User

```bash
curl -X GET "${NOCOBASE_URL}/api/users:get?filterByTk=1&appends=roles" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Use `appends=roles` to include the user's role assignments.

### Create User

```bash
curl -X POST "${NOCOBASE_URL}/api/users:create" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "jdoe",
    "nickname": "John Doe",
    "email": "jdoe@example.com",
    "password": "initial-password",
    "phone": "+1234567890"
  }'
```

Fields:
- `username` — login name (unique)
- `nickname` — display name
- `email` — email address (unique if used for auth)
- `password` — initial password
- `phone` — optional phone number

### Update User

```bash
curl -X POST "${NOCOBASE_URL}/api/users:update?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "nickname": "John D.",
    "phone": "+9876543210"
  }'
```

### Destroy User

```bash
curl -X POST "${NOCOBASE_URL}/api/users:destroy?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

## API Key Management

API keys provide long-lived authentication tokens for programmatic access.

### Create API Key

```bash
curl -X POST "${NOCOBASE_URL}/api/apiKeys:create" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CI/CD Pipeline Key",
    "expiresIn": "90d"
  }'
```

Expiration options:
- `"1d"` — 1 day
- `"7d"` — 7 days
- `"30d"` — 30 days
- `"90d"` — 90 days
- `"never"` — no expiration

The response includes the API key token. Store it securely — it is only shown once.

### List API Keys

```bash
curl -X GET "${NOCOBASE_URL}/api/apiKeys:list" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Returns all API keys for the current user. The actual token values are not returned in list responses — only metadata (name, creation date, expiration).

### Destroy API Key

```bash
curl -X DELETE "${NOCOBASE_URL}/api/apiKeys:destroy/key-id-here" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Revoke an API key immediately. All requests using this key will fail after deletion.

## Authenticator Configuration

Authenticators define how users can sign in (email/password, SMS, OIDC, SAML, etc.).

### List Authenticators

```bash
curl -X GET "${NOCOBASE_URL}/api/authenticators:list" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### List Authenticator Types

```bash
curl -X GET "${NOCOBASE_URL}/api/authenticators:listTypes" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Returns available authenticator type plugins (e.g., `email-password`, `sms`, `oidc`, `saml`, `cas`).

### Get Public Authenticators

```bash
curl -X GET "${NOCOBASE_URL}/api/authenticators:publicList" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Returns only the authenticators visible on the login page (enabled and set to public).

For detailed role management, permissions, and authenticator CRUD, see `references/role-management.md`.

## Common Workflows

### Set Up a New User with Role

```
1. POST users:create → create the user account
2. GET roles:list → find the target role name
3. POST roles/{roleName}/users:add → assign role to user
```

### Rotate an API Key

```
1. POST apiKeys:create → create new key with desired expiration
2. Update external systems with the new key
3. DELETE apiKeys:destroy/{oldKeyId} → revoke old key
```

### Verify Authentication Setup

```
1. GET auth:check → confirm current token is valid
2. GET authenticators:publicList → see what login methods are available
3. GET users:get?filterByTk=currentUserId&appends=roles → check role assignments
```

## Best Practices

1. **Use API keys for automation** — create dedicated API keys with appropriate expiration for CI/CD and integrations.
2. **Rotate keys regularly** — create new keys before revoking old ones to avoid downtime.
3. **Check auth before operations** — call `auth:check` to verify the token is still valid.
4. **Use X-Authenticator** — specify the authenticator explicitly when multiple auth methods exist.
5. **Never store passwords** — use API keys or SSO tokens for programmatic access.
6. **Assign roles immediately** — create users and assign roles in the same workflow to avoid orphaned accounts.
7. **Monitor API key expiration** — list keys periodically and renew before they expire.

## See also

- `mcp-patterns` — transport and tool catalog
- `data-sources` — per-datasource role scopes (`data_sources_roles_*`)
- `routes-and-menus` — role-based desktop-route access
- `system-admin` — system-level grants and `available_actions_list`
- `troubleshoot` — ACL denial debugging
