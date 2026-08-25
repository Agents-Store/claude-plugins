---
description: Validate the spec and the documents, report where the project stands and what to run next, or audit the implementation against the documents
argument-hint: [--docs | --code | (empty = spec + documents + dashboard)]
allowed-tools: [Read, Bash, Glob, Grep, Skill]
---

Read-only in every mode. Nothing here writes to the spec or to a client document.

**Empty** — `macstack-dev:lint`, all three passes, then the status screen. One engine,
two ways of printing it: the dashboard is the lint findings ordered by cost of ignoring
them, not a second set of predicates with its own opinion.

**`--docs`** — pass 3 and the judgment checks only. Use it after editing documents and
before handing anything to a client.

**`--code`** — `macstack-dev:conformance`. The only mode that reads the source tree.
It answers, per case id, whether the implementation actually does what the documents
promise, and writes a dated pair into `history/reviews/`: the technical audit and its
business-language twin. Its verdicts are what `/macstack-dev:plan` reads to tell real
work from a document nobody has checked.

Report errors before warnings, and end with the single next command. If the spec fails
lint, say plainly that it must not be scaffolded from.
