---
description: One-time migration of an existing docs/ folder into the standard macstack/ layout
argument-hint: "[project path]"
---

Use the macstack-dev:docs-migrate skill on the project at $ARGUMENTS (default: current
directory). This is a one-time, destructive relocation of specification-side material
out of `docs/` into `macstack/` — it proposes a move map first and moves files only
after the user confirms; refuses on a dirty working tree or the default branch;
`git mv` only, never cp+rm or a blind sed; and reports any external references it
could not rewrite. Finish with macstack-dev:lint and report what moved, what stayed,
and which IDs still need a human decision.
