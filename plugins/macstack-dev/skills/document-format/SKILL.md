---
name: document-format
description: This skill should be used before writing, seeding, migrating or reviewing ANY document under macstack/ — when the user asks to "write the user cases", "add a screen", "add a trigger", "fix the document format", "why is this a table", "make the documents readable", or when any other skill of this plugin is about to create or edit a file in client/, generated/ or history/. Defines the entity + YAML + anchored-prose shape, the table budget, and the language rule.
---

# How a macstack document is shaped

Every document under `macstack/` is written the same way, whatever it is about.
A client reads the prose; a parser reads the anchors and the YAML. Neither
format is bent to serve the other.

Structure is declared once in
`${CLAUDE_PLUGIN_ROOT}/skills/documents/references/doc-contracts.json` — read it
rather than this file when you need the exact sections and YAML keys for a given
document. This skill is the *why* and the shape; the contract is the *what*.

## The shape

One entity — one heading with an id, one anchor above it, one YAML block under
it, prose below in anchored sections.

````markdown
<!-- macstack:case=C-04 -->
### C-04 · Check in to a session

```yaml
role: coach
priority: critical
screens: [coach-today]
triggers: [trg-entry-form]
```

<!-- macstack:flow -->
**How it goes**
1. Opens the "Today" screen.
2. Presses "Start session".

<!-- macstack:experience -->
**What the experience must be**
- Reachable in one tap from the first screen.
- With geolocation denied, the warning explains the consequence and does not read as a refusal.

<!-- macstack:acceptance -->
**Done when**
- the check-in is stored with an exact timestamp;
- a second check-in on the same session is impossible.
````

Three rules make this work and they are not negotiable:

1. **Anchors and YAML keys are ASCII and never translated.** Headings and prose
   follow `docs.language`. This is what lets one parser read a Russian document
   and a German one.
2. **The YAML block is the machine interface.** Exactly one per entity,
   immediately after the heading, before any prose. A key the contract does not
   declare for that entity kind is an error, not an extension.
3. **Prose sections are found by anchor, never by heading text.** `**Done when**`
   is for the reader; `<!-- macstack:acceptance -->` is for the checker.

## The table budget

A table is allowed only when **all** of these hold:

- at most 4 columns
- every cell at most 80 characters
- at least 3 rows
- no `<br>`, no bold, no code fence, no pipe inside a cell

Anything else is a list or a YAML block. Document journals are exempt — they are
`| date | what changed |` and stay that way.

This is not a style preference. Every oversized table measured in the field
started as a reasonable one and grew a paragraph at a time: a live project
reached 56 tables across 20 documents, cells up to 1353 characters, and one
client-facing document at six columns by thirty-seven rows of 600–880 characters
a row. Nobody reads that, and the client it was written for could not correct it.

**A cell wants to be a section.** When you catch yourself writing `<br>` inside a
cell, or bolding half of it, the table has already failed — convert it.

## Never hand-write an index

An index, a summary or a coverage count inside an authored document is a second
copy of the content below it. The same project printed all 63 of its cases twice
— once as index rows, once as headings, with zero divergence — which is 15% of
the file existing only to be kept in sync by hand.

Indexes are generated into `generated/INDEX.md`. If you want one, run `render`.

## Language

Prose follows `docs.language`. Terminology stays English, always:

- ids, YAML keys, anchors
- role ids, entity names, workflow names
- statuses and enum values
- file paths
- the whole of `macstack.json`

A domain term gets its English original in parentheses at first mention, and the
mapping is collected in the `glossary` section of `client/OVERVIEW.md`.

Lint measures the ratio of letters from the wrong alphabet outside code spans,
YAML blocks, anchors and ID tokens. Past 15% it is an error. The rule exists
because a live project ran `docs.language: ru` with one client document 100%
English and another at 21% Cyrillic — Russian headings over an English body
copied out of the spec. Both read as finished documents; neither was one.

Tool output follows `docs.language` too — the scripts share
`skills/documents/references/i18n.py`.

## Every edit is journalled

Every document carries a `journal` section. An edit appends a row **and** bumps
the version in three places that must agree: the document's `<!-- macstack:doc -->`
header, the last journal row, and `docs.files.<key>.version` in `macstack.json`.
Lint 12.5 checks all three; a mismatch is an error, not a warning.

`updated` is when the text changed. `reviewed` is when the document was last
checked **against the code**. They are different facts and conflating them is how
a document stays confidently wrong.

## What to read next

| You are about to | Read |
|---|---|
| Write or repair a document | `documents` |
| Add a case, screen or trigger | this file, then the contract |
| Check a document | `lint` rules 12.21, 12.24, 12.25 |
| Convert an old table-shaped document | `documents`, migration mode |

Full templates for every document type, with a worked before/after conversion:
`${CLAUDE_PLUGIN_ROOT}/skills/document-format/references/format-rules.md`.
