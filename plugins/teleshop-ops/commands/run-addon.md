---
description: Manually execute a store addon workflow
allowed-tools: ["mcp__teleshop__list_workflows", "mcp__teleshop__get_workflow_variables", "mcp__teleshop__execute_workflow"]
argument-hint: <addon-id> [--variables <json>]
---

# Run Addon

Manually trigger execution of a store addon.

## Arguments
Format: `<addon-id> [--variables <json>]`
- addon-id: The addon/workflow ID (required)
- --variables: JSON object with variables to set before execution (optional)

Parse from "$ARGUMENTS".

## Process

1. **If no addon-id provided, list available addons:**
   ```
   list_workflows()
   ```
   Show addons for user to choose.

2. **If --variables provided, check current variables:**
   ```
   get_workflow_variables(id=<addon-id>)
   ```
   Show current configuration.

3. **Execute the addon:**
   ```
   execute_workflow(id=<addon-id>)
   ```

4. **Report execution:**
   Confirm the addon was triggered and show result.

## Example Usage
```
/run-addon addon-123
/run-addon addon-456 --variables {"sync_url": "https://example.com/feed.xml"}
```

## Notes
- Addon must be enabled (toggled on) to execute
- Use /list-addons to see available addon IDs
