---
description: Build the client review package from USER-CASES.md + BUSINESS-LOGIC.md
---

Use the `macstack-dev:client-package` skill on the project at $ARGUMENTS (default: current
directory). Build the package, report how many cases and acceptance items it carries and which
document version it froze, then append the printed `handoff` entry to `macstack/log.md` — rule
12.20 requires it and it is the only record of which version the client reviewed. Remind the
user that `handoffs/` is immutable: a new round writes a new dated file, it never overwrites.
