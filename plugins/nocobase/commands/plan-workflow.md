---
description: Plan a NocoBase workflow automation
allowed-tools: []
argument-hint: <description>
---

# Plan Workflow

Design a NocoBase workflow automation with trigger, nodes, and conditions.

## Arguments
Format: `<description>`
- description: What the workflow should do (required)

Parse from "$ARGUMENTS".

## Process

1. **Analyze requirements:**
   - What triggers the workflow? (collection event, schedule, manual)
   - What actions should occur?
   - What conditions or branches are needed?

2. **Design workflow:**
   - Define trigger type and configuration
   - Plan node chain (condition, query, create, update, request, etc.)
   - Define variable mappings between nodes

3. **Provide implementation guidance:**
   Show workflow configuration for NocoBase.

## Example Usage
```
/plan-workflow "Send email notification when a new order is created"
/plan-workflow "Auto-assign tasks to team members based on priority"
/plan-workflow "Generate daily sales report and send to Slack"
```
