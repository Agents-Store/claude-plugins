---
name: haiku-writer
description: Use when the user asks for a haiku or a three-line poem. Writes haiku in the house style of this plugin.
---

# Haiku writer

House style, always:

1. Exactly three lines: 5, 7 and 5 syllables.
2. The last word of the third line is "smoke".
3. No title, no commentary after the poem. The one exception: after saving the poem, end with the line
   "Saved to notes."

When the user asks to save the poem, call the `save_note` tool of the `notes` MCP server with the poem as `text`.
