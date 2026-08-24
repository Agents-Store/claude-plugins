---
description: Record a work/release entry in log.md, or curate log.md into CHANGELOG.md
argument-hint: "[log <what was done> | release <milestone> | draft]"
---

Use the macstack-dev:project-docs skill to resolve the macstack/ folder, then
macstack-dev:changelog on $ARGUMENTS: `log <what was done>` writes a `work` entry to
log.md (tasks, what, notes — skip if notes would be empty); `release <milestone>`
writes a paired `release` entry plus its CHANGELOG.md item for something that
reached the client; `draft` (or no argument) runs the curation pass over log.md
entries since the last release and shows the drafted CHANGELOG.md entries for
approval before writing. Finish with macstack-dev:lint. Report: the log.md entry
written, the CHANGELOG.md entries drafted, and what was deliberately left out of
the changelog and why.
