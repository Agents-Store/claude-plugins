---
description: Start an autonomous web research agent
allowed-tools: ["mcp__firecrawl__agent", "mcp__firecrawl__agent_status"]
argument-hint: <research-prompt> [--urls <url1,url2>]
---

# Agent Research

Start an autonomous research agent that browses, searches, and extracts information based on a natural language task description.

## Arguments
Format: `<research-prompt> [--urls <url1,url2>]`
- research-prompt: Description of the research task (required, max 10,000 chars)
- --urls: Starting URLs to guide the agent, comma-separated (optional)

Parse from "$ARGUMENTS".

## Process

1. **Start research agent:**
   Use `agent` with the research prompt and optional starting URLs.

2. **Monitor progress:**
   Use `agent_status` to poll until the agent completes.

3. **Present results:**
   Show the agent's findings in a structured format.

## Example Usage
```
/agent-research "Compare pricing plans for the top 5 CRM tools"
/agent-research "Analyze the API documentation of Stripe vs PayPal" --urls https://docs.stripe.com,https://developer.paypal.com
/agent-research "Find the latest AI automation tools launched in the last month"
```
