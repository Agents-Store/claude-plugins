# dataforseo-dev

DataForSEO data analysis plugin for [Agents Store](https://github.com/agents-store). Provides keyword research, competitor analysis, backlink auditing, SERP monitoring, on-page audits, content analysis, and AI optimization tracking via 70+ MCP tools.

## What This Plugin Does

This plugin enriches developers with comprehensive SEO data tools powered by DataForSEO's API. Unlike `seo-dev` (which teaches code-level SEO implementation), `dataforseo-dev` provides the **data layer** — helping you decide *what* to optimize by analyzing real search data.

## Skills

| Skill | Description |
|-------|-------------|
| **setup** | Verify DataForSEO MCP connection and credentials |
| **mcp-patterns** | All 70+ MCP tools organized by category with parameters and usage patterns |
| **api-reference** | REST API endpoints with curl examples (reference-only) |
| **keyword-research** | Keyword discovery, difficulty assessment, gap analysis workflows |
| **competitor-analysis** | Domain comparison, keyword gaps, competitive landscape |
| **backlink-audit** | Link profile analysis, spam detection, prospecting workflows |
| **site-audit** | Lighthouse audits, content parsing, technology detection |
| **ai-optimization** | LLM mention tracking, ChatGPT visibility, AI search optimization |
| **troubleshoot** | Common errors, diagnostics, and fixes |
| **examples** | End-to-end scenario walkthroughs |

## Commands

| Command | Description |
|---------|-------------|
| `/dataforseo-dev:keyword-research <topic>` | Run keyword research for a topic or domain |
| `/dataforseo-dev:site-audit <url>` | Run on-page SEO audit for a URL |
| `/dataforseo-dev:competitor-analysis <domain>` | Compare a domain against competitors |

## Agent

**seo-data-analyst** — SEO data analysis specialist that orchestrates multi-tool workflows for comprehensive SEO analysis.

## Prerequisites

- **DataForSEO account** — Sign up at [dataforseo.com](https://dataforseo.com)
- **Node.js >= v20.0.0** — Required for the MCP server
- **Environment variables:**
  - `DATAFORSEO_USERNAME` — Your DataForSEO account email
  - `DATAFORSEO_PASSWORD` — Your DataForSEO account password

## MCP Server

This plugin includes a `.mcp.json` configuration that runs the official [dataforseo-mcp-server](https://www.npmjs.com/package/dataforseo-mcp-server) via npx. The server provides 70+ tools across 9 API modules:

- **SERP** — Search engine results (Google, YouTube, Bing)
- **DataForSEO Labs** — Keyword research and domain analysis
- **Backlinks** — Link profiles, referring domains, spam scores
- **Keywords Data** — Google Ads volume, Google Trends, DFS Trends
- **OnPage** — Lighthouse audits, page analysis, content parsing
- **Content Analysis** — Sentiment, citations, phrase trends
- **Domain Analytics** — Technology detection, WHOIS
- **AI Optimization** — LLM mentions, ChatGPT scraping, AI search
- **Business Data** — Business listings

## Cost Model

DataForSEO uses a pay-per-request pricing model. Each API call costs credits. Monitor usage at [app.dataforseo.com](https://app.dataforseo.com). The plugin's skills include cost optimization guidance.
