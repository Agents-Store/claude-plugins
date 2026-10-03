# web-search-dev

Developer reference for web search, scraping and documentation lookup in Claude Code: 5 bundled MCP servers (47 tools), REST APIs, SDKs and CLIs, plus Pexels and Unsplash REST media search. Role in the search family: tools and API reference for developers (search, scraping, documentation lookup).

This plugin also replaces `image-search-dev` (retired; installed copies are renamed to `web-search-dev`).

## Services

| Service | Tools | Use For |
|---------|-------|---------|
| **Firecrawl** | 27 MCP tools | Scraping, crawling, structured JSON extraction, agent research, live-page interaction, file parsing, change monitors, Alexandria data providers |
| **Exa** | 2 MCP tools (search + fetch), +2 opt-in | Semantic web search, page fetching, advanced filters and `agent_run` (opt-in) |
| **Perplexity** | 4 MCP tools | Search, AI-powered Q&A, deep research, reasoning |
| **Jina** | 12 MCP tools | Page reading (batch + question mode), web/academic/image search, reranking, deduplication |
| **Context7** | 2 MCP tools | Up-to-date framework/library documentation |
| **Pexels** | REST (`curl`) | Stock photos and videos |
| **Unsplash** | REST (`curl`) | High-quality stock photos (API guidelines apply) |

## Skills

| Skill | Description |
|-------|-------------|
| **setup** | Verify which services are connected and operational |
| **mcp-patterns** | All 47 MCP tools with routing table, per-service references and media REST reference |
| **api-reference** | REST API endpoints with curl examples for all services, including Pexels and Unsplash |
| **sdk-patterns** | SDK installation and code patterns (TypeScript + Python) |
| **cli-recipes** | Firecrawl CLI and Jina CLI commands and workflows |
| **web-scraping** | Practical scraping patterns: single page, batch, crawl, extraction |
| **doc-search** | Find framework docs using Context7, Exa, and Perplexity |
| **media-search** | Find stock photos and videos with the Pexels and Unsplash REST APIs and Jina |
| **troubleshoot** | Per-service error diagnostics and fixes |
| **examples** | End-to-end scenario walkthroughs |

## Agent

**web-search-developer** — Developer specialist for web scraping, documentation search, media discovery, and search service integration. It inherits all tools, including the five bundled MCP servers.

## Installation

Install via Agents Store marketplace or add directly to Claude Code.

## MCP Configuration

The plugin bundles `.mcp.json` with 5 MCP servers:
- Firecrawl (stdio via npx)
- Exa (stdio via npx, `exa-mcp-server`)
- Perplexity (stdio via npx)
- Jina (native HTTP transport, `https://mcp.jina.ai/v1`)
- Context7 (stdio via npx)

Hosted alternatives (if you prefer remote MCP over npx; keep `${VAR}` placeholders for keys):
- Firecrawl: `https://mcp.firecrawl.dev/v2/mcp` (keyless: 3 tools; OAuth variant: `/v2/mcp-oauth`)
- Exa: `https://mcp.exa.ai/mcp` (OAuth with `?login`; `agent_run` on by default once authenticated)
- Perplexity: `https://api.perplexity.ai/mcp` (OAuth sign-in or API key)
- Context7: `https://mcp.context7.com/mcp` (Bearer auth)

API keys are configured via standard environment variables (`FIRECRAWL_API_TOKEN`, `EXA_API_KEY`, `PERPLEXITY_API_KEY`, `JINA_API_KEY`, `CONTEXT7_API_KEY`).

Exa's `web_search_advanced_exa` and `agent_run` are opt-in on the bundled server: set `ENABLED_TOOLS=web_search_exa,web_fetch_exa,web_search_advanced_exa,agent_run` in the environment that launches Claude Code.

## Media search (Pexels and Unsplash — REST)

No MCP server is involved: the `media-search` skill calls the public REST APIs with `curl`. Both keys are optional.

| Variable | Service |
|----------|---------|
| `PEXELS_API_KEY` | Pexels (200 req/hour, 20,000 req/month) |
| `UNSPLASH_ACCESS_KEY` | Unsplash (demo 50 req/hour, production 1,000 req/hour) |

Unsplash API use requires hotlinking `photo.urls.*`, calling `photo.links.download_location` when a photo is used, and attributing the photographer and Unsplash with `utm_source` links; Pexels requires a link to Pexels and photographer credit. The checklist is in `media-search`.

## Prerequisites

- Node.js 22+ (for MCP servers via npx — `firecrawl-mcp` requires it; `exa-mcp-server` and `@upstash/context7-mcp` need 20+)
- API keys for services you want to use (at least one)
