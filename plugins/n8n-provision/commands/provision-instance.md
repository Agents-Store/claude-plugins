---
description: Run a full instance provisioning session with multiple workflows
allowed-tools: ["Bash", "Read", "Grep"]
argument-hint: [--preset <startup|devops|marketing|custom>] [--dry-run]
---

# Provision Instance

Batch-provision an n8n instance with a suite of workflows.

## Arguments
Format: `[--preset <startup|devops|marketing|custom>] [--dry-run]`
- --preset: Use a predefined workflow suite (default: custom — interactive selection)
  - startup: 10 essential workflows for SaaS startups
  - devops: 8 DevOps monitoring and CI/CD workflows
  - marketing: 8 marketing automation workflows
  - custom: interactive — user describes what they need, agent searches and proposes
- --dry-run: Analyze and plan without actually deploying

Parse from "$ARGUMENTS".

## Process

1. **Check instance readiness** (follow `instance-readiness` skill):
   - Health check via `~~instance_audit`
   - Existing workflow inventory via `~~workflow_list`
   - Check for naming conflicts

2. **Build workflow list:**
   - If preset: load from `batch-provisioning` skill presets (see `references/BATCH_STRATEGIES.md`)
   - If custom: ask user what they need, search via `~~template_search`, propose a list

3. **Analyze each workflow:**
   - Run `workflow-analysis` on every candidate
   - Compile credential requirements across all workflows
   - Flag any issues (community nodes, security, compatibility)

4. **Present provisioning plan:**
   - Workflow list with analysis summaries
   - Credential setup checklist (grouped by service)
   - Estimated import order (dependency-aware)
   - If `--dry-run`: stop here

5. **Execute batch import** (follow `batch-provisioning` skill):
   - Deploy one-by-one with validation between each
   - Tag with batch identifier
   - Report progress after each deployment

6. **Post-provisioning report:**
   - All deployed workflows with IDs
   - Credential setup checklist
   - Activation instructions
   - Any failures and remediation steps

## Example Usage
```
/n8n-provision:provision-instance --preset startup
/n8n-provision:provision-instance --preset devops --dry-run
/n8n-provision:provision-instance --preset custom
```
