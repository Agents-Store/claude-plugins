---
name: client-package
description: This skill should be used when the user asks to "send the cases to the client", "give the client something to edit", "собрать пакет для клиента", "отдать клиенту на согласование", "prepare the user cases for review", or needs the outbound half of the client loop — turning USER-CASES.md and BUSINESS-LOGIC.md into one file a client can annotate and send back.
---

# Hand the client something they can actually edit

The inbound half of the loop has always worked: client material lands in `inbox/`, a delta
analyses it, rulings decide it, `USER-CASES.md` absorbs it. **The outbound half did not
exist.** Nobody sends a client an 88 KB markdown file and expects edits back, so in practice
the client writes a fresh document of their own and somebody transcribes it by hand — which
is where a hundred small changes go missing.

This skill builds one self-contained HTML: every acceptance bullet numbered, with an empty
box beside it to write in. It opens in any browser, prints to PDF, and needs nothing
installed.

## Run it

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/client-package/references/package.py" macstack \
        [--date YYYY-MM-DD] [--slug user-cases]
```

Writes `macstack/handoffs/<date>-<slug>.html` and prints a ready `handoff` entry. **Append
that entry to `log.md`** — lint rule 12.20 requires it, and it is the only record of which
version the client actually reviewed.

## `handoffs/` is immutable, and that is what makes the numbers work

Bullet numbers (`C-04.2`) are **positional within one package**, not global ids.
`USER-CASES.md` does not carry them, so inserting a bullet shifts everything below it in the
next package.

That is safe for exactly one reason: **the handoff file never changes.** A comment written on
`2026-08-24-user-cases.html` is resolved against that file, which still exists, byte for byte,
with the numbering the client saw. Regenerating for a new round writes a new dated file; it
never overwrites the old one.

So: never edit a file in `handoffs/`, and never present these numbers to anyone as stable
identifiers. If a client cites `C-04.2` six months later, open the package they were sent —
not today's document.

## The return trip needs nothing new

The client sends the file back. It lands in `inbox/` like any other incoming material, with an
`intake` entry, and from there the existing `docs-merge` loop takes over: delta → rulings →
`USER-CASES.md`. Do not build a second path for returned packages — the one that exists is the
best-tested part of this plugin, and a parallel one would be a second place for a client's
change to get lost.

## What goes in, and what deliberately does not

**In:** `BUSINESS-LOGIC.md` first, as context in plain words, then every case with its intro,
priority and acceptance bullets, grouped by the same sections the document uses.

**Not in:** `OPEN-QUESTIONS.md`, `DECISIONS.md`, `TASKS.md`, `ROLES.md`, `ARCHITECTURE.md`,
`reviews/`. Some of it is internal, some of it would invite the client to re-open decisions
already taken, and all of it makes the package longer without making it more answerable. A
package the client does not finish reading produces fewer corrections, not more.

If a client genuinely needs to see the open questions, send `OPEN-QUESTIONS.md` §A separately —
it is written for exactly that and is short.

## Language

Taken from `docs.language`. A client-facing document is the one place to confirm the language
before sending rather than after.
