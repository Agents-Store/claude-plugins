---
description: Merge client feedback or a new client document into macstack/ via the intake → delta → gate → ruling → apply loop
argument-hint: "[file in inbox/ | what to improve]"
---

Use the macstack-dev:project-docs skill to confirm the macstack/ folder exists and is
current, then the macstack-dev:docs-merge skill to run the merge loop on $ARGUMENTS —
a file already in inbox/ (or a path in this repo to cite), or, with no file, the
user's text taken straight to the delta step as chat-sourced material. Finish with
macstack-dev:lint. Report: the delta path, the rulings path, which documents changed
and their version bumps, the A-IDs opened and closed, and the log.md entry.
