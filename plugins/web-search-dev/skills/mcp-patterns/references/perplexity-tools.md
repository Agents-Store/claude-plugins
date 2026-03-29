# Perplexity MCP Tools (4 tools)

Perplexity provides **AI-synthesized answers** with citations. Each tool uses a different model optimized for specific tasks.

## perplexity_search
Quick web search using Sonar Pro model. Best for finding current information, news, facts, and specific web content.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Search query |

```
Tool: perplexity_search
Input: { "query": "What are the latest Next.js 15 features?" }
```

Returns an AI-synthesized answer with source URLs. Use this for factual lookups and quick questions.

## perplexity_ask
Quick questions using Sonar model. Best for everyday searches and conversational queries.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Question to ask |

```
Tool: perplexity_ask
Input: { "query": "How do I set up Tailwind CSS in a Next.js 15 project?" }
```

Lower cost than `perplexity_search`, good for straightforward questions.

## perplexity_research
Deep research using Sonar Deep Research model. Best for complex topics requiring comprehensive analysis.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Research topic |

```
Tool: perplexity_research
Input: { "query": "Compare tRPC vs GraphQL vs REST for Next.js applications in 2025" }
```

Takes longer but produces thorough, well-cited analysis. Use for complex comparisons, technical evaluations, and multi-aspect topics.

## perplexity_reason
Logical reasoning using Sonar Reasoning Pro model. Best for step-by-step analysis and complex problem solving.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Problem to reason about |

```
Tool: perplexity_reason
Input: { "query": "My Next.js app has a hydration mismatch error when using date formatting. The server renders '3/29/2025' but the client renders '03/29/2025'. Why does this happen and how to fix it?" }
```

Best for debugging, logic problems, and step-by-step explanations.

## When to Use Which Tool

| Need | Tool | Model |
|------|------|-------|
| Quick facts, current info | `perplexity_search` | Sonar Pro |
| Simple questions | `perplexity_ask` | Sonar |
| In-depth analysis | `perplexity_research` | Sonar Deep Research |
| Logic / debugging | `perplexity_reason` | Sonar Reasoning Pro |

## API Key

All 4 tools require `PERPLEXITY_API_KEY`. Get one at https://console.perplexity.ai.
