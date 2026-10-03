---
description: Set up document generator preferences — style, language, company profile, and logo.
allowed-tools: ["Bash", "Read", "Write"]
argument-hint: ""
---

# Document Generator Setup

Run the onboarding interview to configure document generation preferences.

## Steps

1. **Check existing preferences:**
   ```bash
   cat ~/.document-generator/preferences.json 2>/dev/null
   ```
   If preferences already exist, ask the user if they want to update them or start fresh.

2. **Check dependencies:**
   ```bash
   node "${CLAUDE_PLUGIN_ROOT}/scripts/check_deps.js"
   ```
   If `ready` is false, show the user what is missing and ask permission to run the listed `installCommands`. (`ready` covers Node, the npm modules and the Playwright browser; pandoc and the PDF engines are optional extras listed in `missing`.)

3. **Run the onboarding interview** from the **user-preferences** skill:
   - Ask about preferred document style (show 5+ presets with descriptions)
   - Ask about default language (en, uk, de, fr, es)
   - Optionally collect company information (name, address, phone, email, website, registration/tax ID)
   - Optionally collect company logo (file path → validate → convert to base64 → store)
   - Optionally set formatting preferences (paper size A4/Letter, currency symbol, date format)

4. **Save preferences** to `~/.document-generator/preferences.json`

5. **Confirm setup is complete** and show a summary of what was configured.

## Notes

- This command can be run at any time to update preferences
- Use the **user-preferences** skill for the full onboarding flow details
- Preferences are stored at `~/.document-generator/preferences.json`
- Logos are stored at `~/.document-generator/logos/`
