---
description: Scaffold project files from macstack.json (prototype → stack plugins → dev plugins)
---

Use the macstack-dev:scaffold-project skill on the current project's macstack.json.
Follow the mandatory source order: 1) prototype (github or local absolute path),
2) stack plugins (architecture), 3) dev plugins (how to build with each software) —
then generate the files. Always invoke macstack-dev:infisical-env (.infisical.json +
.env.prod/.env.dev + secrets scripts) and macstack-dev:best-practices (rules +
commands). Finish with macstack-dev:lint and report created files by source.
