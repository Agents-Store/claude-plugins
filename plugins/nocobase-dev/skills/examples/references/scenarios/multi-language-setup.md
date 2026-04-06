# Setting Up Multi-Language Support

End-to-end walkthrough for configuring NocoBase to support multiple languages and adding Ukrainian translations. This scenario covers checking the current language configuration, syncing translatable texts, creating translations, and publishing them.

## Prerequisites

- A running NocoBase V2 instance with API access
- The **setup** skill verification steps completed successfully
- The localization plugin enabled (check with `app:getPlugins`)
- At least one collection created (so there are texts to translate)

## Step 1 -- Check Current Language Setting

Verify the current application language and available languages.

```bash
curl -s -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/app:getLang"
```

**Expected response:**

```json
{
  "data": "en-US"
}
```

This returns the current default language. If you need to add Ukrainian as an enabled language, update system settings:

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/systemSettings:update" \
  -d '{
    "enabledLanguages": ["en-US", "uk-UA"]
  }'
```

Check the full system settings to see all configured languages:

```bash
curl -s -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/systemSettings:get"
```

## Step 2 -- Sync Translations

Synchronize all translatable text sources. This scans collections, fields, menus, and plugins to discover every string that can be translated.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/localization:sync"
```

**Expected response:** A success confirmation. The operation is idempotent -- running it multiple times does not create duplicates.

Always run sync before listing texts, especially after:
- Creating new collections or fields
- Enabling or disabling plugins
- Modifying UI schema labels or menu items

## Step 3 -- List Translatable Texts

Retrieve all texts available for translation.

### List All Texts

```bash
curl -s -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/localizationTexts:list?page=1&pageSize=50"
```

**Expected response:**

```json
{
  "data": [
    {
      "id": 1,
      "module": "collections",
      "text": "Companies"
    },
    {
      "id": 2,
      "module": "collections",
      "text": "Contacts"
    },
    {
      "id": 3,
      "module": "collections",
      "text": "Deals"
    },
    {
      "id": 4,
      "module": "collections",
      "text": "Company Name"
    },
    {
      "id": 5,
      "module": "collections",
      "text": "Industry"
    }
  ],
  "meta": {
    "count": 42,
    "page": 1,
    "pageSize": 50,
    "totalPage": 1
  }
}
```

Note the `id` values -- you need them to create translations.

### Filter by Module

To see only collection-related texts:

```bash
curl -s -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/localizationTexts:list?filter={\"module\":\"collections\"}&pageSize=100"
```

### Search for Specific Text

Find texts containing a specific word:

```bash
curl -s -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/localizationTexts:list?filter={\"text\":{\"$includes\":\"Company\"}}&pageSize=50"
```

## Step 4 -- Add Ukrainian Translations

Create translations for each text entry. Use the `textId` from Step 3 and the target locale `uk-UA`.

### Translate Collection Names

```bash
# "Companies" -> "Компанії"
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/localizationTranslations:updateOrCreate" \
  -d '{
    "textId": 1,
    "locale": "uk-UA",
    "translation": "Компанії"
  }'
```

```bash
# "Contacts" -> "Контакти"
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/localizationTranslations:updateOrCreate" \
  -d '{
    "textId": 2,
    "locale": "uk-UA",
    "translation": "Контакти"
  }'
```

```bash
# "Deals" -> "Угоди"
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/localizationTranslations:updateOrCreate" \
  -d '{
    "textId": 3,
    "locale": "uk-UA",
    "translation": "Угоди"
  }'
```

### Translate Field Labels

```bash
# "Company Name" -> "Назва компанії"
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/localizationTranslations:updateOrCreate" \
  -d '{
    "textId": 4,
    "locale": "uk-UA",
    "translation": "Назва компанії"
  }'
```

```bash
# "Industry" -> "Галузь"
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/localizationTranslations:updateOrCreate" \
  -d '{
    "textId": 5,
    "locale": "uk-UA",
    "translation": "Галузь"
  }'
```

