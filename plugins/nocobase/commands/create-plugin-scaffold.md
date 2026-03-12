---
description: Generate NocoBase plugin scaffold structure
allowed-tools: []
argument-hint: <plugin-name> [--type <server|client|full>]
---

# Create Plugin Scaffold

Generate the directory structure and boilerplate for a NocoBase plugin.

## Arguments
Format: `<plugin-name> [--type <server|client|full>]`
- plugin-name: Name of the plugin (required)
- --type: Plugin type — server (backend only), client (frontend only), full (both, default)

Parse from "$ARGUMENTS".

## Process

1. **Generate directory structure:**
   ```
   packages/plugins/@my-project/<plugin-name>/
   ├── package.json
   ├── src/
   │   ├── server/
   │   │   ├── index.ts
   │   │   ├── plugin.ts
   │   │   ├── collections/
   │   │   └── migrations/
   │   └── client/
   │       ├── index.ts
   │       ├── plugin.ts
   │       └── components/
   └── README.md
   ```

2. **Generate boilerplate files:**
   - package.json with NocoBase dependencies
   - Server plugin class with lifecycle hooks
   - Client plugin class with component registration

3. **Provide setup instructions.**

## Example Usage
```
/create-plugin-scaffold "custom-fields"
/create-plugin-scaffold "approval-workflow" --type server
/create-plugin-scaffold "dashboard-widgets" --type client
```
