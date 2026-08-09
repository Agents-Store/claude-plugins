---
description: Update macstack.json and derived files after stack changes (spec = definition of done)
---

Compare the current project state against macstack.json: new/removed software,
workflows, triggers, entities, interfaces, env keys. Update macstack.json to match
reality, regenerate derived artifacts (.env.example from resources.accesses,
CLAUDE.md Tech Stack section, enabledPlugins), run macstack-dev:lint, and remind the
user to commit the spec together with the code change (macstack-sync rule).
