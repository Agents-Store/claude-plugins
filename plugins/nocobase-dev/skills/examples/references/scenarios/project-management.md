# Scenario: Project Management Application

Build a project management application with tasks, milestones, assignments, and kanban boards using the NocoBase HTTP API.

## Entity Model

```
projects ──< milestones
    │
    └──< tasks ──< task_comments
         │
    tasks >──< users (via task_assignments)
```

## Step 1: Create Collections

### projects

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections:create" \
  -d '{
    "name": "projects",
    "title": "Projects",
    "createdBy": true,
    "updatedBy": true,
    "fields": [
      {
        "name": "name",
        "type": "string",
        "interface": "input",
        "uiSchema": {"title": "Project Name", "type": "string", "x-component": "Input", "required": true}
      },
      {
        "name": "description",
        "type": "text",
        "interface": "richText",
        "uiSchema": {"title": "Description", "type": "string", "x-component": "RichText"}
      },
      {
        "name": "status",
        "type": "string",
        "interface": "select",
        "uiSchema": {
          "title": "Status", "type": "string", "x-component": "Select",
          "enum": [
            {"value": "planning", "label": "Planning"},
            {"value": "active", "label": "Active"},
            {"value": "on_hold", "label": "On Hold"},
            {"value": "completed", "label": "Completed"},
            {"value": "archived", "label": "Archived"}
          ]
        }
      },
      {
        "name": "priority",
        "type": "string",
        "interface": "select",
        "uiSchema": {
          "title": "Priority", "type": "string", "x-component": "Select",
          "enum": [
            {"value": "low", "label": "Low"},
            {"value": "medium", "label": "Medium"},
            {"value": "high", "label": "High"},
            {"value": "critical", "label": "Critical"}
          ]
        }
      },
      {
        "name": "startDate",
        "type": "date",
        "interface": "datetime",
        "uiSchema": {"title": "Start Date", "x-component": "DatePicker"}
      },
      {
        "name": "endDate",
        "type": "date",
        "interface": "datetime",
        "uiSchema": {"title": "End Date", "x-component": "DatePicker"}
      },
      {
        "name": "budget",
        "type": "decimal",
        "interface": "number",
        "uiSchema": {"title": "Budget", "x-component": "InputNumber", "x-component-props": {"precision": 2}}
      }
    ]
  }'
```

### milestones

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections:create" \
  -d '{
    "name": "milestones",
    "title": "Milestones",
    "fields": [
      {
        "name": "title",
        "type": "string",
        "interface": "input",
        "uiSchema": {"title": "Title", "type": "string", "x-component": "Input", "required": true}
      },
      {
        "name": "dueDate",
        "type": "date",
        "interface": "datetime",
        "uiSchema": {"title": "Due Date", "x-component": "DatePicker"}
      },
      {
        "name": "status",
        "type": "string",
        "interface": "select",
        "uiSchema": {
          "title": "Status", "type": "string", "x-component": "Select",
          "enum": [
            {"value": "pending", "label": "Pending"},
            {"value": "in_progress", "label": "In Progress"},
            {"value": "completed", "label": "Completed"}
          ]
        }
      }
    ]
  }'
```

### tasks (with self-referencing for subtasks)

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections:create" \
  -d '{
    "name": "tasks",
    "title": "Tasks",
    "createdBy": true,
    "updatedBy": true,
    "fields": [
      {
        "name": "title",
        "type": "string",
        "interface": "input",
        "uiSchema": {"title": "Title", "type": "string", "x-component": "Input", "required": true}
      },
      {
        "name": "description",
        "type": "text",
        "interface": "richText",
        "uiSchema": {"title": "Description", "type": "string", "x-component": "RichText"}
      },
      {
        "name": "status",
        "type": "string",
        "interface": "select",
        "uiSchema": {
          "title": "Status", "type": "string", "x-component": "Select",
          "enum": [
            {"value": "todo", "label": "To Do"},
            {"value": "in_progress", "label": "In Progress"},
            {"value": "review", "label": "Review"},
            {"value": "done", "label": "Done"}
          ]
        }
      },
      {
        "name": "priority",
        "type": "string",
        "interface": "select",
        "uiSchema": {
          "title": "Priority", "type": "string", "x-component": "Select",
          "enum": [
            {"value": "low", "label": "Low"},
            {"value": "medium", "label": "Medium"},
            {"value": "high", "label": "High"},
            {"value": "critical", "label": "Critical"}
          ]
        }
      },
      {
        "name": "dueDate",
        "type": "date",
        "interface": "datetime",
        "uiSchema": {"title": "Due Date", "x-component": "DatePicker"}
      },
      {
        "name": "estimatedHours",
        "type": "float",
        "interface": "number",
        "uiSchema": {"title": "Estimated Hours", "x-component": "InputNumber"}
      },
      {
        "name": "actualHours",
        "type": "float",
        "interface": "number",
        "uiSchema": {"title": "Actual Hours", "x-component": "InputNumber"}
      },
      {
        "name": "taskNumber",
        "type": "sequence",
        "interface": "sequence",
        "patterns": [
          {"type": "string", "options": {"value": "TASK-"}},
          {"type": "integer", "options": {"digits": 4, "start": 1, "key": "task_seq"}}
        ]
      }
    ]
  }'
