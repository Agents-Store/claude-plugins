---
name: client-package
description: This skill should be used when the user asks to "send the documents to the client", "give the client something to comment on", "собрать пакет для клиента", "отдать клиенту на согласование", "показать клиенту артефакт", or needs either half of the client loop — turning the six client documents into one page a client can read and answer, and taking their answers back into the ledger.
---

# Hand the client something they can actually read and answer

Nobody sends a client an 88 KB markdown file and expects edits back. In practice the client
writes a document of their own and somebody transcribes it by hand — which is where a hundred
small changes go missing.

This skill builds one self-contained HTML page from the six client documents, and reads the
answers back. It opens in any browser, prints to PDF, and needs nothing installed.

## Build

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/client-package/references/package.py" macstack \
        [--date YYYY-MM-DD] [--slug user-cases] [--artifact]
```

Writes `macstack/history/handoffs/<date>-<slug>.html` and records itself in the ledger as a
`handoff` row. That row is what the NEXT package measures "changed since you last read this"
against — without it the next round marks either everything or nothing.

`--artifact` builds the version for publishing. Publish it with the Artifact tool and put the
URL into the handoff row.

## What the client sees

**Whole entities, as prose.** A case reads as a case: what it is, who does it, what has to be
true when it is done. Acceptance bullets stay inside their case, as part of it.

Acceptance bullets are test cases — written for a machine. A package that flattens them into
hundreds of separate questions is an interrogation, not a document, and the client stops
reading. One answer per entity, not one per bullet.

Eight sections: what the product is · goals · who does what · what starts work and who does
it · what must be delivered · questions for you · screens · how to use it.

**Closed questions do not go in.** Six of the questions in `OPEN-QUESTIONS.md` are struck
through and marked CLOSED; asking them again spends attention the client has a fixed amount
of. Lint rule 12.6 already says the same thing.

## Permanent ids, and why `handoffs/` is immutable

The id on an entity (`C-04`) comes from the document, not from its position in the package.
It does not move when something is inserted above it, so a client quoting `C-04` from a
six-month-old email lands on the same thing.

The handoff file still never changes: the client's answers come back against THAT file. A new
round writes a new dated file, and refuses to overwrite an existing one. Never edit a file in
`handoffs/`.

## Read the answers back

The client presses **"Собрать мои ответы"** at the bottom of the page and sends you the text.
Channel does not matter — file, email, message, or pasted into the chat. If it came through
the chat, write it to `macstack/inbox/<date>-answers.json` first: the inbox is what gives a
correction a traceable source.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/client-package/references/package.py" macstack \
        --read <file.json> [--dry]
```

`--dry` prints what would be recorded and writes nothing.

Every answer becomes a `comment` row in `history/ledger.jsonl` with a `verdict` field —
including a plain "верно". Silent agreement and no answer at all look identical otherwise,
and they are not the same thing: one means somebody read it and agreed.

## What the next round then does by itself

Under each entity the client answered, the next package shows what they said with its date,
and pre-selects their previous verdict — **still changeable**. Locking a client into an old
answer is wrong: the document may have moved since, and a "верно" from six months ago can
stop being true.

An answer the client did not touch is not re-asked. Otherwise every round returns all two
hundred answers and nobody can see what actually got reconsidered.

## Then it is ordinary incoming material

An answer that asks for a change goes through `intake`: delta → ruling → apply. Do not put a
client's comment straight into a document. A comment is a request; what it costs to be wrong
about it is the owner's call, not this session's.

## Language

The page follows `docs.language`. Ids and keys stay Latin. The client never sees a key.
