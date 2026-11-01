---
description: List all automation flows in Directus
argument-hint:
---

# List Flows

Follow the `flow-automation` skill (`${CLAUDE_PLUGIN_ROOT}/skills/flow-automation/SKILL.md`) for how flows, triggers and operations work; read it before the first call.

## Process

1. Call `flows` tool with:
   ```json
   {
     "action": "read",
     "query": {
       "fields": ["id", "name", "status", "trigger", "description", "icon", "color"],
       "sort": ["name"]
     }
   }
   ```
2. Display flows as a table: name, status (active/inactive), trigger type, description
3. Show total count
4. Highlight active vs inactive flows

## Output

```
| Name | Status | Trigger | Description |
|------|--------|---------|-------------|
| Welcome Email | active | event | Send email on user create |
| Daily Report | active | schedule | Generate daily metrics |
| Cleanup | inactive | schedule | Remove old drafts |
```