```

### task_comments

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections:create" \
  -d '{
    "name": "task_comments",
    "title": "Task Comments",
    "createdBy": true,
    "fields": [
      {
        "name": "content",
        "type": "text",
        "interface": "richText",
        "uiSchema": {"title": "Comment", "type": "string", "x-component": "RichText", "required": true}
      }
    ]
  }'
```

### task_assignments (through table)

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections:create" \
  -d '{
    "name": "task_assignments",
    "title": "Task Assignments",
    "fields": [
      {
        "name": "role",
        "type": "string",
        "interface": "select",
        "uiSchema": {
          "title": "Role", "type": "string", "x-component": "Select",
          "enum": [
            {"value": "lead", "label": "Lead"},
            {"value": "contributor", "label": "Contributor"},
            {"value": "reviewer", "label": "Reviewer"}
          ]
        }
      },
      {
        "name": "assignedAt",
        "type": "date",
        "interface": "datetime",
        "uiSchema": {"title": "Assigned At", "x-component": "DatePicker"}
      }
    ]
  }'
```

## Step 2: Create Relations

```bash
# projects.owner → users (belongsTo)
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections/projects/fields:create" \
  -d '{
    "name": "owner",
    "type": "belongsTo",
    "interface": "m2o",
    "target": "users",
    "foreignKey": "ownerId",
    "uiSchema": {"title": "Owner", "x-component": "AssociationField", "x-component-props": {"fieldNames": {"label": "nickname", "value": "id"}}}
  }'

# projects.milestones → milestones (hasMany)
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections/projects/fields:create" \
  -d '{
    "name": "milestones",
    "type": "hasMany",
    "interface": "o2m",
    "target": "milestones",
    "foreignKey": "projectId",
    "uiSchema": {"title": "Milestones", "x-component": "AssociationField"}
  }'

# milestones.project → projects (belongsTo)
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections/milestones/fields:create" \
  -d '{
    "name": "project",
    "type": "belongsTo",
    "interface": "m2o",
    "target": "projects",
    "foreignKey": "projectId",
    "uiSchema": {"title": "Project", "x-component": "AssociationField", "x-component-props": {"fieldNames": {"label": "name", "value": "id"}}}
  }'

# tasks.project → projects (belongsTo)
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections/tasks/fields:create" \
  -d '{
    "name": "project",
    "type": "belongsTo",
    "interface": "m2o",
    "target": "projects",
    "foreignKey": "projectId",
    "uiSchema": {"title": "Project", "x-component": "AssociationField", "x-component-props": {"fieldNames": {"label": "name", "value": "id"}}}
  }'

# tasks.milestone → milestones (belongsTo)
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections/tasks/fields:create" \
  -d '{
    "name": "milestone",
    "type": "belongsTo",
    "interface": "m2o",
    "target": "milestones",
    "foreignKey": "milestoneId",
    "uiSchema": {"title": "Milestone", "x-component": "AssociationField", "x-component-props": {"fieldNames": {"label": "title", "value": "id"}}}
  }'

# tasks.parent → tasks (self-reference for subtasks)
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections/tasks/fields:create" \
  -d '{
    "name": "parent",
    "type": "belongsTo",
    "interface": "m2o",
    "target": "tasks",
    "foreignKey": "parentId",
    "uiSchema": {"title": "Parent Task", "x-component": "AssociationField", "x-component-props": {"fieldNames": {"label": "title", "value": "id"}}}
  }'

# tasks.children → tasks (subtasks)
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections/tasks/fields:create" \
  -d '{
    "name": "children",
    "type": "hasMany",
    "interface": "o2m",
    "target": "tasks",
    "foreignKey": "parentId",
    "uiSchema": {"title": "Subtasks", "x-component": "AssociationField"}
  }'

# tasks ↔ users (many-to-many via task_assignments)
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections/tasks/fields:create" \
  -d '{
    "name": "assignees",
    "type": "belongsToMany",
    "interface": "m2m",
    "target": "users",
    "through": "task_assignments",
    "foreignKey": "taskId",
    "otherKey": "userId",
    "uiSchema": {"title": "Assignees", "x-component": "AssociationField", "x-component-props": {"fieldNames": {"label": "nickname", "value": "id"}}}
  }'

# task_comments.task → tasks (belongsTo)
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections/task_comments/fields:create" \
  -d '{
    "name": "task",
    "type": "belongsTo",
    "interface": "m2o",
    "target": "tasks",
    "foreignKey": "taskId",
    "uiSchema": {"title": "Task", "x-component": "AssociationField"}
  }'

# tasks.comments → task_comments (hasMany)
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections/tasks/fields:create" \
  -d '{
    "name": "comments",
    "type": "hasMany",
    "interface": "o2m",
    "target": "task_comments",
    "foreignKey": "taskId",
    "uiSchema": {"title": "Comments", "x-component": "AssociationField"}
  }'

