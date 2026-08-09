---
description: Validate macstack.json against the JSON Schema and referential-integrity rules
---

Use the macstack-dev:lint skill on the project's macstack.json (resolve prototype
chain first if set). Output ERRORS, then WARNINGS, then the OK line. If errors exist,
propose concrete fixes and apply them on user confirmation.
