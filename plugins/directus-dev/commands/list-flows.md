---
description: List all automation flows in Directus
allowed-tools: ["mcp__directus__flows"]
argument-hint:
---

# List Flows

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
