---
name: localization
description: Localization — translations, sync, publish, multi-language support. This skill should be used when the user asks to "translate", "localize", "add language support", "sync translations", "publish translations", or "manage multilingual content" in NocoBase.
---

# Localization

Manage NocoBase V2 multi-language support through the HTTP API — synchronize translation sources, list translatable texts, create or update translations, and publish them to the active application.

## Authentication

All requests require the API key header:

```
Authorization: Bearer ${NOCOBASE_API_KEY}
```

Base URL for all endpoints: `${NOCOBASE_URL}/api/`

## Overview

NocoBase V2 supports multiple languages through a centralized localization system. The platform separates translatable text sources from their translations, allowing you to:

- Discover all translatable strings across the application (collection names, field labels, menu items, plugin strings)
- Create translations for any locale
- Publish translations so they take effect in the running application

The localization workflow follows a strict sequence: **sync** source texts, **list** available texts, **update** translations, then **publish**.

## Sync Translations

Synchronize all translatable text sources with the localization database. This scans collections, fields, menus, plugins, and other system components to discover strings that can be translated.

```bash
curl -X POST "${NOCOBASE_URL}/api/localization:sync" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Run this after:
- Creating new collections or fields
- Installing or enabling plugins
- Modifying UI schema labels
- Any change that introduces new user-facing text

The sync operation is idempotent — running it multiple times does not create duplicates.

## List Translatable Texts

Retrieve all texts that have been synced and are available for translation.

```bash
curl -X GET "${NOCOBASE_URL}/api/localizationTexts:list?page=1&pageSize=50" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Supports query parameters:
- `page` / `pageSize` — pagination
- `filter` — filter by module, text content, or translation status

Each text entry includes:
- `id` — unique identifier for the text
- `module` — source module (e.g., `collections`, `menus`, `plugins`)
- `text` — the original (default language) string

### Filter by Module

```bash
curl -X GET "${NOCOBASE_URL}/api/localizationTexts:list?filter={\"module\":\"collections\"}" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### Filter by Text Content

```bash
curl -X GET "${NOCOBASE_URL}/api/localizationTexts:list?filter={\"text\":{\"$includes\":\"order\"}}" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

## Update or Create Translations

Create a new translation or update an existing one for a specific text and locale.

```bash
curl -X POST "${NOCOBASE_URL}/api/localizationTranslations:updateOrCreate" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "textId": 42,
    "locale": "uk-UA",
    "translation": "Замовлення"
  }'
```

Fields:
- `textId` (required) — the ID of the localization text (from `localizationTexts:list`)
- `locale` (required) — target locale code (e.g., `en-US`, `uk-UA`, `zh-CN`, `de-DE`, `fr-FR`, `ja-JP`)
- `translation` (required) — the translated string

This is an upsert operation: if a translation for the given `textId` + `locale` already exists, it is updated; otherwise a new translation is created.

## Publish Translations

Make all pending translation changes active in the running application.

```bash
curl -X POST "${NOCOBASE_URL}/api/localization:publish" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Translations are not visible to users until published. Always call publish after completing a batch of translation updates.

## Full Localization Workflow

Follow these steps to add or update translations for a locale.

### Step 1: Sync Sources

Ensure all translatable texts are discovered.

```bash
curl -X POST "${NOCOBASE_URL}/api/localization:sync" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### Step 2: List Available Texts

Get all texts that need translation.

```bash
curl -X GET "${NOCOBASE_URL}/api/localizationTexts:list?pageSize=100" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### Step 3: Create/Update Translations

For each text, provide the translated string.

```bash
# Translate "Orders" to Ukrainian
curl -X POST "${NOCOBASE_URL}/api/localizationTranslations:updateOrCreate" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "textId": 1,
    "locale": "uk-UA",
    "translation": "Замовлення"
  }'

# Translate "Customers" to Ukrainian
curl -X POST "${NOCOBASE_URL}/api/localizationTranslations:updateOrCreate" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "textId": 2,
    "locale": "uk-UA",
    "translation": "Клієнти"
  }'

# Translate "Status" to Ukrainian
curl -X POST "${NOCOBASE_URL}/api/localizationTranslations:updateOrCreate" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "textId": 3,
    "locale": "uk-UA",
    "translation": "Статус"
  }'
```

### Step 4: Publish

Apply all translations.

```bash
curl -X POST "${NOCOBASE_URL}/api/localization:publish" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

## Locale Codes

NocoBase uses standard BCP 47 locale codes. Common examples:

| Code | Language |
|------|----------|
| `en-US` | English (US) |
| `zh-CN` | Chinese (Simplified) |
| `zh-TW` | Chinese (Traditional) |
| `ja-JP` | Japanese |
| `ko-KR` | Korean |
| `uk-UA` | Ukrainian |
| `ru-RU` | Russian |
| `de-DE` | German |
| `fr-FR` | French |
| `es-ES` | Spanish |
| `pt-BR` | Portuguese (Brazil) |
| `ar-SA` | Arabic |
| `tr-TR` | Turkish |

## Important Notes

- **UI element labels come from UI schemas.** Do not edit schema `title` or `x-component-props.title` values to translate them. Instead, use the localization system which handles schema labels automatically after sync.
- **Sync is non-destructive.** Running sync does not remove existing translations — it only adds newly discovered texts.
- **Publish is global.** Publishing applies all pending translations across all locales at once.
- **Batch translations.** Make all translation updates first, then publish once at the end. Avoid publishing after every individual update.
- **Collection and field names** are translatable through this system. After creating a new collection, sync to make its name and field labels available for translation.
- **Plugin strings** are also translatable. After enabling a new plugin, sync to discover its UI strings.

## Common Automation Patterns

### Translate a Newly Created Collection

```
1. POST collections:create → create the collection
2. POST collections/{name}/fields:create → add fields
3. POST localization:sync → discover new translatable texts
4. GET localizationTexts:list?filter={"module":"collections"} → find the new texts
5. POST localizationTranslations:updateOrCreate → add translations for each text
6. POST localization:publish → apply translations
```

### Bulk Translation Import

When you have a batch of translations (e.g., from an external translation service):

```
1. POST localization:sync → ensure all texts are up to date
2. GET localizationTexts:list?pageSize=200 → get all text IDs
3. For each translation pair:
   POST localizationTranslations:updateOrCreate → upsert the translation
4. POST localization:publish → apply all at once
```

## Best Practices

1. **Sync before translating** — always run `localization:sync` before listing texts to ensure you have the latest sources.
2. **Batch then publish** — make all translation updates before calling publish.
3. **Use consistent locale codes** — stick to the standard BCP 47 format.
4. **Do not edit UI schemas for translation** — use the localization system instead.
5. **Sync after schema changes** — run sync after creating collections, fields, or modifying UI schemas.
6. **Paginate text lists** — large installations can have hundreds of translatable texts; use pagination.
7. **Track translation coverage** — compare `localizationTexts:list` count against translations per locale to find gaps.

## MCP note

The localization HTTP resources (`localization`, `localizationTexts`, `localizationTranslations`) have no dedicated `localization_*` tools. Access via the generic `resource_*` family:

```
resource_list({ resource: "localizationTexts", pageSize: 100 })
resource_create({
  resource: "localizationTranslations",
  values: { textId: 42, locale: "uk-UA", translation: "..." }
})
```

## See also

- `mcp-patterns` — generic resource access via `resource_*`
- `system-admin` — `app:getLang` and language-list endpoints
- `ux-constructor` — i18n in blueprint titles/labels
