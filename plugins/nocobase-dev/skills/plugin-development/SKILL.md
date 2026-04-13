---
name: plugin-development
description: |
  NocoBase plugin scaffolding, lifecycle, server/client APIs, migrations, custom actions, and ACL. Use when:
  - "create a NocoBase plugin"
  - "scaffold plugin structure"
  - "custom action endpoint"
  - "NocoBase plugin lifecycle"
  - "write a migration"
  - "extend NocoBase with code"
  - "register a custom resource"
  - "plugin server-side API"
  - "plugin client-side component"
---

# Plugin Development

Develop custom NocoBase plugins — scaffold structure, lifecycle hooks, server-side actions, client-side components, migrations, and ACL configuration.

## Plugin Structure

```
packages/plugins/@my-project/plugin-name/
├── package.json
├── src/
│   ├── index.ts              # Re-exports
│   ├── server/
│   │   ├── index.ts          # Server entry point
│   │   ├─�� plugin.ts         # Server plugin class
│   │   ���── collections/      # Collection definitions
│   │   │   └── my_table.ts
│   │   ├── actions/          # Custom API actions
│   │   │   └── myAction.ts
│   │   ├── resources/        # REST resources
│   │   ├── migrations/       # Database migrations
│   │   │   └── 20240101-init.ts
│   │   └── middleware/       # Custom middleware
│   └── client/
│       ├── index.ts          # Client entry point
│       ├── plugin.ts         # Client plugin class
│       ├── components/       # React components
│       ├── initializers/     # Schema initializers
��       └── settings/         # Schema settings
└── README.md
```

## Plugin Lifecycle

```
load → install → enable → (running) → disable → remove

load:    Register collections, actions, middleware
install: Run migrations, seed data
enable:  Activate the plugin
disable: Deactivate (data preserved)
remove:  Uninstall (optional: clean data)
```

## Server Plugin Class

```typescript
import { Plugin } from '@nocobase/server';

export class MyPlugin extends Plugin {
  async afterAdd() {
    // Called after plugin is added to app
  }

  async beforeLoad() {
    // Called before load — register event listeners
  }

  async load() {
    // Main initialization
    // Register collections, actions, middleware, resources

    // Register collection
    this.db.collection({
      name: 'my_records',
      fields: [
        { type: 'string', name: 'title' },
        { type: 'text', name: 'content' },
        { type: 'boolean', name: 'published', defaultValue: false },
      ],
    });

    // Register custom action
    this.app.resource({
      name: 'my_records',
      actions: {
        async publish(ctx, next) {
          const { filterByTk } = ctx.action.params;
          await ctx.db.getRepository('my_records').update({
            filterByTk,
            values: { published: true, publishedAt: new Date() },
          });
          ctx.body = { success: true };
          await next();
        },
      },
    });

    // Set ACL permissions
    this.app.acl.allow('my_records', 'list', 'loggedIn');
    this.app.acl.allow('my_records', 'publish', 'admin');
  }

  async install() {
    // Run on first install — seed data, initial config
  }

  async afterEnable() {
    // Plugin is now active
  }

  async afterDisable() {
    // Plugin is now inactive
  }

  async remove() {
    // Cleanup on uninstall
  }
}
```

## Client Plugin Class

```typescript
import { Plugin } from '@nocobase/client';
import { MyComponent } from './components/MyComponent';

export class MyPlugin extends Plugin {
  async load() {
    // Register components
    this.app.addComponents({
      MyComponent,
    });

    // Add plugin settings page
    this.app.pluginSettingsManager.add('my-plugin', {
      title: 'My Plugin Settings',
      icon: 'SettingOutlined',
      Component: MyPluginSettings,
    });

    // Register schema initializer (adds block type to "Add block" menu)
    this.app.schemaInitializerManager.addItem(
      'BlockInitializers',
      'otherBlocks.myBlock',
      {
        title: 'My Custom Block',
        Component: MyBlockInitializer,
      }
    );
  }
}
```

## Collection Definition File

