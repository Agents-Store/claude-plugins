# Role Management Reference

Detailed reference for NocoBase V2 role administration, permissions, collection-level access control, and authenticator configuration via the HTTP API.

## Role CRUD

### List Roles

```bash
curl -X GET "${NOCOBASE_URL}/api/roles:list" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Returns all defined roles with their names, titles, and configuration.

### Get Single Role

```bash
curl -X GET "${NOCOBASE_URL}/api/roles:get?filterByTk=admin" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

The `filterByTk` value is the role `name` (string), not a numeric ID.

### Create Role

```bash
curl -X POST "${NOCOBASE_URL}/api/roles:create" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "sales-manager",
    "title": "Sales Manager",
    "description": "Access to orders, customers, and sales reports",
    "default": false,
    "snippets": ["ui.*"]
  }'
```

Fields:
- `name` (required) — unique identifier, use kebab-case (e.g., `sales-manager`)
- `title` (required) — human-readable display name
- `description` — optional explanation of the role's purpose
- `default` — `true` to auto-assign this role to new users
- `snippets` — array of UI permission snippets (e.g., `"ui.*"` for full UI access)

### Update Role

```bash
curl -X POST "${NOCOBASE_URL}/api/roles:update?filterByTk=sales-manager" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Sales Manager (Updated)",
    "snippets": ["ui.*", "pm.*"]
  }'
```

### Destroy Role

```bash
curl -X POST "${NOCOBASE_URL}/api/roles:destroy?filterByTk=sales-manager" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Built-in roles (`root`, `admin`, `member`) cannot be deleted.

## Check Permissions

### Check Role for Current User

```bash
curl -X GET "${NOCOBASE_URL}/api/roles:check" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Returns the effective permissions for the currently authenticated user, including:
- Role name and title
- Strategy settings (global resource permissions)
- Action permissions per collection
- UI snippet permissions

### Set Default Role

```bash
curl -X POST "${NOCOBASE_URL}/api/roles:setDefaultRole" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "member"
  }'
```

The default role is automatically assigned to every new user at registration. Only one role can be the default.

## Role-Collection Access Control

Control which collections and actions a role can access.

### List Collection Access for a Role

```bash
curl -X GET "${NOCOBASE_URL}/api/roles/sales-manager/collections:list" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Returns the list of collections accessible to this role along with the permitted actions for each.

### Configure Collection Access

```bash
curl -X POST "${NOCOBASE_URL}/api/roles/sales-manager/collections:update" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "collectionName": "orders",
    "usingActionsConfig": true,
    "actions": [
      { "name": "view", "scope": null },
      { "name": "create", "scope": null },
      { "name": "update", "scope": { "createdById": "{{ $user.id }}" } },
      { "name": "destroy", "scope": null, "enabled": false }
    ]
  }'
```

Action names: `view`, `create`, `update`, `destroy`, `export`, `importXlsx`

Scope options:
- `null` — all records (no restriction)
- `{ "createdById": "{{ $user.id }}" }` — only records created by the current user
- Custom filter objects for field-level conditions

### Assign User to Role

```bash
curl -X POST "${NOCOBASE_URL}/api/roles/sales-manager/users:add" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "tk": 5
  }'
```

The `tk` value is the user's ID.

### Remove User from Role

```bash
curl -X POST "${NOCOBASE_URL}/api/roles/sales-manager/users:remove" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "tk": 5
  }'
```

## Authenticator Configuration

### List Authenticators

```bash
curl -X GET "${NOCOBASE_URL}/api/authenticators:list" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### Get Single Authenticator

```bash
curl -X GET "${NOCOBASE_URL}/api/authenticators:get?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### Create Authenticator

```bash
curl -X POST "${NOCOBASE_URL}/api/authenticators:create" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "google-oidc",
    "authType": "oidc",
    "title": "Sign in with Google",
    "description": "Google Workspace OIDC login",
    "enabled": true,
    "options": {
      "oidc": {
        "issuer": "https://accounts.google.com",
        "clientId": "your-client-id",
        "clientSecret": "your-client-secret",
        "scope": "openid email profile"
      }
    }
  }'
```

Fields:
- `name` — unique identifier for the authenticator
- `authType` — plugin type (`"email-password"`, `"sms"`, `"oidc"`, `"saml"`, `"cas"`)
- `title` — display name on the login page
- `enabled` — whether this authenticator is active
- `options` — type-specific configuration object

### Update Authenticator

```bash
curl -X POST "${NOCOBASE_URL}/api/authenticators:update?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": false
  }'
```

### Destroy Authenticator

```bash
curl -X POST "${NOCOBASE_URL}/api/authenticators:destroy?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### List Available Authenticator Types

```bash
curl -X GET "${NOCOBASE_URL}/api/authenticators:listTypes" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Returns which authentication plugins are installed and available for use.

### List Public Authenticators

```bash
curl -X GET "${NOCOBASE_URL}/api/authenticators:publicList" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Returns only authenticators that appear on the public login page.

## Example: Creating a Role with Specific Collection Access

Complete workflow to create a restricted `viewer` role that can only read orders and customers.

### Step 1: Create the Role

```bash
curl -X POST "${NOCOBASE_URL}/api/roles:create" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "viewer",
    "title": "Viewer",
    "description": "Read-only access to orders and customers",
    "default": false,
    "snippets": ["ui.*"]
  }'
```

### Step 2: Configure Collection Access for Orders

```bash
curl -X POST "${NOCOBASE_URL}/api/roles/viewer/collections:update" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "collectionName": "orders",
    "usingActionsConfig": true,
    "actions": [
      { "name": "view", "scope": null }
    ]
  }'
```

### Step 3: Configure Collection Access for Customers

```bash
curl -X POST "${NOCOBASE_URL}/api/roles/viewer/collections:update" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "collectionName": "customers",
    "usingActionsConfig": true,
    "actions": [
      { "name": "view", "scope": null }
    ]
  }'
```

### Step 4: Assign a User to the Role

```bash
curl -X POST "${NOCOBASE_URL}/api/roles/viewer/users:add" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "tk": 10
  }'
```

### Step 5: Verify

```bash
curl -X GET "${NOCOBASE_URL}/api/roles/viewer/collections:list" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

## Built-in Roles

| Role | Purpose | Deletable |
|------|---------|-----------|
| `root` | Super admin, full system access | No |
| `admin` | Admin role with full data access | No |
| `member` | Default role for regular users | No |

## Permission Snippets

Snippets control access to system-level features.

| Snippet | Access |
|---------|--------|
| `ui.*` | All UI configuration |
| `ui.pages` | Page management |
| `pm.*` | All plugin management |
| `pm.enable` | Enable/disable plugins |
| `app.*` | Application settings |

## Strategy (Global Resource Permissions)

Roles have a `strategy` field that sets default permissions for all collections not explicitly configured.

```json
{
  "strategy": {
    "actions": ["view", "create", "update", "destroy"]
  }
}
```

If a collection has explicit action config (`usingActionsConfig: true`), it overrides the strategy.
