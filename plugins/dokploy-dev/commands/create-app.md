---
description: Create a new application in a Dokploy project
argument-hint: <name> --project <project> [--build <nixpacks|dockerfile|static>]
---

# Create Application

Create a new application in an existing Dokploy project.

## Arguments
Format: `<name> --project <project> [--build <nixpacks|dockerfile|static>]`
- name: Application name (required)
- --project: Project name or ID (required)
- --build: Build type — nixpacks, dockerfile, heroku, paketo, railpack, or static (default: nixpacks)

Parse from "$ARGUMENTS".

## Process

1. **Resolve project:** If --project is a name, call `project-all` and find matching project.

2. **Create application** using MCP tool `application-create` with:
   - `name`: the app name
   - `appName`: kebab-case version of name (for Docker container naming)
   - `projectId`: resolved project ID

3. **Set build type** using MCP tool `application-saveBuildType` if --build is specified.

4. **Display result:**
   Show application ID, name, project, build type. Suggest next steps: connect git repo, set env vars, add domain, deploy.

## Example Usage
```
/dokploy-dev:create-app "web-frontend" --project my-saas
/dokploy-dev:create-app "api-server" --project my-saas --build dockerfile
/dokploy-dev:create-app "landing-page" --project marketing --build static
```
