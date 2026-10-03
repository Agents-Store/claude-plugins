---
description: Fetch the shadcn registries from the official endpoint (skipping unavailable and hidden ones) and add them to components.json
argument-hint: [--filter <keyword>]
allowed-tools: [Read, Write, Edit, Bash, WebFetch]
---

# Add Registries

Fetch the list of shadcn-compatible registries from the official endpoint and populate the project's `components.json`. The CLI already resolves `@registry/item` for any directory entry without this step — the bulk add exists so the shadcn MCP (which only searches registries listed in `components.json`) can see them.

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
   The fetch-and-merge flow below remains the way to add the whole directory in bulk.

3. Parse the JSON response. Each entry has:
   - `name` — e.g. `"@magicui"`
   - `url` — e.g. `"https://magicui.design/r/{name}.json"`
   - `description` — brief text
   - `health` — `status` (`healthy` | `degraded` | `unavailable` | `observing`) and `hidden`

4. If `$ARGUMENTS` contains `--filter <keyword>`, only include registries whose `name` or `description` contains the keyword (case-insensitive).

5. Read the current `components.json` and extract the existing `"registries"` object (may be empty or missing).

6. Build the new registries object by merging existing entries with the fetched ones. **Skip every registry whose `health.status` is `unavailable` or whose `health.hidden` is true** — on 2026-10-02 that was 39 of 418 entries, none of which install. Keep `degraded` ones but count them for the report. For each remaining registry:
   - Key: the `name` field (e.g. `"@magicui"`)
   - Value: the `url` field (e.g. `"https://magicui.design/r/{name}"`)
   - Do NOT clobber existing **object-valued** entries (registries with `headers`/`params` auth, e.g. shadcn studio premium) — the merge must preserve those objects as-is.

7. Write the merged `"registries"` back to `components.json`. Preserve all other fields. (Registries can also live in `package.json#registries` since CLI 4.18 — this command only writes `components.json`.)

8. Report: how many registries were added (new), already present (kept), skipped as unavailable/hidden, and how many of the added ones are `degraded`.

## Example Output

```
Fetched 418 registries from https://ui.shadcn.com/r/registries.json
Skipped 39 unavailable/hidden registries
Added 374 new registries to components.json (41 of them degraded)
Kept 5 already configured
Total registries in components.json: 379
```