# projects.tasks → tasks (hasMany)
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections/projects/fields:create" \
  -d '{
    "name": "tasks",
    "type": "hasMany",
    "interface": "o2m",
    "target": "tasks",
    "foreignKey": "projectId",
    "uiSchema": {"title": "Tasks", "x-component": "AssociationField"}
  }'
```

## Step 3: Seed Sample Data

```bash
# Create a project
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/projects:create" \
  -d '{
    "name": "Website Redesign",
    "status": "active",
    "priority": "high",
    "startDate": "2025-04-01",
    "endDate": "2025-06-30",
    "budget": 50000
  }'

# Create a milestone (assuming project id=1)
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/milestones:create" \
  -d '{
    "title": "Design Phase Complete",
    "dueDate": "2025-04-30",
    "status": "in_progress",
    "projectId": 1
  }'

# Create tasks
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/tasks:create" \
  -d '{
    "title": "Create wireframes",
    "status": "in_progress",
    "priority": "high",
    "dueDate": "2025-04-15",
    "estimatedHours": 16,
    "projectId": 1,
    "milestoneId": 1
  }'

curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/tasks:create" \
  -d '{
    "title": "Design mockups",
    "status": "todo",
    "priority": "high",
    "dueDate": "2025-04-25",
    "estimatedHours": 24,
    "projectId": 1,
    "milestoneId": 1
  }'
```

## Step 4: Workflows

### Task Overdue Alert (scheduled)

```bash
# Create the workflow
curl -X POST "${NOCOBASE_URL}/api/workflows:create" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "schedule",
    "title": "Task Overdue Alert",
    "enabled": false,
    "config": {
      "mode": 0,
      "cron": "0 9 * * 1-5",
      "limit": 0
    }
  }'

# Add query node: find overdue tasks (workflowId from above)
curl -X POST "${NOCOBASE_URL}/api/workflows/1/nodes:create" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "query",
    "title": "Find Overdue Tasks",
    "config": {
      "collection": "tasks",
      "multiple": true,
      "params": {
        "filter": {
          "$and": [
            {"dueDate": {"$dateBefore": "{{NOW()}}"}},
            {"status": {"$ne": "done"}}
          ]
        },
        "appends": ["assignees", "project"]
      }
    }
  }'

# Add request node: send alert webhook
curl -X POST "${NOCOBASE_URL}/api/workflows/1/nodes:create" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "request",
    "title": "Send Overdue Alert",
    "config": {
      "url": "https://hooks.slack.com/services/xxx",
      "method": "POST",
      "headers": [{"name": "Content-Type", "value": "application/json"}],
      "data": "{\"text\": \"Overdue tasks found: {{$jobsData.node1.length}} tasks need attention\"}"
    }
  }'
```

### All Tasks Done → Complete Milestone

```bash
curl -X POST "${NOCOBASE_URL}/api/workflows:create" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "collection",
    "title": "Auto-Complete Milestone",
    "enabled": false,
    "config": {
      "collection": "tasks",
      "mode": 2,
      "condition": {
        "$and": [{"status": "done"}]
      }
    }
  }'
```

Workflow nodes:
1. **Query** — count tasks in same milestone where status != "done"
2. **Condition** — remaining == 0?
3. **Update** (yes branch) — set milestone.status = "completed"

## Step 5: Query Data

### List all tasks for a project with assignees

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/tasks:list?filter={\"projectId\":1}&appends=[assignees,milestone]&sort=[-priority,dueDate]&page=1&pageSize=50"
```

### Dashboard: tasks by status (chart query)

```bash
curl -X POST "${NOCOBASE_URL}/api/charts:query" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "collection": "tasks",
    "measures": [{"field": "id", "aggregation": "count", "alias": "taskCount"}],
    "dimensions": [{"field": "status", "alias": "status"}]
  }'
```

### Dashboard: tasks created vs completed by week

```bash
curl -X POST "${NOCOBASE_URL}/api/charts:query" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "collection": "tasks",
    "measures": [{"field": "id", "aggregation": "count", "alias": "count"}],
    "dimensions": [
      {"field": "createdAt", "alias": "week", "format": "YYYY-[W]WW"},
      {"field": "status", "alias": "status"}
    ],
    "orders": [{"field": "week", "order": "asc"}]
  }'
```

## UI Design

### Recommended Menu Structure

```
Projects
  ├── Dashboard (Charts: tasks by status, created vs completed, overdue count)
  ├── All Projects (Table block)
  ├── My Tasks (Table block, filtered: assignees includes current user)
  ├── Calendar (Calendar block: tasks by dueDate)
  └── Team (Table block: users with task counts)
```

### Project Detail Page (tabs)

```
Tab 1: Task Board (Kanban, group by status)
  - Cards: title, priority, assignees, dueDate
  - Drag-drop to change status

Tab 2: Task List (Table with tree display for subtasks)
  - Columns: taskNumber, title, status, priority, assignees, dueDate
  - Filters: status, priority, assignee
  - Inline edit: status, priority

Tab 3: Timeline (Gantt chart)
  - Start: startDate or createdAt
  - End: dueDate
  - Group by: milestone

Tab 4: Milestones (Table)
  - Columns: title, dueDate, status, task count
```
