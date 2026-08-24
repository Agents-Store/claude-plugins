---
description: Turn uncovered user cases into task entries with files, acceptance and a pointer to the requirement
---

Use the `macstack-dev:plan-changes` skill on the project at $ARGUMENTS (default: current
directory). Run the analyser, report the four states, then for every case in "ни того ни
другого" read the codebase and fill `files` and `acceptance` — never guess them, leave the
field empty and say so if the code does not answer. Append the finished entries to
`macstack/history/TASKS.md` under the newest milestone with a journal row, and stop before
writing any code: the point is the handoff to a planning session.
