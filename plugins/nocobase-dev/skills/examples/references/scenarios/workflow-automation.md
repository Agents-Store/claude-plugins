# Automating Business Processes with Workflows

End-to-end walkthrough for creating a workflow that automatically generates follow-up tasks when high-value deals are created. This scenario covers the complete lifecycle: creating a workflow, adding nodes, enabling, testing, and monitoring.

## Prerequisites

- A running NocoBase V2 instance with API access and the workflow plugin enabled
- The **setup** skill verification steps completed successfully
- The "deals" collection from the CRM scenario (or any collection with a numeric `value` field)
- A "tasks" collection to receive generated tasks (created in this walkthrough)

## Step 1 -- Create the Tasks Collection

First, create a collection to store the auto-generated tasks.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections:create" \
  -d '{
    "name": "tasks",
    "title": "Tasks",
    "fields": [
      {
        "name": "title",
        "type": "string",
        "interface": "input",
        "uiSchema": {
          "title": "Task Title",
          "type": "string",
          "x-component": "Input",
          "required": true
        }
      },
      {
        "name": "description",
        "type": "text",
        "interface": "textarea",
        "uiSchema": {
          "title": "Description",
          "type": "string",
          "x-component": "Input.TextArea"
        }
      },
      {
        "name": "priority",
        "type": "string",
        "interface": "select",
        "uiSchema": {
          "title": "Priority",
          "type": "string",
          "x-component": "Select",
          "enum": [
            { "value": "low", "label": "Low" },
            { "value": "medium", "label": "Medium" },
            { "value": "high", "label": "High" },
            { "value": "urgent", "label": "Urgent" }
          ],
          "default": "medium"
        }
      },
      {
        "name": "status",
        "type": "string",
        "interface": "select",
        "uiSchema": {
          "title": "Status",
          "type": "string",
          "x-component": "Select",
          "enum": [
            { "value": "open", "label": "Open" },
            { "value": "in_progress", "label": "In Progress" },
            { "value": "completed", "label": "Completed" }
          ],
          "default": "open"
        }
      },
      {
        "name": "dealTitle",
        "type": "string",
        "interface": "input",
        "uiSchema": {
          "title": "Related Deal",
          "type": "string",
          "x-component": "Input"
        }
      },
      {
        "name": "dealValue",
        "type": "decimal",
        "interface": "number",
        "uiSchema": {
          "title": "Deal Value",
          "type": "number",
          "x-component": "InputNumber",
          "x-component-props": { "precision": 2 }
        }
      }
    ]
  }'
```

## Step 2 -- Create the Workflow

Create a workflow triggered when a new deal record is created. Start with `enabled: false` so you can configure nodes before activation.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/workflows:create" \
  -d '{
    "type": "collection",
    "title": "High-Value Deal Task Creator",
    "description": "Automatically create a follow-up task when a deal with value > 10000 is created",
    "enabled": false,
    "config": {
      "collection": "deals",
      "mode": 1,
      "condition": {
        "$and": []
      }
    }
  }'
```

Note the returned workflow `id` (e.g., `1`). You will use it in subsequent steps to add nodes.

**Key fields explained:**

- `type: "collection"` -- triggers on collection data events
- `config.collection: "deals"` -- monitors the deals collection
- `config.mode: 1` -- fires only on record creation (not update or delete)
- `config.condition` -- empty `$and` means no additional filtering at the trigger level (we filter in a condition node instead)

## Step 3 -- Add a Condition Node

Add a condition node that checks if the deal value exceeds 10,000. Only high-value deals proceed to task creation.

Replace `1` in the URL with your workflow ID from Step 2.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/workflows/1/nodes:create" \
  -d '{
    "type": "condition",
    "title": "Check Deal Value > 10000",
    "config": {
      "rejectOnFalse": true,
      "engine": "math.js",
      "calculation": "{{$context.data.value}} > 10000"
    }
  }'
```

**Key fields explained:**

- `rejectOnFalse: true` -- the workflow stops if the condition is false (deals <= 10000 are ignored)
- `engine: "math.js"` -- uses the math.js expression engine
- `calculation` -- compares the trigger record's `value` field against 10000
- `{{$context.data.value}}` -- references the `value` field from the deal record that triggered the workflow

## Step 4 -- Add a Create Node

Add a node that creates a new task record when the condition passes.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/workflows/1/nodes:create" \
  -d '{
    "type": "create",
    "title": "Create Follow-Up Task",
    "config": {
      "collection": "tasks",
      "params": {
        "values": {
          "title": "Follow up on high-value deal: {{$context.data.title}}",
          "description": "A new deal worth ${{$context.data.value}} has been created. Schedule a meeting with the contact to discuss next steps and timeline.",
          "priority": "high",
          "status": "open",
          "dealTitle": "{{$context.data.title}}",
          "dealValue": "{{$context.data.value}}"
        }
      }
    }
  }'
```

**Key fields explained:**

