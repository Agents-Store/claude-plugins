---
description: List all available store addons and their status
allowed-tools: ["mcp__teleshop__list_workflows"]
argument-hint:
---

# List Addons

List all available addons for the Teleshop store with their current status.

## Process

1. **List all addons:**
   ```
   list_workflows()
   ```

2. **Display as table:**
   Show ID, name, description, enabled/disabled status, last execution time.

## Example Usage
```
/list-addons
```
