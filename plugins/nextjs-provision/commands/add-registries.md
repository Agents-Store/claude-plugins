---
description: Fetch all 260+ shadcn registries from the official endpoint and add them to components.json
argument-hint: [--filter <keyword>]
allowed-tools: [Read, Write, Edit, Bash, WebFetch]
---

# Add Registries

Fetch the complete list of shadcn-compatible registries from the official endpoint and populate the project's `components.json`.

## Instructions

1. Verify `components.json` exists in the project root. If not, ask whether to run `npx shadcn@latest init` first.

2. Fetch the official registry list:
   ```bash
   curl -s https://ui.shadcn.com/r/registries.json
   ```
   Or use WebFetch on `https://ui.shadcn.com/r/registries.json`.

2b. For a handful of registries, the native CLI command is an alternative to the fetch-and-merge flow:
   ```bash
   npx shadcn registry add @name=https://domain.com/r/{name}.json @name2=https://other.com/r/{name}.json
   ```
   The fetch-and-merge flow below remains the way to add all 260+ in bulk.

3. Parse the JSON response. Each entry has:
   - `name` — e.g. `"@magicui"`
   - `url` — e.g. `"https://magicui.design/r/{name}.json"`
   - `description` — brief text

4. If `$ARGUMENTS` contains `--filter <keyword>`, only include registries whose `name` or `description` contains the keyword (case-insensitive).

5. Read the current `components.json` and extract the existing `"registries"` object (may be empty or missing).

6. Build the new registries object by merging existing entries with the fetched ones. For each fetched registry:
   - Key: the `name` field (e.g. `"@magicui"`)
   - Value: the `url` field (e.g. `"https://magicui.design/r/{name}"`)
   - Do NOT clobber existing **object-valued** entries (registries with `headers`/`params` auth, e.g. shadcn studio premium) — the merge must preserve those objects as-is.

7. Write the merged `"registries"` back to `components.json`. Preserve all other fields.

8. Report: how many registries were added (new) vs already present (skipped).

## Example Output

```
Fetched 267 registries from https://ui.shadcn.com/r/registries.json
Added 262 new registries to components.json
Skipped 5 already configured
Total registries in components.json: 265
```
