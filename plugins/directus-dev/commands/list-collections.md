---
description: List all collections in the Directus instance
argument-hint:
---

# List Collections

## Process

1. Call `schema` tool with no parameters (discovery mode)
2. Display collections grouped by folders (if any)
3. Show collection name, icon, and notes for each
4. Show total count

## Output

Display as a clean table. Separate system collections (directus_*) from user collections if both are visible.