### Batch Translation Pattern

For efficiency, script all translations in sequence. Here is a representative batch covering common CRM terms:

```bash
# Collection names
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/localizationTranslations:updateOrCreate" \
  -d '{"textId": 1, "locale": "uk-UA", "translation": "Компанії"}'

curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/localizationTranslations:updateOrCreate" \
  -d '{"textId": 2, "locale": "uk-UA", "translation": "Контакти"}'

curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/localizationTranslations:updateOrCreate" \
  -d '{"textId": 3, "locale": "uk-UA", "translation": "Угоди"}'

# Field labels
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/localizationTranslations:updateOrCreate" \
  -d '{"textId": 4, "locale": "uk-UA", "translation": "Назва компанії"}'

curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/localizationTranslations:updateOrCreate" \
  -d '{"textId": 5, "locale": "uk-UA", "translation": "Галузь"}'
```

**Important:** The `textId` values above are examples. Your actual text IDs will differ based on what texts exist in your instance. Always run `localizationTexts:list` first to get the correct IDs.

The `updateOrCreate` endpoint is an upsert -- if a translation for the given `textId` + `locale` already exists, it is updated; otherwise a new one is created. This makes it safe to run the same translation batch multiple times.

## Step 5 -- Publish Translations

Make all pending translations active in the running application.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/localization:publish"
```

**Important:** Translations are not visible to users until published. Always publish after completing a batch of translation updates.

Publishing is global -- it applies all pending translations across all locales at once. There is no per-locale publishing.

## Step 6 -- Verify Translations Are Active

### Check Application Language

Verify that Ukrainian is available as a language option:

```bash
curl -s -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/systemSettings:get"
```

Look for `"enabledLanguages"` containing `"uk-UA"`.

### Verify by Syncing Again

Run another sync to confirm all texts are up to date, then list texts to check translation coverage:

```bash
# Sync to ensure everything is current
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/localization:sync"

# List texts to review (all should now have Ukrainian translations)
curl -s -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/localizationTexts:list?filter={\"module\":\"collections\"}&pageSize=100"
```

### Test in the UI

Switch the NocoBase UI language to Ukrainian (uk-UA) in the user profile settings or by passing the locale parameter. Collection names, field labels, and other translated strings should now appear in Ukrainian.

## Common Ukrainian Translations for Reference

Here is a reference table of common NocoBase UI terms in Ukrainian:

| English | Ukrainian |
|---------|-----------|
| Companies | Компанії |
| Contacts | Контакти |
| Deals | Угоди |
| Tasks | Завдання |
| Orders | Замовлення |
| Products | Продукти |
| Users | Користувачі |
| Status | Статус |
| Name | Назва |
| Title | Заголовок |
| Description | Опис |
| Email | Електронна пошта |
| Phone | Телефон |
| Created At | Створено |
| Updated At | Оновлено |
| Industry | Галузь |
| Website | Вебсайт |
| Priority | Пріоритет |
| Notes | Нотатки |
| Active | Активний |
| Inactive | Неактивний |
| Open | Відкрито |
| Closed | Закрито |

## Summary

This scenario demonstrated the complete localization workflow:

1. **Checked** the current language settings with `app:getLang` and `systemSettings:get`
2. **Enabled** Ukrainian as an available language in system settings
3. **Synced** translatable text sources with `localization:sync`
4. **Listed** available texts with `localizationTexts:list`
5. **Created** Ukrainian translations with `localizationTranslations:updateOrCreate`
6. **Published** translations with `localization:publish`
7. **Verified** translations are active

The process follows the strict sequence: sync -> list -> translate -> publish. This sequence works for any locale, not just Ukrainian.

## Adding More Languages

To add another language (e.g., German), repeat the process:

1. Add `"de-DE"` to `enabledLanguages` in system settings.
2. Sync texts (if not already synced).
3. Create translations with `locale: "de-DE"` for each `textId`.
4. Publish.

Each locale's translations are independent. You can translate different subsets of texts for different locales.
