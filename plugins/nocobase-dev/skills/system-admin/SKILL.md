---
name: system-admin
description: System administration — settings, storage, backups, plugins, app management, multi-app. This skill should be used when the user asks to "configure system settings", "manage storage", "enable plugins", "restart the app", "clear cache", "manage backups", "create sub-applications", or "administer NocoBase" through the API.
---

# System Administration

Manage NocoBase system settings, storage providers, backups, plugins, application lifecycle, multi-app instances, and background jobs across MCP, CLI, and HTTP.

## MCP operational tools

| Task | MCP tool |
|------|----------|
| List background jobs (imports, exports, long tasks) | `jobs_list` |
| Get one job's status | `jobs_get` |
| Resume a paused job | `jobs_resume` |
| List canonical ACL actions | `available_actions_list` |

Most system admin is still HTTP/CLI-first — plugin management, settings, storage, restart. See sections below for `pm:*`, `systemSettings:*`, and `app:*`.

For plugin management details, see `plugin-development` (pm CLI reference) and `publish-manage` (cross-env migrations).

## Authentication

All requests require the API key header:

```
Authorization: Bearer ${NOCOBASE_API_KEY}
```

Base URL for all endpoints: `${NOCOBASE_URL}/api/`

## System Settings

Global application settings that control the instance name, logo, and general behavior.

### Get System Settings

```bash
curl -X GET "${NOCOBASE_URL}/api/systemSettings:get" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Returns the full system settings object including title, logo URL, enabled languages, and other global configuration.

### Update System Settings

```bash
curl -X POST "${NOCOBASE_URL}/api/systemSettings:update" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My NocoBase Instance",
    "enabledLanguages": ["en-US", "uk-UA", "zh-CN"],
    "appLang": "en-US"
  }'
```

Common settings fields:
- `title` — application name displayed in the browser tab and header
- `enabledLanguages` — array of locale codes available to users
- `appLang` — default language for the application
- `logo` — logo configuration object

## Storage Management

Configure file storage providers for attachments and uploaded files.

### List Storage Providers

```bash
curl -X GET "${NOCOBASE_URL}/api/storages:list" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### Get Storage Details

```bash
curl -X GET "${NOCOBASE_URL}/api/storages:get?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### Create Storage Provider

```bash
curl -X POST "${NOCOBASE_URL}/api/storages:create" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "S3 Bucket",
    "name": "s3-main",
    "type": "s3",
    "default": false,
    "options": {
      "region": "us-east-1",
      "accessKeyId": "AKIAIOSFODNN7EXAMPLE",
      "secretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
      "bucket": "my-nocobase-files",
      "endpoint": ""
    },
    "rules": {
      "size": 20971520
    }
  }'
```

Storage types:
- `local` — local filesystem storage
- `s3` — Amazon S3 or S3-compatible (MinIO, DigitalOcean Spaces, etc.)
- `ali-oss` — Alibaba Cloud OSS
- `tx-cos` — Tencent Cloud COS

### Update Storage

```bash
curl -X POST "${NOCOBASE_URL}/api/storages:update?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "default": true,
    "rules": {
      "size": 52428800
    }
  }'
```

### Destroy Storage

```bash
curl -X POST "${NOCOBASE_URL}/api/storages:destroy?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Cannot delete a storage provider if files are still stored in it. Migrate files first.

## Backup Settings

Configure automatic backup behavior.

### Get Backup Settings

```bash
curl -X GET "${NOCOBASE_URL}/api/backupSettings:get" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### Update Backup Settings

```bash
curl -X POST "${NOCOBASE_URL}/api/backupSettings:update" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "cron": "0 2 * * *",
    "maxBackups": 7
  }'
```

## Plugin Management

Enable, disable, and remove NocoBase plugins. Plugins extend the platform with additional features (workflow nodes, field types, authentication methods, etc.).

### Enable a Plugin

```bash
curl -X POST "${NOCOBASE_URL}/api/pm:enable" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "filterByTk": "workflow"
  }'
```

The `filterByTk` value is the plugin package name (e.g., `workflow`, `oidc`, `saml`, `map`, `localization`).

Enabling a plugin may trigger database migrations and require an application restart.

### Disable a Plugin

```bash
curl -X POST "${NOCOBASE_URL}/api/pm:disable" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "filterByTk": "map"
  }'
```

Disabling a plugin removes its features from the UI but preserves its data. Re-enabling restores functionality.

### Remove a Plugin

```bash
curl -X POST "${NOCOBASE_URL}/api/pm:remove" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "filterByTk": "custom-plugin"
  }'
```

Removing a plugin uninstalls it entirely. Data created by the plugin may be lost. Use with caution.

## Application Management

Control the NocoBase application lifecycle — inspect status, restart, clear cache.

### Get Application Info

```bash
curl -X GET "${NOCOBASE_URL}/api/app:getInfo" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Returns application metadata including:
- NocoBase version
- Database type and version
- Node.js version
- Installed plugins and their versions

### Get Current Language

```bash
curl -X GET "${NOCOBASE_URL}/api/app:getLang" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Returns the current application language setting.

### Get Installed Plugins

```bash
curl -X GET "${NOCOBASE_URL}/api/app:getPlugins" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Returns a list of all installed plugins with their name, version, enabled status, and description.

### Restart Application

