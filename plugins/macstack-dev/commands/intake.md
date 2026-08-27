---
description: Take in anything the client sends — a document, a returned review package, or a correction typed straight into this chat — and merge it through delta → ruling → apply
argument-hint: [file in inbox/ | what to change, in your own words | (empty = whatever is unprocessed)]
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep, Skill]
---

Use `macstack-dev:intake`. It owns the loop; this command only routes into it.

## Three ways material arrives, one loop

1. **A file in `inbox/`** — a PDF, a spec, a screenshot, a spreadsheet. Anything.
2. **A stray file that appeared in `client/`** — anything there that is not one of the
   six documents is incoming material, not a document. Move it to `inbox/` first.
3. **Text typed into this chat.** "убери геолокацию", "клиент сказал, что счета должны
   выходить 5-го". Write it to `inbox/<date>-<slug>.md` before doing anything else.

The third is the one people forget to record. A correction that exists only in a chat
transcript has no source: six months later nobody can say who asked for it or when, and
the document says something nobody can trace. Write it down first, then work.

## The loop, and none of it is optional

1. **Land it.** The file goes into `inbox/` under an ASCII name and gets an entry in the
   manifest. A source already committed in this repo is cited by path, never copied.
   Nothing in `inbox/` is ever edited afterwards.

2. **Read it.** Check size and first bytes before parsing — an iCloud placeholder reads
   as empty and yields a confidently wrong delta. `.xlsx` is refused: ask for a CSV
   beside it and write no log entry, so the file stays in the unprocessed set.

3. **Work out the delta.** Contradictions with what the documents already say, and
   additions. For each contradiction: what it touches, and what it costs if we choose
   wrong. A delta is a proposal, not an edit.

4. **Ask, then decide.** Every contradiction goes to the owner as a question with two
   real options: the recommendation you would defend, and "write it into
   `OPEN-QUESTIONS.md` and let the client answer". Never both silently.

   Record the ruling in `history/DECISIONS.md` with its `cost-if-wrong` clause, written
   NOW, before the outcome is known — a retrospective cost clause is worthless.

5. **Apply in one direction: `client/` → `generated/` → `macstack.json`.** Client prose
   is edited by hand and never rewritten silently; the generated documents are rebuilt;
   the spec is synced. Never the reverse.

6. **Write every edit to `history/ledger.jsonl`**, keyed by the id of the statement that
   changed, with `was` and `now`. That row is what lets the next review package show the
   client what moved since they last read it. An edit with no row is a defect.

7. **Open the work.** What was decided and needs building becomes a task in
   `history/TASKS.md`, then goes to the tracker with `/macstack-dev:plan sync`.

## Answers coming back from a review package

Those arrive through `/macstack-dev:review --read`, which writes them into the ledger.
Then come here: an answer that asks for a change is ordinary incoming material. Do not
apply a client's comment straight to a document — a comment is a request, and what it
costs to be wrong about it is the owner's call.
