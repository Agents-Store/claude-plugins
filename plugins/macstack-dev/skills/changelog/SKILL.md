---
name: changelog
description: This skill should be used when the user wants to "write a changelog", "log what I did", "record today's work", "what shipped", "что сделали", "лог разработки", "записать в журнал", "release notes", "what changed for the client", "закрыть веху", "что нового в релизе", "cut a release", write a `work` or `release` entry to `macstack/log.md`, or curate `log.md` into `macstack/CHANGELOG.md`. Never used for `intake` or `merge` entries — those stay owned by `docs-merge`.
---

# Changelog — the Development Log and Its Client-Facing Derivative

`log.md` is the raw development record; `CHANGELOG.md` is its curated, client-facing
derivative — the same raw → curated relationship this folder already runs for
`inbox/` → the documents intake produces. Nobody reads `log.md` to find out what
shipped; nobody reads `CHANGELOG.md` to find out why a decision was made. Confusing
the two either produces a changelog no client can parse, or a client document that
quietly loses the reasoning git cannot hold.

Open `${CLAUDE_PLUGIN_ROOT}/skills/project-docs/references/doc-contracts.json` for
the `log`/`changelog` document contracts (anchors, entry grammar, id spaces) —
authoritative, not repeated here.

## Where the two documents sit

| | `log.md` | `CHANGELOG.md` |
|---|---|---|
| Register | engineering, for the team | plain language, for the client and the PM |
| Written | the day the work happened | only when something reached the people who use it |
| Content | every `work`/`release` entry worth a record | curated from `log.md`, never written independently |
| Order | append-only, oldest first | **newest first** |
| Audience | internal | client |

## The four kinds of `log.md` entry

Heading: `## [YYYY-MM-DD] <intake|merge|work|release> | <title>`.

| Kind | Owner | Requires | When |
|---|---|---|---|
| `intake` | `docs-merge` | `source` | client material lands in `inbox/` |
| `merge` | `docs-merge` | `source, delta, decisions, applied, opened, closed` | a delta was ruled on and applied |
| `work` | **this skill** | `tasks, what, notes` | development happened, worth a record |
| `release` | **this skill** | `release, milestone, changelog` | something reached the people who use it |

*`intake`/`merge` are not redefined here — they belong to `docs-merge`.*

## Writing a `work` entry

Write one whenever a session advances a task AND there is something worth saying
past "see the diff" — `git log` already covers what changed and when, per commit.
`tasks` names the `TASKS.md` ids advanced. `what` states what now exists that did
not before — a property, not a diff. `notes` is the half git cannot hold: the dead
end taken, what turned out harder than expected, a decision deferred. **An entry
with empty `notes` is usually not worth writing.**

```
## [2026-08-24] work | M11 — split the export run in two
- tasks: T-42, T-43
- what: export now runs as two independent jobs (metadata, then rows) instead of one
- notes: tried keeping it one job with an internal checkpoint first — rows outnumber
  metadata 400:1, so a mid-job crash always looked like a metadata failure and
  retried the wrong half. Splitting was the simpler fix, not the elegant one.
  *(Superseded by M11 in every name, not in shape — see the M11 entry.)*
```

Cite git by commit range or subject tag (`a1b2c3..d4e5f6`, `"fix(export): ..."`),
never by line number — a line pointer rots the moment the file above it grows.

## Writing a `release` entry

**A release is not a merge.** Merging to main is an engineering event; a release is
a client-visible one. Do not write a `release` entry for a merge nobody outside the
team can see yet.

```
## [2026-08-24] release | M11 — split export ships
- release: R-2026-08-24
- milestone: M11
- changelog: CHANGELOG.md#r-2026-08-24
```

Pairs 1:1 with a `CHANGELOG.md` entry of the same `R-` id — write both in the same
pass; a `release` entry with no matching changelog item is a broken pointer.

## The curation pass — `log.md` → `CHANGELOG.md`

`CHANGELOG.md` is derived, never written independently:

1. Read every `work`/`release` entry since the last `R-` id in `CHANGELOG.md`.
2. Group by milestone.
3. Translate each into what a user can now do that they could not before — not an
   engineering property, not a restated diff.
4. **Drop everything with no user-visible effect.** Most `work` entries never
   become a changelog entry; a changelog that mirrors `log.md` is a git log with
   extra steps. Never invent a claim `log.md` does not support.
5. Exception: if a `work` entry's `notes` says something turned out not to work and
   the client saw it, that is exactly the thing a changelog must not quietly omit.

**GATE** — show the drafted entries before writing `CHANGELOG.md`.

```
<!-- macstack:release=R-2026-08-24 -->
## R-2026-08-24 · M11 — exports no longer stall on large accounts
Large-account exports used to time out partway through. They now run in two
smaller steps and finish reliably, even on the biggest accounts.
```

New entries prepend under the `<!-- macstack:section=releases -->` anchor — newest
first, the opposite of `log.md`'s append order.

## Supersession — never delete

An outdated `CHANGELOG.md` or `log.md` entry stays and gains an appended
correction; it is never rewritten or removed:

```
*(M11 split this one run into two: see the M11 entry at the end.)*
```

A changelog that edits its own past cannot be trusted about its present. Thread a
continuation of a previous entry the same way — append, point forward, never fold
the new text back into the earlier entry.

## Not a git log

`git log` already answers what changed and when, per commit. What it cannot answer
is why this way and what was tried first (`log.md`'s `notes`), and what the client
can now do that they could not before (`CHANGELOG.md`). A drafted entry that
restates a diff instead of one of those two gets cut.

## Routing

| Situation | Do |
|---|---|
| No `macstack/` yet | `macstack-dev:project-docs` first |
| Client material / a delta was ruled on | `docs-merge` owns `intake`/`merge` — not this skill |
| Development happened, worth recording | write a `work` entry here |
| Something reached the client | write a `release` entry + matching `CHANGELOG.md` item |
| Ready to publish accumulated work | run the curation pass |
| After any write | `macstack-dev:lint` |