- `type: "create"` -- this node creates a new record
- `config.collection: "tasks"` -- creates the record in the tasks collection
- `params.values` -- field values for the new task record, using workflow variable placeholders
- `{{$context.data.title}}` and `{{$context.data.value}}` -- reference fields from the triggering deal record

## Step 5 -- Enable the Workflow

Now that all nodes are configured, enable the workflow to start processing.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/workflows:update?filterByTk=1" \
  -d '{
    "enabled": true
  }'
```

**Verify the workflow is active:**

```bash
curl -s -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/workflows:get?filterByTk=1"
```

Confirm `"enabled": true` in the response.

## Step 6 -- Test by Creating Deal Records

### Test 1: High-Value Deal (Should Trigger Task)

Create a deal with value > 10000.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/deals:create" \
  -d '{
    "title": "Enterprise License Agreement",
    "value": 50000.00,
    "stage": "proposal",
    "description": "Annual enterprise license for 500 seats"
  }'
```

This should trigger the workflow and create a task automatically.

### Test 2: Low-Value Deal (Should NOT Trigger Task)

Create a deal with value <= 10000.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/deals:create" \
  -d '{
    "title": "Small Consulting Project",
    "value": 5000.00,
    "stage": "qualification",
    "description": "Short-term consulting engagement"
  }'
```

This should trigger the workflow but the condition node should stop execution (deal value is not > 10000).

## Step 7 -- Check Execution Status

### List Recent Executions

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/executions:list?filter={\"workflowId\":1}&sort=[-createdAt]&page=1&pageSize=10"
```

**Expected:** Two executions.

- The first (high-value deal) should have `status: 1` (resolved/completed).
- The second (low-value deal) should have `status: -1` (rejected by condition) or `status: 1` with the condition node rejecting.

### Get Execution Details with Jobs

Inspect the full execution trace for the high-value deal.

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/executions:get?filterByTk=1&appends=jobs"
```

**Expected response structure:**

```json
{
  "data": {
    "id": 1,
    "workflowId": 1,
    "status": 1,
    "context": {
      "data": {
        "title": "Enterprise License Agreement",
        "value": 50000.00
      }
    },
    "jobs": [
      {
        "id": 1,
        "nodeId": 1,
        "status": 1,
        "result": true
      },
      {
        "id": 2,
        "nodeId": 2,
        "status": 1,
        "result": {
          "id": 1,
          "title": "Follow up on high-value deal: Enterprise License Agreement"
        }
      }
    ]
  }
}
```

Each job corresponds to a node execution:
- Job 1 (condition node): `result: true` means the deal passed the value check.
- Job 2 (create node): `result` contains the newly created task record.

## Step 8 -- Verify the Task Was Created

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/tasks:list?sort=[-createdAt]&page=1&pageSize=5"
```

**Expected:** A task record matching the high-value deal.

```json
{
  "data": [
    {
      "id": 1,
      "title": "Follow up on high-value deal: Enterprise License Agreement",
      "description": "A new deal worth $50000 has been created. Schedule a meeting with the contact to discuss next steps and timeline.",
      "priority": "high",
      "status": "open",
      "dealTitle": "Enterprise License Agreement",
      "dealValue": 50000.00
    }
  ],
  "meta": { "count": 1, "page": 1, "pageSize": 5, "totalPage": 1 }
}
```

Verify that:
- Only one task exists (the low-value deal did not create a task).
- The task title includes the deal name.
- The priority is "high".
- The deal value is correctly copied.

## Extending the Workflow

Once the basic workflow is working, you can extend it with additional nodes:

### Add a Notification Node

After the create node, add a request node to send a webhook notification:

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/workflows/1/nodes:create" \
  -d '{
    "type": "request",
    "title": "Notify Sales Manager",
    "config": {
      "url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
      "method": "POST",
      "headers": [
        { "name": "Content-Type", "value": "application/json" }
      ],
      "data": {
        "text": "New high-value deal created: {{$context.data.title}} (${{$context.data.value}}). A follow-up task has been assigned."
      },
      "timeout": 5000,
      "ignoreFail": true
    }
  }'
```

### Add Tiered Priority Logic

Replace the single condition node with multiple conditions for tiered prioritization:

- Deal > 100,000: priority "urgent"
- Deal > 50,000: priority "high"
- Deal > 10,000: priority "medium"

This requires creating separate condition and create node pairs for each tier, or using a calculation node to compute the priority dynamically.

## Summary

This scenario demonstrated:

- **1 workflow** with a collection trigger on the deals collection
- **1 condition node** checking deal value > 10,000
- **1 create node** generating a task record with data from the triggering deal
- **2 test cases**: high-value deal (task created) and low-value deal (no task)
- **Execution monitoring** to verify workflow behavior

## Cleanup

```bash
# Disable the workflow
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/workflows:update?filterByTk=1" \
  -d '{"enabled": false}'

# Delete the workflow
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/workflows:destroy?filterByTk=1"

# Delete the tasks collection
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/collections:destroy?filterByTk=tasks"
```
