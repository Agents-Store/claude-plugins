---
name: project-setup
description: Project initialization, organization and project management. Use when setting up Trigger.dev in a new or existing project.
---

# Project Setup

This skill covers initializing Trigger.dev in your project and managing organizations and projects.

## Available Tools

| Tool | Description |
|------|-------------|
| `tds-search_docs` | Search Trigger.dev documentation |
| `tds-list_orgs` | List your organizations |
| `tds-list_projects` | List your projects |
| `tds-create_project_in_org` | Create a new project in an org |
| `tds-initialize_project` | Initialize Trigger.dev in your project directory |

## Initialization Flow

### Step 1: List Organizations
```
Tool: tds-list_orgs
Input: {}

Returns list of orgs with slug and ID.
Pick the org you want to create the project in.
```

### Step 2: Create Project (if needed)
```
Tool: tds-create_project_in_org
Input: {
  "orgParam": "my-org-slug",
  "name": "My Background Jobs"
}

Returns project with projectRef (proj_xxx).
Only create if no trigger.config.ts exists yet.
```

### Step 3: Initialize in Directory
```
Tool: tds-initialize_project
Input: {
  "orgParam": "my-org-slug",
  "projectName": "My Background Jobs",
  "cwd": "/path/to/your/project"
}

This creates:
- trigger.config.ts
- src/trigger/ directory with example task
- Installs @trigger.dev/sdk
```

### Step 4: List Projects (verify)
```
Tool: tds-list_projects
Input: {}

Verify your project appears in the list.
```

## Project Structure After Init

```
your-project/
  trigger.config.ts        # Main config file
  src/
    trigger/
      example.ts           # Example task
  package.json             # Updated with @trigger.dev/sdk
```

## trigger.config.ts Basics

The config file defines your project settings. Search docs for details:

```
Tool: tds-search_docs
Input: {"query": "trigger.config.ts configuration"}
```

Key configuration options:
- `project` - Your project ref (proj_xxx)
- `runtime` - "node" (default) or "bun"
- `dirs` - Directories containing task files (default: ["src/trigger"])
- `retries` - Default retry configuration
- `machine` - Default machine preset
- `build` - Build extensions configuration

## Environment Setup

Trigger.dev has 4 environments:
- **dev** - Local development (runs tasks in your dev server)
- **staging** - Testing before production
- **prod** - Production environment
- **preview** - Branch-based preview environments

For local development, run `npx trigger.dev@latest dev` to start the dev server.

## Common Issues

| Issue | Solution |
|-------|----------|
| No orgs found | Verify API key / auth with Trigger.dev |
| Project already exists | Use existing projectRef from trigger.config.ts |
| Init fails | Ensure cwd is correct and has package.json |
| Can't find config | Pass configPath parameter explicitly |

## Best Practices

1. **One project per service** - Each microservice gets its own Trigger.dev project
2. **Use meaningful names** - Project names should reflect their purpose
3. **Set up environments early** - Configure staging before going to prod
4. **Check docs for latest** - Use tds-search_docs for current best practices
