---
description: Create a new CRM deal in a pipeline
allowed-tools: mcp__sendpulse__crm_deals_create, mcp__sendpulse__crm_pipelines_list, mcp__sendpulse__crm_pipelines_steps_list
argument-hint: <deal-name> [--pipeline <id>] [--amount <amount>]
---

# Create Deal

Create a new CRM deal in a sales pipeline.

## Arguments
Format: `<deal-name> [--pipeline <id>] [--amount <amount>]`
- deal-name: Name for the deal
- --pipeline: Pipeline ID (optional — lists pipelines if omitted)
- --amount: Deal amount (optional)

Parse from "$ARGUMENTS".

## Process

1. **List pipelines if not specified:**
   ```
   crm_pipelines_list()
   ```
   Show available pipelines. Ask user to select.

2. **Get pipeline steps:**
   ```
   crm_pipelines_steps_list(pipeline_id=<pipeline-id>)
   ```
   Use the first step as default.

3. **Create deal:**
   ```
   crm_deals_create(
     name=<deal-name>,
     pipeline_id=<pipeline-id>,
     step_id=<first-step-id>,
     amount=<amount>
   )
   ```

4. **Report result:**
   - Deal ID
   - Pipeline name and stage
   - Amount

## Example Usage
```
/create-deal "Enterprise License" --pipeline pipe_001 --amount 50000
/create-deal "Website Redesign"
/create-deal "Q2 Campaign" --amount 10000
```

## Notes
- Deal is created at the first pipeline step by default
- If no pipeline specified, shows all available pipelines
- Amount is optional and can be added later
