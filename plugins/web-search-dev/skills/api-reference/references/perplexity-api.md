# Perplexity REST API

Base URL: `https://api.perplexity.ai`

## Agent API (Recommended)

The Agent API supports third-party models with web search tools, presets, and model fallback chains. The **simplest way** to use it is with presets — one parameter controls the depth of research:

### Quick Start with Presets

```bash
# Fast factual lookup (cheapest, fastest)
curl -s -X POST https://api.perplexity.ai/v1/agent \
  -H "Authorization: Bearer ${PERPLEXITY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"input": "What are the latest Next.js 15 features?", "preset": "fast-search"}' | jq .

# Detailed analysis with web search
curl -s -X POST https://api.perplexity.ai/v1/agent \
  -H "Authorization: Bearer ${PERPLEXITY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"input": "Compare tRPC vs GraphQL for Next.js apps", "preset": "pro-search"}' | jq .

# Comprehensive multi-step research (most thorough, slowest)
curl -s -X POST https://api.perplexity.ai/v1/agent \
  -H "Authorization: Bearer ${PERPLEXITY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"input": "State of WebAssembly adoption in 2025", "preset": "deep-research"}' | jq .
```

| Preset | Speed | Depth | Best For |
|--------|-------|-------|----------|
| `fast-search` | Fast | Light | Quick facts, current info |
| `pro-search` | Medium | Detailed | Comparisons, technical analysis |
| `deep-research` | Slow | Comprehensive | In-depth reports, multi-aspect topics |

### With Specific Model

```bash
curl -s -X POST https://api.perplexity.ai/v1/agent \
  -H "Authorization: Bearer ${PERPLEXITY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Compare React Server Components vs Client Components performance",
    "model": "openai/gpt-4o",
    "preset": "pro-search"
  }' | jq .
```

### Presets

| Preset | Best For |
|--------|----------|
| `fast-search` | Quick factual lookups |
| `pro-search` | Detailed analysis with web search |
| `deep-research` | Comprehensive multi-step research |

### Model Fallback Chain

```bash
curl -s -X POST https://api.perplexity.ai/v1/agent \
  -H "Authorization: Bearer ${PERPLEXITY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Explain React 19 new hooks",
    "models": ["anthropic/claude-sonnet-4-6", "openai/gpt-4o", "xai/grok-4-1"],
    "preset": "pro-search"
  }' | jq .
```

### With Streaming

```bash
curl -s -X POST https://api.perplexity.ai/v1/agent \
  -H "Authorization: Bearer ${PERPLEXITY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "How to implement OAuth 2.0 in Next.js",
    "preset": "fast-search",
    "stream": true
  }'
```

## Sonar API (Perplexity Models)

Direct access to Perplexity's own models with web-grounded responses.

```bash
curl -s -X POST https://api.perplexity.ai/v1/sonar \
  -H "Authorization: Bearer ${PERPLEXITY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sonar-pro",
    "messages": [
      { "role": "user", "content": "What is the current state of WebAssembly support in browsers?" }
    ]
  }' | jq .
```

### Sonar Models

| Model | Best For |
|-------|----------|
| `sonar` | Quick answers |
| `sonar-pro` | Detailed answers with citations |
| `sonar-reasoning-pro` | Step-by-step reasoning |
| `sonar-deep-research` | Comprehensive research |

## Search API

```bash
curl -s -X POST https://api.perplexity.ai/v1/search \
  -H "Authorization: Bearer ${PERPLEXITY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "React 19 new features"
  }' | jq .
```

## Response Format (Agent API)

```json
{
  "id": "resp_xxx",
  "model": "openai/gpt-4o",
  "status": "completed",
  "output": [
    {
      "type": "message",
      "content": "AI-generated response..."
    },
    {
      "type": "search_results",
      "results": [
        { "title": "...", "url": "..." }
      ]
    }
  ],
  "usage": {
    "input_tokens": 150,
    "output_tokens": 500,
    "total_cost": 0.015
  }
}
```
