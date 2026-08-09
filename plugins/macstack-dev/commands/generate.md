---
description: Generate macstack.json from scratch — result-first stack design from a business request
argument-hint: "<business request>"
---

Use the macstack-dev:generate-stack skill (delegate design to the macstack-architect
agent for complex requests) to design a stack for: $ARGUMENTS. Then run
macstack-dev:discover-context to fill prototype and context.plugins, and
macstack-dev:lint. Present goals/results first and wait for the user to confirm the
RESULTS before offering /macstack-dev:scaffold.
