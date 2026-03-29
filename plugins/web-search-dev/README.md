# web-search-dev

Web search and scraping developer toolkit for Claude Code. Covers 7 services with 60+ MCP tools, REST APIs, SDKs, and CLIs for practical development tasks.

## Services

| Service | Tools | Use For |
|---------|-------|---------|
| **Firecrawl** | 12 MCP tools | Scraping, crawling, structured extraction, browser automation |
| **Exa** | 4 MCP tools | Semantic web search, code examples, domain-scoped search |
| **Perplexity** | 4 MCP tools | AI-powered Q&A, deep research, reasoning |
| **Jina** | 19 MCP tools | Page reading, parallel ops, image search, text classification |
| **Context7** | 2 MCP tools | Up-to-date framework/library documentation |
| **Pexels** | 9 MCP tools | Stock photos and videos |
| **Unsplash** | 4 MCP tools | High-quality stock photos |

## Skills

| Skill | Description |
|-------|-------------|
| **setup** | Verify which services are connected and operational |
| **mcp-patterns** | All 60+ MCP tools with routing table and per-service references |
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
- Exa (stdio via mcp-remote)
- Perplexity (stdio via npx)
- Jina (stdio via mcp-remote)
- Context7 (stdio via npx)

API keys are configured via `userConfig` — Claude Code prompts for them when the plugin is enabled.

Pexels and Unsplash require separate MCP configuration.

## Relationship to deep-research

This plugin complements the `deep-research` plugin:
- **deep-research** — Research orchestration: 7-step algorithm, report templates, CONNECTORS pattern
- **web-search-dev** — Developer toolkit: direct service knowledge, practical scraping, doc search, media discovery

Use `deep-research` for research reports. Use `web-search-dev` for building applications.

## Prerequisites

- Node.js 18+ (for MCP servers via npx)
- API keys for services you want to use (at least one)
