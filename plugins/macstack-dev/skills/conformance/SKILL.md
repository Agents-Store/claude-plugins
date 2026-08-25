---
name: conformance
description: This skill should be used when the user asks to "check the implementation against the documents", "audit the platform", "does the code do what the spec says", "test the whole stack against the requirements", "conformance review", "what is actually built", or runs /macstack-dev:check --code. Produces a dated audit pair — a technical conformance review and its business-language twin — with one verdict per case id.
---

# Audit the implementation against the documents

Every other check in this plugin asks whether the documents are well formed. This one
asks whether they are **true**.

It is read-only against the source tree and writes exactly two files, both dated, both
into `history/reviews/`:

```
history/reviews/<date>-<slug>-conformance.md   the technical audit
history/reviews/<date>-<slug>-business.md      its business-language twin
```

The twin is not optional. It shipped as a WARNING "until a generator exists" for three
releases; the generator is this skill. An audit only an engineer can read is an audit
the person paying for the platform cannot act on.

## What it reads

| Source | What it asks of the code |
|---|---|
| `client/USER-CASES.md` | does each acceptance bullet hold? |
| `client/UX-UI.md` | is each `forbidden` item actually unreachable on that screen? |
| `client/AUTOMATION.md` | does each trigger exist, fire from the declared source, and raise what it claims? |
| `generated/TEST-CASES.md` | which of these are already proven by a named test, and which need a human? |
| `generated/ARCHITECTURE.md` | **the map** — where to look |

Use the architecture document as the map. A blind recursive `grep` over `src/` is the
wrong instrument twice over: it finds the word rather than the behaviour, and in an
iCloud-backed folder it hangs for minutes on files that are not local. Read the map,
open the files it names, and fall back to a scoped search only when the map is silent —
which is itself a finding.

## Verdicts

One per case id, from a closed set. `plan` reads these to tell real work from a document
nobody has checked, and it can only do that if "done" is one token rather than six
phrasings of it.

- **`implemented`** — the behaviour exists and something proves it.
- **`partial`** — part of the acceptance list holds and part does not. Name which
  bullets, by id.
- **`absent`** — nothing in the code answers this case.
- **`externally-blocked`** — the code is complete and cannot be exercised because
  something outside it is missing: a credential, a client input, a third-party account.
  Name the `A<n>` it waits on.

A verdict without evidence is an opinion. Evidence cites a **test title** or a named
symbol — never `file.ts:120`, which is banned outright because line numbers rot the
moment the file above them grows.

## The two documents

**The technical one** carries a finding per case: the verdict, the surfaces that
implement it, the evidence, and what remains. Its `counts` section is the arithmetic —
per role and in total, how many of each verdict, and how many acceptance bullets have no
test at all.

**The twin** answers the same question without a single file path in it: which parts of
the platform do what was agreed, which do not yet, and what the client has to supply for
the blocked ones to move. Same date, same slug, same commit. It is written from the
findings, not from a second pass over the code — two independent readings would
eventually disagree, and then nobody knows which one to believe.

## What it does NOT do

- **It does not fix anything.** The output is a verdict and a list; the fix is
  `/macstack-dev:plan` and then a coding session.
- **It does not move `reviewed` dates by itself** for documents it did not actually
  check. A review dated later than `reviewed` moves that date forward — but only for the
  documents whose content this run examined. Marking all six because one was audited is
  how a document goes stale while lint stays green.
- **It does not invent a test.** A bullet that cannot be verified because the case never
  names the fact needed to verify it is a hole in `USER-CASES.md`, not in the tests. Say
  that, and stop.

## Feeding the loop

The newest conformance review is what `/macstack-dev:plan` reads before reporting a
work list. Measured when this link was first built: a gap report that ignored the audit
announced 63 unplanned cases where 35 were already confirmed implemented. Reading the
verdicts cut it to 8. **A gap report that ignores what has already been checked reports
the size of the document, not the size of the work.**

## Running it from another agent

The procedure above names no tool that only one coding agent has. It is a document set,
a map and a set of verdicts, and a session in Codex or any other agent reads them the
same way — which is the point of `/macstack-dev:start` writing the spec block into both
`CLAUDE.md` and `AGENTS.md`.
