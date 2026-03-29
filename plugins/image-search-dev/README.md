# image-search-dev

Stock image and video search developer toolkit for Claude Code. Provides MCP tool patterns, usage examples, and troubleshooting for Pexels and Unsplash via the `mcpware-dev-tools` MCP server.

## Services

| Service | Tools | Content | License |
|---------|-------|---------|---------|
| **Pexels** | 9 | Photos + Videos | Free commercial, attribution appreciated |
| **Unsplash** | 4 | Photos only | Unsplash License (free commercial) |
| **MinIO** | 1 | Upload to storage | N/A |

## Skills

| Skill | Description |
|-------|-------------|
| `setup` | Verify Pexels and Unsplash MCP tools are accessible |
| `mcp-patterns` | All 13 tools with parameters, task routing, and usage patterns |
| `examples` | 4 end-to-end scenario walkthroughs |
| `troubleshoot` | Rate limits, API errors, and diagnostic steps |

## Agent

**image-search-developer** — Stock image and video search specialist. Helps find photos, videos, browse collections, and integrate media into applications.

## Prerequisites

- The `mcpware-dev-tools` MCP server must be configured in your Claude Code settings
- Valid API keys for Pexels and/or Unsplash configured in the MCP server

This plugin provides knowledge only — MCP connections are configured separately via the `mcpware-dev-tools` server.

## Relationship to web-search-dev

The `web-search-dev` plugin covers image search tools as part of a broader web search toolkit (Firecrawl, Exa, Perplexity, Jina, Pexels, Unsplash, Context7). This plugin is a focused standalone alternative for users who only need stock image/video search without the web scraping and documentation search capabilities.
