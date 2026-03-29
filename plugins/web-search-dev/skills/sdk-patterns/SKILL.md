---
name: sdk-patterns
description: This skill should be used when the user asks about "Firecrawl SDK", "Exa SDK", "exa-js", "exa-py", "Perplexity SDK", "Jina SDK", "web search client library", "search npm package", "search Python package", or needs code patterns for integrating web search services into a project.
---

# Web Search Services SDK Patterns

Code patterns for integrating Firecrawl, Exa, Perplexity, and Jina into application code.

## Firecrawl

### Installation

```bash
npm install firecrawl     # Node.js
pip install firecrawl-py  # Python
```

### TypeScript

```typescript
import Firecrawl from 'firecrawl';

const firecrawl = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });

// Scrape a page
const result = await firecrawl.scrapeUrl('https://example.com', {
  formats: ['markdown', 'links'],
});
console.log(result.markdown);

// Search the web
const searchResults = await firecrawl.search('Next.js tutorials', { limit: 10 });

// Crawl a site
const crawl = await firecrawl.crawlUrl('https://docs.example.com', {
  limit: 50,
  maxDepth: 3,
});

// Extract structured data
const extracted = await firecrawl.extract(['https://example.com/pricing'], {
  prompt: 'Extract pricing plans',
  schema: { type: 'array', items: { type: 'object', properties: { plan: { type: 'string' }, price: { type: 'string' } } } },
});
```

### Python

```python
from firecrawl import FirecrawlApp

app = FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])

# Scrape
result = app.scrape_url("https://example.com", params={"formats": ["markdown"]})
print(result["markdown"])

# Search
results = app.search("Next.js tutorials", params={"limit": 10})

# Crawl
crawl = app.crawl_url("https://docs.example.com", params={"limit": 50})
```

---

## Exa

### Installation

```bash
npm install exa-js        # Node.js
pip install exa-py        # Python
```

### TypeScript

```typescript
import Exa from 'exa-js';

const exa = new Exa(process.env.EXA_API_KEY);

// Basic search
const results = await exa.search('React hooks best practices', {
  numResults: 10,
  type: 'auto',
});

// Search with content
const withContent = await exa.search('Prisma ORM examples', {
  numResults: 5,
  contents: {
    text: { maxCharacters: 5000 },
    highlights: { maxCharacters: 200 },
  },
});

// Domain-scoped search
const githubResults = await exa.search('authentication middleware', {
  numResults: 10,
  includeDomains: ['github.com'],
});

// Find similar pages
const similar = await exa.findSimilar('https://example.com/article', {
  numResults: 10,
});
```

### Python

```python
from exa_py import Exa

exa = Exa(api_key=os.environ["EXA_API_KEY"])

# Search (Python uses snake_case for all params)
results = exa.search(
    "React hooks patterns",
    num_results=10,
    type="auto"
)

# Search with content
with_content = exa.search(
    "Prisma examples",
    num_results=5,
    contents={"text": {"max_characters": 5000}}
)
```

---

## Perplexity

### Installation

```bash
npm install @perplexity-ai/perplexity_ai  # Node.js
pip install perplexityai                    # Python
```

### TypeScript

```typescript
import { Perplexity } from '@perplexity-ai/perplexity_ai';

const client = new Perplexity({ apiKey: process.env.PERPLEXITY_API_KEY });

// Agent API (recommended)
const response = await client.agent.create({
  input: 'Compare tRPC vs GraphQL for Next.js',
  preset: 'pro-search',
});

// Sonar API
const sonarResponse = await client.sonar.create({
  model: 'sonar-pro',
  messages: [
    { role: 'user', content: 'What are the latest React 19 features?' },
  ],
});
```

### Python

```python
from perplexity import Perplexity

client = Perplexity()  # auto-reads PERPLEXITY_API_KEY env var

# Agent API
response = client.agent.create(
    input="Compare tRPC vs GraphQL for Next.js",
    preset="pro-search"
)

# Sonar API
sonar_response = client.sonar.create(
    model="sonar-pro",
    messages=[{"role": "user", "content": "React 19 features"}]
)
```

---

## Jina

Jina's API is HTTP-based — no dedicated SDK package needed. Use `fetch` or `requests` directly.

### TypeScript

```typescript
// Read a URL
const response = await fetch('https://r.jina.ai/https://nextjs.org/docs', {
  headers: { 'Authorization': `Bearer ${process.env.JINA_API_KEY}` },
});
const markdown = await response.text();

// Search
const searchResponse = await fetch('https://s.jina.ai/?q=React+hooks', {
  headers: {
    'Authorization': `Bearer ${process.env.JINA_API_KEY}`,
    'Accept': 'application/json',
  },
});
const results = await searchResponse.json();

// Embeddings
const embedResponse = await fetch('https://api.jina.ai/v1/embeddings', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${process.env.JINA_API_KEY}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    model: 'jina-embeddings-v5-text-small',
    input: ['text to embed'],
  }),
});
```

### Python

```python
import requests

headers = {"Authorization": f"Bearer {os.environ['JINA_API_KEY']}"}

# Read a URL
response = requests.get("https://r.jina.ai/https://example.com", headers=headers)
markdown = response.text

# Search
search = requests.get(
    "https://s.jina.ai/",
    params={"q": "React hooks"},
    headers={**headers, "Accept": "application/json"}
)
results = search.json()

# Rerank
rerank = requests.post(
    "https://api.jina.ai/v1/rerank",
    headers={**headers, "Content-Type": "application/json"},
    json={
        "model": "jina-reranker-v3",
        "query": "best database for real-time",
        "documents": ["PostgreSQL", "Redis", "MongoDB"]
    }
)
```

---

## Best Practices

- Store API keys in environment variables, never in code
- Handle rate limits with exponential backoff
- Use the appropriate service for each task (see mcp-patterns routing table)
- Prefer SDK methods over raw HTTP when SDK is available
- Use TypeScript types for type safety when integrating search results