```bash
curl -X POST "${NOCOBASE_URL}/api/app:restart" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Perform a graceful restart of the NocoBase application. Required after:
- Enabling or disabling plugins
- Certain system setting changes
- Database migration operations

The application will be temporarily unavailable during restart. Wait a few seconds before making subsequent requests.

### Clear Application Cache

```bash
curl -X POST "${NOCOBASE_URL}/api/app:clearCache" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Clear all cached data including:
- UI schema cache
- Collection metadata cache
- Plugin configuration cache

Use when the UI does not reflect recent changes, or after manual database modifications.

## Multi-App Management

NocoBase supports running multiple independent application instances from a single installation (multi-tenancy).

### List Applications

```bash
curl -X GET "${NOCOBASE_URL}/api/applications:list" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### Create Sub-Application

```bash
curl -X POST "${NOCOBASE_URL}/api/applications:create" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "tenant-acme",
    "displayName": "ACME Corp",
    "options": {
      "standalone": true
    }
  }'
```

Each sub-application gets its own database schema, users, and configuration.

### Update Application

```bash
curl -X POST "${NOCOBASE_URL}/api/applications:update?filterByTk=tenant-acme" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "displayName": "ACME Corporation"
  }'
```

### Destroy Application

```bash
curl -X POST "${NOCOBASE_URL}/api/applications:destroy?filterByTk=tenant-acme" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Permanently deletes the sub-application and all its data. This is irreversible.

## Verification Providers

Configure verification providers (SMS, email, etc.) for two-factor authentication and user verification.

### List Verification Providers

```bash
curl -X GET "${NOCOBASE_URL}/api/verifications_providers:list" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### Create Verification Provider

```bash
curl -X POST "${NOCOBASE_URL}/api/verifications_providers:create" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "sms-twilio",
    "title": "Twilio SMS",
    "type": "sms-twilio",
    "options": {
      "accountSid": "ACxxxxx",
      "authToken": "xxxxx",
      "from": "+15551234567"
    },
    "default": true
  }'
```

### Update Verification Provider

```bash
curl -X POST "${NOCOBASE_URL}/api/verifications_providers:update?filterByTk=sms-twilio" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "options": {
      "from": "+15559876543"
    }
  }'
```

### Destroy Verification Provider

```bash
curl -X POST "${NOCOBASE_URL}/api/verifications_providers:destroy?filterByTk=sms-twilio" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### List Verifications

```bash
curl -X GET "${NOCOBASE_URL}/api/verifications:list" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### Get Verification Details

```bash
curl -X GET "${NOCOBASE_URL}/api/verifications:get?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### Create Verification (Send Code)

```bash
curl -X POST "${NOCOBASE_URL}/api/verifications:create" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "sms-twilio",
    "receiver": "+15551234567"
  }'
```

### Update Verification

```bash
curl -X POST "${NOCOBASE_URL}/api/verifications:update?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "verified"
  }'
```

### Destroy Verification

```bash
curl -X POST "${NOCOBASE_URL}/api/verifications:destroy?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

## Available Actions

List all actions available in the system (useful for understanding the API surface).

```bash
curl -X GET "${NOCOBASE_URL}/api/availableActions:list" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Returns all registered resource actions, including built-in CRUD operations and custom actions added by plugins.

## Common Administration Workflows

### Initial Setup After Installation

```
1. GET app:getInfo → verify installation and version
2. POST systemSettings:update → set title, default language
3. GET app:getPlugins → check installed plugins
4. POST pm:enable → enable needed plugins (workflow, localization, etc.)
5. POST app:restart → apply plugin changes
6. POST storages:create → configure file storage (S3, local, etc.)
```

### Plugin Lifecycle

```
1. GET app:getPlugins → list installed plugins and their status
2. POST pm:enable → enable the plugin
3. POST app:restart → restart to apply
4. Verify the plugin is working (check its API endpoints)
5. If needed: POST pm:disable → disable the plugin
```

### Troubleshooting UI Issues

```
1. POST app:clearCache → clear all caches
2. GET systemSettings:get → verify settings are correct
3. If still broken: POST app:restart → full restart
```

### Multi-Tenant Setup

```
1. POST applications:create → create a sub-application
2. Access the sub-application at its URL
3. Configure independently (own users, collections, UI)
4. POST applications:update → modify settings as needed
```

## Best Practices

1. **Restart after plugin changes** — always call `app:restart` after enabling or disabling plugins.
2. **Clear cache when in doubt** — if the UI does not reflect changes, `app:clearCache` is a safe first step.
3. **Use S3 for production** — local file storage does not scale; configure S3-compatible storage early.
4. **Set up backups** — configure backup settings before going to production.
5. **Monitor app info** — periodically check `app:getInfo` to track version and database status.
6. **Test plugins in staging** — enable new plugins on a staging instance before production.
7. **Keep default language consistent** — set `appLang` to match your primary user base.
8. **Limit multi-app usage** — each sub-application consumes database and memory resources; plan capacity accordingly.
9. **Secure verification providers** — store SMS/email provider credentials securely and rotate them periodically.
10. **Use availableActions for discovery** — call `availableActions:list` (HTTP) or `available_actions_list` (MCP) to understand what API endpoints are registered, especially after enabling new plugins.

## See also

- `plugin-development` — plugin lifecycle and `pm` CLI
- `publish-manage` — cross-environment publishing (risk-gated)
- `auth-and-users` — user/role admin
- `data-sources` — external-database admin
- `troubleshoot` — error-mode diagnosis
