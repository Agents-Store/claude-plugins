---
description: Create or repair the macstack/ project-docs folder (USER-CASES, BUSINESS-LOGIC, OPEN-QUESTIONS, DECISIONS, log, inbox, deltas, decisions, reviews)
argument-hint: "[project path]"
---

Use the macstack-dev:project-docs skill on $ARGUMENTS or the current project to create
or repair the macstack/ folder standard: macstack.json, README.md, USER-CASES.md,
BUSINESS-LOGIC.md, OPEN-QUESTIONS.md, DECISIONS.md, log.md, inbox/, deltas/,
decisions/, reviews/. Creates only what is missing — NEVER overwrites an existing
document. Finish with macstack-dev:lint and report what was added, file by file.
