---
description: Generate a professional presentation (PPTX)
allowed-tools: ["Bash", "Read", "Write"]
argument-hint: <title> [--slides <number>] [--theme <corporate|minimal|bold>]
---

# Generate Presentation

Generate a professional PowerPoint presentation with title slide, agenda, content slides, and summary.

## Arguments

Format: `<title> [--slides <number>] [--theme <corporate|minimal|bold>]`
- title: Presentation title (required)
- --slides: Approximate number of content slides (optional, default: auto)
- --theme: Color theme (optional, default: corporate)

Parse from "$ARGUMENTS".

## Process

1. **Plugin directory:**
   Scripts and templates live under `${CLAUDE_PLUGIN_ROOT}` (Claude Code substitutes it with the installed plugin path). Use it as is; do not search for the plugin.

2. **Check dependencies:**
   ```bash
   node "${CLAUDE_PLUGIN_ROOT}/scripts/check_deps.js"
   ```
   If `ready` is false, show what is missing and ask permission to run the listed `installCommands`.

3. **Gather required data from user:**
   - Subtitle (optional)
   - Author/presenter name
   - Audience context (who is this for?)
   - Key topics/agenda items
   - Content for each slide (bullets, key points)
   - Optional: images, charts, branding colors

4. **Read template:**
   ```bash
   cat "${CLAUDE_PLUGIN_ROOT}/templates/presentation_template.json"
   ```

5. **Build slide array:**
   Construct slides based on user content:
   - First slide: type "title"
   - Second slide: type "agenda" (from topics list)
   - Content slides: type "content" or "two-column" per topic
   - Optional: type "chart" for data visualization
   - Second-to-last: type "summary" with key takeaways
   - Last: type "contact" (optional)

6. **Generate PPTX:**
   ```bash
   node "${CLAUDE_PLUGIN_ROOT}/scripts/generate_pptx.js" /absolute/path/.doc_input.json
   ```

7. **Deliver result:**
   Show file path, size, and number of slides generated.

## Example Usage
```
/document-generator-ops:generate-presentation "Product Launch Strategy" --slides 10 --theme corporate
/document-generator-ops:generate-presentation "Q1 Review" --theme minimal
```