```typescript
// src/server/collections/tasks.ts
import { CollectionOptions } from '@nocobase/database';

export default {
  name: 'tasks',
  title: 'Tasks',
  fields: [
    {
      type: 'string',
      name: 'title',
      required: true,
    },
    {
      type: 'text',
      name: 'description',
    },
    {
      type: 'string',
      name: 'status',
      interface: 'select',
      uiSchema: {
        enum: [
          { value: 'todo', label: 'To Do' },
          { value: 'in_progress', label: 'In Progress' },
          { value: 'done', label: 'Done' },
        ],
      },
      defaultValue: 'todo',
    },
    {
      type: 'date',
      name: 'dueDate',
    },
    {
      type: 'belongsTo',
      name: 'assignee',
      target: 'users',
    },
  ],
} as CollectionOptions;
```

## Migrations

```typescript
// src/server/migrations/20240101-add-priority-field.ts
import { Migration } from '@nocobase/server';

export default class AddPriorityField extends Migration {
  async up() {
    const collection = this.db.getCollection('tasks');
    if (!collection.hasField('priority')) {
      collection.addField('priority', {
        type: 'string',
        interface: 'select',
        uiSchema: {
          enum: [
            { value: 'low', label: 'Low' },
            { value: 'medium', label: 'Medium' },
            { value: 'high', label: 'High' },
          ],
        },
        defaultValue: 'medium',
      });
      await this.db.sync();
    }
  }

  async down() {
    const collection = this.db.getCollection('tasks');
    collection.removeField('priority');
    await this.db.sync();
  }
}
```

## Custom Actions

```typescript
// src/server/actions/batchAssign.ts
export async function batchAssign(ctx, next) {
  const { filter, values } = ctx.action.params;
  const { assigneeId } = values;

  const repo = ctx.db.getRepository('tasks');
  const updated = await repo.update({
    filter,
    values: { assigneeId },
  });

  ctx.body = {
    updated: updated.length,
    message: `${updated.length} tasks assigned`,
  };

  await next();
}
```

Custom actions are accessible via the standard Resource:Action pattern:

```bash
curl -X POST "${NOCOBASE_URL}/api/my_records:publish?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

## Plugin Management via API

### List Installed Plugins

```bash
curl -X GET "${NOCOBASE_URL}/api/app:getPlugins" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### Enable a Plugin

```bash
curl -X POST "${NOCOBASE_URL}/api/pm:enable" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"filterByTk": "my-plugin"}'
```

### Disable a Plugin

```bash
curl -X POST "${NOCOBASE_URL}/api/pm:disable" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"filterByTk": "my-plugin"}'
```

### Add a Plugin

```bash
curl -X POST "${NOCOBASE_URL}/api/pm:add" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"filterByTk": "my-plugin"}'
```

### Remove a Plugin

```bash
curl -X POST "${NOCOBASE_URL}/api/pm:remove" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"filterByTk": "my-plugin"}'
```

## package.json Template

```json
{
  "name": "@my-project/plugin-name",
  "version": "0.1.0",
  "main": "dist/server/index.js",
  "client": "dist/client/index.js",
  "devDependencies": {
    "@nocobase/server": "workspace:*",
    "@nocobase/client": "workspace:*",
    "@nocobase/database": "workspace:*",
    "@nocobase/test": "workspace:*"
  }
}
```

## ACL (Access Control)

Configure permissions in the plugin's `load()` method:

```typescript
// Allow any logged-in user to list
this.app.acl.allow('my_records', 'list', 'loggedIn');

// Allow only admin to create/update/destroy
this.app.acl.allow('my_records', 'create', 'admin');
this.app.acl.allow('my_records', 'update', 'admin');
this.app.acl.allow('my_records', 'destroy', 'admin');

// Public access (no auth required)
this.app.acl.allow('my_records', 'list', 'public');
```

ACL strategies: `public` (no auth), `loggedIn` (any authenticated user), or a role name string (`admin`, `member`, etc.).

## Best Practices

1. **One responsibility per plugin** -- keep plugins focused and composable
2. **Use migrations** -- never modify schema directly, always use versioned migrations
3. **Follow naming conventions** -- snake_case for collections, camelCase for fields
4. **Set ACL permissions** -- always configure access control for new resources
5. **Handle errors** -- add try/catch in custom actions with meaningful error messages
6. **Test with @nocobase/test** -- use the built-in testing utilities
7. **Support disable/remove** -- clean up properly when plugin is deactivated
8. **Version your migrations** -- use date-based naming (`20240101-description.ts`) for ordering
9. **Use Repository API** -- leverage `ctx.db.getRepository()` instead of raw SQL
10. **Document your plugin** -- README with setup instructions and configuration
