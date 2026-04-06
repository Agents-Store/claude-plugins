# NocoBase API — System Settings, Storage, Plugins, Localization & Utilities

All endpoints use base URL `${NOCOBASE_URL}/api/` with header `Authorization: Bearer ${NOCOBASE_API_KEY}`.

---

## System Settings (2 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/systemSettings:get` | Get current system settings |
| POST | `/api/systemSettings:update` | Update system settings |

### Get System Settings

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/systemSettings:get"
```

**Response includes:** `title`, `logo`, `enabledLanguages`, `appLang`, `allowSignUp`, `smsAuthEnabled`, `theme`, etc.

### Update System Settings

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/systemSettings:update" \
  -d '{
    "title": "My NocoBase App",
    "allowSignUp": false,
    "enabledLanguages": ["en-US", "zh-CN"]
  }'
```

---

## Backup Settings (2 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/backupSettings:get` | Get backup configuration |
| POST | `/api/backupSettings:update` | Update backup settings |

### Get Backup Settings

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/backupSettings:get"
```

### Update Backup Settings

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/backupSettings:update" \
  -d '{
    "enabled": true,
    "cron": "0 2 * * *",
    "maxBackups": 7
  }'
```

---

## Storage (5 endpoints)

File storage configurations (local, S3, Alibaba OSS, Tencent COS, etc.).

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/storages:list` | List all storage configurations |
| GET | `/api/storages:get?filterByTk={id}` | Get storage details |
| POST | `/api/storages:create` | Create a new storage configuration |
| POST | `/api/storages:update?filterByTk={id}` | Update storage settings |
| POST | `/api/storages:destroy?filterByTk={id}` | Delete a storage configuration |

### List Storages

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/storages:list"
```

### Create Storage (S3 example)

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/storages:create" \
  -d '{
    "title": "AWS S3 Storage",
    "name": "s3-main",
    "type": "s3",
    "default": true,
    "options": {
      "region": "us-east-1",
      "accessKeyId": "AKIA...",
      "secretAccessKey": "...",
      "bucket": "my-nocobase-files"
    },
    "baseUrl": "https://my-nocobase-files.s3.amazonaws.com"
  }'
```

**Body fields:** `title`, `name`, `type` (`local`, `s3`, `ali-oss`, `tx-cos`), `default` (boolean), `options` (object), `baseUrl` (string)

### Update Storage

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/storages:update?filterByTk=1" \
  -d '{ "default": true }'
```

### Destroy Storage

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/storages:destroy?filterByTk=2"
```

---

## Theme Configuration (4 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/themeConfig:list` | List all theme configurations |
| POST | `/api/themeConfig:create` | Create a new theme |
| POST | `/api/themeConfig:update?filterByTk={id}` | Update a theme |
| POST | `/api/themeConfig:destroy?filterByTk={id}` | Delete a theme |

### List Themes

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/themeConfig:list"
```

### Create Theme

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/themeConfig:create" \
  -d '{
    "config": {
      "name": "Dark Theme",
      "token": {
        "colorPrimary": "#1677ff",
        "colorBgBase": "#141414",
        "colorTextBase": "#ffffff"
      }
    },
    "optional": true,
    "isBuiltIn": false
  }'
```

### Update Theme

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/themeConfig:update?filterByTk=2" \
  -d '{ "config": { "token": { "colorPrimary": "#ff4d4f" } } }'
```

### Destroy Theme

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/themeConfig:destroy?filterByTk=2"
```

---

## Map Configuration (2 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/map-configuration:get` | Get map provider settings |
| POST | `/api/map-configuration:set` | Set map provider configuration |

### Get Map Configuration

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/map-configuration:get?type=amap"
```

**Query parameter:** `type` — map provider (`amap`, `google`)

### Set Map Configuration

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/map-configuration:set" \
  -d '{
    "type": "google",
    "config": {
      "accessKey": "your-google-maps-api-key"
    }
  }'
```

---

## Plugin Manager (3 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/pm:enable` | Enable a plugin |
| POST | `/api/pm:disable` | Disable a plugin |
| POST | `/api/pm:remove` | Remove (uninstall) a plugin |

### Enable Plugin

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/pm:enable" \
  -d '{ "filterByTk": "workflow" }'
```

### Disable Plugin

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/pm:disable" \
  -d '{ "filterByTk": "workflow" }'
```

### Remove Plugin

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/pm:remove" \
  -d '{ "filterByTk": "custom-plugin" }'
