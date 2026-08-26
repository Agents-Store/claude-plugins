---
description: Give the client the documents to read and answer — a self-contained HTML file, a published page, or both — and take their answers back
argument-hint: [--read | --html | --artifact | (empty = both)]
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep, Skill, Artifact]
---

Use `macstack-dev:client-package`.

The inbound half of the client loop always worked. This is the outbound half: nobody
sends a client an 88 KB markdown file and expects edits back, so in practice the client
writes a document of their own and somebody transcribes it by hand — which is where a
hundred small changes go missing.

## Building — no argument, or `--html` / `--artifact`

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/client-package/references/package.py" macstack \
  [--slug <name>] [--artifact]
```

The package carries the client's own documents, section by section, as prose — **not a
checklist**. Acceptance bullets are test cases: they are written for a machine and live
inside their case as part of it. A package that flattens them into hundreds of separate
questions is an interrogation, not a document, and the client stops reading.

Eight sections: what the product is · goals · who does what · what starts work and who
does it · what must be delivered · questions for you · screens · how to use it.

The unit the client answers is the **entity** — a case, a screen, a trigger, a question.
Each carries its permanent id (`C-04`), which does not change between rounds, so a
comment quoted six months later still lands on the same thing.

`--artifact` also builds the version for publishing. Publish it with the Artifact tool,
then paste the URL into the `handoff` row the script prints.

`history/handoffs/` is immutable for the same reason `inbox/` is: the client's answers
come back against THAT file. A new round writes a new dated file.

## Reading the answers back — `--read`

The client presses **"Collect my answers"** at the bottom of the page and sends you the
text. It does not matter which channel: the HTML file, the published page, an email, a
message. One path for all of them — a second path for returned packages is a second
place for a client's change to get lost.

Take what they sent and run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/client-package/references/package.py" macstack \
  --read <file.json> [--dry]
```

**If the client pasted the answers into this chat instead of a file** — which is the
common case — write them to `macstack/inbox/<date>-answers.json` first, then read that.
The inbox keeps what the client actually sent, unedited, and `--read` is then reading a
file like any other.

`--dry` prints what would be recorded and writes nothing. Use it first when the text
came from a chat and might be truncated.

Every answer becomes a row in `history/ledger.jsonl`, including a plain "right":
silent agreement and no answer at all look identical otherwise, and they are different
things — the first means somebody read it and agreed.

## What the next round then does by itself

The next package shows, under each piece the client answered:

- what they said, with the date;
- their previous verdict, **pre-selected and still changeable**. Locking a client into
  an old answer is wrong: the document may have moved, and a "right" from six months ago
  can stop being right.

An answer the client did not touch and did not comment on is not sent back a second
time. Otherwise every round returns all two hundred answers and it becomes impossible
to see what they actually reconsidered.

## Then

Answers that ask for a change are ordinary incoming material: run
`/macstack-dev:intake`, which owns the delta → ruling → apply loop. Do not apply a
client's comment straight to a document — a comment is a request, and what it costs to
be wrong about it is decided by the owner, not by this session.
