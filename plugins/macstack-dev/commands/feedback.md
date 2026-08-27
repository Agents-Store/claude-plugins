---
description: Report a problem with macstack-dev, the macstack.json schema, or the registry — and fix it at the source
argument-hint: <what went wrong>
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep, Skill, WebFetch]
---

Use `macstack-dev:feedback` to route the fix, then apply it **at the source**. A fix
applied to a mirror is silently overwritten by the next sync.

| What broke | Where it is fixed |
|---|---|
| A skill's instructions, the folder convention, the merge loop | this plugin |
| The document shape, a table that should be a list, a language rule | this plugin, `documents` and `doc-contracts.json` |
| The schema, a field, an enum, a lint rule of the standard | `macstacks/macstack` |
| A software category, a coverage area | `macstacks/registry` |

When the schema changes, all three copies change together: the canon, the vk-ops
mirror and this plugin's bundled fallback. Verify with
`gh api repos/macstacks/macstack/contents/<path>?ref=main`, never with a plain `curl`
against the CDN right after a push — it serves the previous revision and prints a full,
entirely false diff, and the obvious reaction to that diff is to overwrite what you
just published.

Record what was learned in `LEARNINGS.md`: problem, fix, root cause, severity.
