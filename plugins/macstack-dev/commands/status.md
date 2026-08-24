---
description: Read-only dashboard — where the project stands and what to do next
argument-hint: "[milestone id]"
---

Use the macstack-dev:status skill on the current project's macstack/ folder (or the
legacy root macstack.json). This command writes nothing — it only reads macstack.json
and the macstack/ documents, computes the attention list from predicates over what
already exists, and renders one screen: header, milestone tree (collapse completed
milestones), coverage row, ⚠ Attention, and ends with the exact next command to run.
Scope the milestone tree to $ARGUMENTS when a milestone id is given, otherwise show
the whole tree. If `macstack/` documents don't exist yet, say so and end with
`/macstack-dev:docs` instead.
