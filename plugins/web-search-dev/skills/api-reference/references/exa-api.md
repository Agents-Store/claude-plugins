# Exa REST API

Base URL: `https://api.exa.ai`

## Search (Primary Endpoint)

```bash
curl -s -X POST https://api.exa.ai/search \
  -H "x-api-key: ${EXA_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "React server components patterns",
    "numResults": 10,
    "type": "auto"
  }' | jq .
```

## Search with Content Extraction

Get search results + full page content in one call:

```bash
curl -s -X POST https://api.exa.ai/search \
  -H "x-api-key: ${EXA_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Prisma ORM pagination example",
    "numResults": 5,
    "contents": {
      "text": { "maxCharacters": 5000 },
      "highlights": { "maxCharacters": 200 }
    }
  }' | jq .
```

## Domain-Scoped Search

```bash
curl -s -X POST https://api.exa.ai/search \
  -H "x-api-key: ${EXA_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication middleware",
    "numResults": 10,
    "includeDomains": ["github.com", "stackoverflow.com"]
  }' | jq .
```

## Category Search

```bash
curl -s -X POST https://api.exa.ai/search \
  -H "x-api-key: ${EXA_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Vercel",
    "category": "company",
    "numResults": 5
  }' | jq .
```

**Warning:** `category: "company"` and `category: "people"` disable date, text, and excludeDomains filters.

## Date-Filtered Search

```bash
curl -s -X POST https://api.exa.ai/search \
  -H "x-api-key: ${EXA_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Next.js 15 new features",
    "numResults": 10,
    "startPublishedDate": "2025-01-01T00:00:00.000Z"
  }' | jq .
```

## Deep Search

```bash
curl -s -X POST https://api.exa.ai/search \
  -H "x-api-key: ${EXA_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare tRPC vs GraphQL for Next.js",
    "type": "deep",
    "numResults": 10
  }' | jq .
```

Types: `auto` (default), `fast`, `instant`, `deep`, `deep-reasoning`.

## Search with Summary

```bash
curl -s -X POST https://api.exa.ai/search \
  -H "x-api-key: ${EXA_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Tailwind CSS v4 migration guide",
    "numResults": 5,
    "contents": {
      "summary": { "query": "What changed in Tailwind v4?" }
    }
  }' | jq .
```

## Response Format

```json
{
  "results": [
    {
      "title": "Page Title",
      "url": "https://example.com/page",
      "publishedDate": "2025-03-01",
      "score": 0.95,
      "text": "Full page content...",
      "highlights": ["Key excerpt..."],
      "summary": "AI-generated summary..."
    }
  ],
  "costDollars": { "total": 0.008 }
}
```

## Common Mistakes

- `useAutoprompt` is DEPRECATED — do not use
- `text`, `highlights`, `summary` must be nested inside `contents`
- `livecrawl: "always"` is deprecated — use `contents.maxAgeHours: 0`
- `numSentences`, `highlightsPerUrl`, `tokensNum` do not exist
