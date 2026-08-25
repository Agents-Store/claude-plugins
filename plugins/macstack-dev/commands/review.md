---
description: Build the client review package from the client documents — a self-contained HTML file, a published artifact with comment threads, or both — and read the client's comments back
argument-hint: [--html | --artifact | --read <url> | (empty = both)]
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep, Skill, Artifact]
---

Use `macstack-dev:client-package`.

The inbound half of the client loop has always worked. The outbound half is this:
nobody sends a client an 88 KB markdown file and expects edits back, so in practice the
client writes a fresh document of their own and somebody transcribes it by hand — which
is where a hundred small changes go missing.

**Building.** The package carries the five client documents — `OVERVIEW.md`,
`USER-CASES.md`, `UX-UI.md`, `AUTOMATION.md`, `HANDBOOK.md` — and never
`OPEN-QUESTIONS.md`, `history/` or anything under `generated/`. A package the client
does not finish reading produces fewer corrections, not more.

Every acceptance bullet, screen prohibition and trigger gets a place to answer:
confirm, correct, or ask. The address printed beside each one is its **stable id**
(`C-04.a3`), not its position in this package — a comment must survive the next
rebuild.

`--html` writes `history/handoffs/<date>-<slug>.html`, self-contained, editable in the
browser and printable to PDF. `--artifact` publishes the same content and the client
comments in threads. Both write a `handoff` entry naming the document, the version, the
file and the recipient — and the artifact one also records its URL and version label.
`handoffs/` is immutable for the same reason `inbox/` is: their edits come back against
THAT file, and a package edited after the fact makes every returned comment
unresolvable. A new round writes a new dated file.

**Reading back.** `--read` pulls the comment threads from a published artifact and
turns them into ordinary incoming material for `/macstack-dev:inbox`. A returned HTML
file lands in `inbox/` the same way. One path, both channels.
