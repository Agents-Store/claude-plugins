---
description: List all Dokploy projects
argument-hint: ""
---

# List Projects

List all projects on the Dokploy instance.

## Process

1. **Fetch projects** using MCP tool `project-all`.

2. **Display as table:**
   Show project ID, name, description, and number of services (applications, databases, compose).

## Example Usage
```
/dokploy-dev:list-projects
```
