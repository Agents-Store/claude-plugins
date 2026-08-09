# web-search-dev

Web search and scraping developer toolkit for Claude Code. Covers 7 services with 65+ MCP tools, REST APIs, SDKs, and CLIs for practical development tasks.

## Services

| Service | Tools | Use For |
|---------|-------|---------|
| **Firecrawl** | 27 MCP tools | Scraping, crawling, structured extraction, live-page interaction, file parsing, change monitors |
| **Exa** | 2 MCP tools (search + fetch) | Semantic web search, page fetching, domain-scoped search |
| **Perplexity** | 4 MCP tools | AI-powered Q&A, deep research, reasoning |
| **Jina** | 21 MCP tools | Page reading, parallel ops, image search, text classification |
| **Context7** | 2 MCP tools | Up-to-date framework/library documentation |
| **Pexels** | 9 MCP tools | Stock photos and videos |
| **Unsplash** | 4 MCP tools | High-quality stock photos |

## Skills

| Skill | Description |
|-------|-------------|
| **setup** | Verify which services are connected and operational |
| **mcp-patterns** | All 65+ MCP tools with routing table and per-service references |
| **api-reference** | REST API endpoints with curl examples for all services |
| **sdk-patterns** | SDK installation and code patterns (TypeScript + Python) |
| **cli-recipes** | Firecrawl CLI and Jina CLI commands and workflows |
| **web-scraping** | Practical scraping patterns: single page, batch, crawl, extraction |
| **doc-search** | Find framework docs using Context7, Exa, and Perplexity |
| **media-search** | Find stock photos and videos with Pexels, Unsplash, Jina |
| **troubleshoot** | Per-service error diagnostics and fixes |
| **examples** | End-to-end scenario walkthroughs |

## Agent

**web-search-developer** — Developer specialist for web scraping, documentation search, media discovery, and search service integration.

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
- Firecrawl: `https://mcp.firecrawl.dev/v2/mcp` (OAuth variant: `/v2/mcp-oauth`)
- Exa: `https://mcp.exa.ai/mcp`
- Perplexity: `https://api.perplexity.ai/mcp`
- Context7: `https://mcp.context7.com/mcp` (Bearer auth)

API keys are configured via standard environment variables (`FIRECRAWL_API_TOKEN`, `EXA_API_KEY`, `PERPLEXITY_API_KEY`, `JINA_API_KEY`).

Pexels and Unsplash require separate MCP configuration.

## Prerequisites

- Node.js 18+ (for MCP servers via npx)
- API keys for services you want to use (at least one)
