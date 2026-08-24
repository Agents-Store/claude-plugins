---
description: Derive TEST-CASES.md from the acceptance bullets of USER-CASES.md, or re-derive it after a version bump
argument-hint: "[case id, role letter, or empty for all]"
---

Use the macstack-dev:project-docs skill to resolve the folder, then
macstack-dev:test-cases to derive `macstack/TEST-CASES.md` from the acceptance bullets
of `USER-CASES.md` — at least one test per bullet, each tagged `auto` (naming the test
title that proves it) or `manual` (with preconditions and steps). Scope to $ARGUMENTS
when given, otherwise cover every case. Update by id: never regenerate over
hand-refined steps, strike tests whose bullet is gone rather than deleting them, and
refresh the coverage table. A bullet that cannot be verified as written is a gap in
USER-CASES — route it to macstack-dev:docs-merge or OPEN-QUESTIONS.md §A instead of
inventing the criterion. Finish with macstack-dev:lint and report tests added, struck
and still missing.