```

---

## App (5 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/app:getInfo` | Get application info (version, environment) |
| GET | `/api/app:getLang` | Get current language settings |
| GET | `/api/app:getPlugins` | List all installed plugins with status |
| POST | `/api/app:restart` | Restart the NocoBase application |
| POST | `/api/app:clearCache` | Clear the application cache |

### Get App Info

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/app:getInfo"
```

### Get Language

```bash
curl "${NOCOBASE_URL}/api/app:getLang?locale=en-US"
```

No authentication required. Returns language resources for the specified locale.

### Get Plugins

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/app:getPlugins"
```

### Restart App

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/app:restart"
```

### Clear Cache

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/app:clearCache"
```

---

## Applications — Multi-App Management (4 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/applications:list` | List all sub-applications |
| POST | `/api/applications:create` | Create a new sub-application |
| POST | `/api/applications:update?filterByTk={name}` | Update a sub-application |
| POST | `/api/applications:destroy?filterByTk={name}` | Delete a sub-application |

### List Applications

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/applications:list"
```

### Create Application

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/applications:create" \
  -d '{
    "name": "tenant-acme",
    "displayName": "ACME Corp",
    "options": { "standalone": true }
  }'
```

### Update Application

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/applications:update?filterByTk=tenant-acme" \
  -d '{ "displayName": "ACME Corporation" }'
```

### Destroy Application

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/applications:destroy?filterByTk=tenant-acme"
```

---

## Localization (4 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/localization:sync` | Sync translatable strings from the application |
| POST | `/api/localization:publish` | Publish updated translations to the application |
| GET | `/api/localizationTexts:list` | List translation source texts |
| POST | `/api/localizationTranslations:updateOrCreate` | Create or update a translation |

### Sync Localization

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/localization:sync"
```

Scans the application for translatable strings and adds them to the localization texts table.

### Publish Translations

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/localization:publish"
```

Makes updated translations live in the application.

### List Localization Texts

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/localizationTexts:list?page=1&pageSize=50&filter={\"module\":{\"$eq\":\"collections\"}}"
```

**Common filter fields:** `module`, `text`

### Update or Create Translation

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/localizationTranslations:updateOrCreate" \
  -d '{
    "filterKeys": ["textId", "locale"],
    "values": {
      "textId": 42,
      "locale": "uk-UA",
      "translation": "Замовлення"
    }
  }'
```

---

## Verifications (5 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/verifications:list` | List verification records |
| GET | `/api/verifications:get?filterByTk={id}` | Get verification details |
| POST | `/api/verifications:create` | Create a verification (send code) |
| POST | `/api/verifications:update?filterByTk={id}` | Update verification status |
| POST | `/api/verifications:destroy?filterByTk={id}` | Delete a verification record |

### Create Verification (Send Code)

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/verifications:create" \
  -d '{
    "type": "sms",
    "receiver": "+1234567890"
  }'
```

---

## Verification Providers (4 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/verifications_providers:list` | List verification providers |
| POST | `/api/verifications_providers:create` | Create a provider configuration |
| POST | `/api/verifications_providers:update?filterByTk={id}` | Update provider config |
| POST | `/api/verifications_providers:destroy?filterByTk={id}` | Delete a provider |

### List Providers

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/verifications_providers:list"
```

### Create Provider

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/verifications_providers:create" \
  -d '{
    "title": "Twilio SMS",
    "type": "sms-twilio",
    "options": {
      "accountSid": "AC...",
      "authToken": "...",
      "from": "+15555555555"
    }
  }'
```

---

## Utilities

Miscellaneous system endpoints.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/availableActions:list` | List all available resource actions |
| POST | `/api/userData:push` | Push user data (custom user sync) |
| GET | `/api/swagger:getUrls` | Get Swagger/OpenAPI documentation URLs |
| GET | `/api/chinaRegions:list` | List China administrative regions |

### List Available Actions

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/availableActions:list"
```

Returns all registered resource actions and their configurations (useful for permission setup).

### Push User Data

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/userData:push" \
  -d '{
    "dataType": "user",
    "records": [
      { "username": "external-user", "email": "ext@example.com", "nickname": "External User" }
    ]
  }'
```

### Get Swagger URLs

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/swagger:getUrls"
```

Returns URLs for all available OpenAPI/Swagger documentation endpoints, organized by plugin.

### List China Regions

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/chinaRegions:list?filter={\"level\":{\"$eq\":1}}"
```

Hierarchical listing of China's provinces, cities, and districts. Used by the China Region field type.
