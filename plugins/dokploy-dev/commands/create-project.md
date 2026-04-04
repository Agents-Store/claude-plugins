---
description: Create a new Dokploy project
argument-hint: <name> [--description <text>]
---

# Create Project

Create a new project on the Dokploy instance.

## Arguments
Format: `<name> [--description <text>]`
- name: Project name (required)
- --description: Project description (optional)

Parse from "$ARGUMENTS".

## Process

1. **Create project** using MCP tool `project-create` with the provided name and description.

2. **Display result:**
   Show project ID, name, and description. Suggest next steps: create an application or database.

## Example Usage
```
/dokploy-dev:create-project "my-saas"
/dokploy-dev:create-project "staging-env" --description "Staging environment for testing"
```
