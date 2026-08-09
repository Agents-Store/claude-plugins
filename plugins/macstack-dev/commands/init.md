---
description: Create macstack.json in an existing project (audit codebase → validated spec)
argument-hint: "[path]"
---

Use the macstack-dev:setup skill to verify tooling, then the macstack-dev:init-project
skill to audit the existing project ($ARGUMENTS or current directory) and produce a
validated macstack.json. Finish with macstack-dev:lint and add the CLAUDE.md
"Stack Specification" section. Report: what was derived from code, what came from the
user, and the remaining open questions.
