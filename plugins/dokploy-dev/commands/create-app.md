---
description: Create a new application in a Dokploy project
argument-hint: <name> --project <project> [--env <environment>] [--build <nixpacks|dockerfile|static>]
allowed-tools: [Read, Bash, Skill, Agent]
---

# Create Application

Create a new application in an existing Dokploy project.

## Arguments
Format: `<name> --project <project> [--env <environment-name>] [--build <nixpacks|dockerfile|static>]`
- name: Application name (required)
- --project: Project name or ID (required)
- --env: Environment name within the project (optional, default: `production`)
- --build: Build type — nixpacks, dockerfile, heroku, paketo, railpack, or static (default: nixpacks)

Parse from "$ARGUMENTS".

## Process

1. **Resolve project:** If --project is a name, call `project-all` and find matching project.

2. **Resolve the target environment:** `project-one { projectId }` → `environments[]` (default `production`); or `environment-byProjectId { projectId }`. If `--env` is given, match by name; if several environments exist and none is specified, ask the user.

3. **Create application** using MCP tool `application-create` with:
   - `name`: the app name
   - `appName`: kebab-case version of name (for Docker container naming)
   - `environmentId`: resolved environment ID (NOT projectId)

4. **Set build type** using MCP tool `application-saveBuildType` if --build is specified.

5. **Display result:**
   Show application ID, name, project, environment, build type. Suggest next steps: connect git repo, set env vars, add domain, deploy.

## Example Usage
```
/dokploy-dev:create-app "web-frontend" --project my-saas
/dokploy-dev:create-app "api-server" --project my-saas --build dockerfile
/dokploy-dev:create-app "landing-page" --project marketing --build static
```
