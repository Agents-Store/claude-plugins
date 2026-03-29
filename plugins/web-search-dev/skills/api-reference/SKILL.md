---
name: api-reference
description: This skill should be used when the user asks for "Firecrawl API endpoints", "Exa REST API", "Perplexity API reference", "Jina API curl examples", "web search API documentation", or needs specific HTTP endpoint details for any of the web search and scraping services.
disable-model-invocation: true
---

# Web Search Services API Reference

Curated REST API endpoints for all 4 core services. For full documentation, visit each service's official docs.

## Authentication Summary

| Service | Auth Header | Key Format | Docs |
|---------|------------|------------|------|
| Firecrawl | `Authorization: Bearer KEY` | `fc-xxx` | https://docs.firecrawl.dev |
| Exa | `x-api-key: KEY` | UUID string | https://docs.exa.ai |
| Perplexity | `Authorization: Bearer KEY` | String | https://docs.perplexity.ai |
| Jina | `Authorization: Bearer KEY` | `jina_xxx` | https://jina.ai/reader |

## Service Endpoints

### Firecrawl — `https://api.firecrawl.dev`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/scrape` | Scrape single URL |
| POST | `/v1/search` | Web search with content |
| POST | `/v1/crawl` | Start site crawl |
| GET | `/v1/crawl/{id}` | Check crawl status |
| POST | `/v1/map` | Map site URLs |
| POST | `/v1/extract` | LLM structured extraction |
| POST | `/v1/agent` | Autonomous research agent |
| POST | `/v1/browser` | Create browser session |

See `references/firecrawl-api.md` for curl examples.

### Exa — `https://api.exa.ai`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/search` | Semantic web search (single powerful endpoint) |
| POST | `/contents` | Fetch content by document ID |

See `references/exa-api.md` for curl examples.

### Perplexity — `https://api.perplexity.ai`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/agent` | Agent API (third-party models + web search) |
| POST | `/v1/search` | Web search |
| POST | `/v1/sonar` | Chat completion with web grounding |
| POST | `/v1/embeddings` | Text embeddings |

See `references/perplexity-api.md` for curl examples.

### Jina — Multiple base URLs

| Method | URL Pattern | Description |
|--------|------------|-------------|
| GET | `https://r.jina.ai/{URL}` | Read any URL as markdown |
| GET | `https://s.jina.ai/?q={QUERY}` | Web search |
| POST | `https://api.jina.ai/v1/embeddings` | Text embeddings |
| POST | `https://api.jina.ai/v1/rerank` | Rerank documents |
| POST | `https://api.jina.ai/v1/classify` | Text classification |

See `references/jina-api.md` for curl examples.
