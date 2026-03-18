---
description: Generate a professional presentation (PPTX)
allowed-tools: ["Bash", "Read", "Write", "Glob"]
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

1. **Resolve plugin directory:**
   Find the plugin dir by globbing for `**/document-generator/scripts/generate_pptx.js`.

2. **Check dependencies:**
   ```bash
   cd <plugin_dir> && node -e "require('pptxgenjs')" 2>&1
   ```

3. **Gather required data from user:**
   - Subtitle (optional)
   - Author/presenter name
   - Audience context (who is this for?)
   - Key topics/agenda items
   - Content for each slide (bullets, key points)
   - Optional: images, charts, branding colors

4. **Read template:**
   ```bash
   cat <plugin_dir>/templates/presentation_template.json
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
   cd <plugin_dir> && node scripts/generate_pptx.js /absolute/path/.doc_input.json
   ```

7. **Deliver result:**
   Show file path, size, and number of slides generated.

## Example Usage
```
/generate-presentation "Product Launch Strategy" --slides 10 --theme corporate
/generate-presentation "Q1 Review" --theme minimal
```
