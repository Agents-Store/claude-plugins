# Connectors

## How tool references work

Plugin files use `~~capability` as a placeholder for whatever tool handles that action. For example, `~~search` means "use any available web search tool" — the agent tries providers in fallback order until one succeeds.

Plugins are **tool-agnostic** — they describe workflows in terms of actions (`~~search`, `~~scrape`, `~~crawl`) rather than specific tool names. The plugin ships no MCP server of its own: it uses whatever search and scrape servers are installed.

`web-search-dev` bundles Exa, Firecrawl, Jina and Perplexity, and is declared in this plugin's `dependencies`, so Claude Code installs it with this plugin. You can also bring any other server that provides these capabilities — the fallback chains below simply skip tools that are not in your tool list.

Tool names in the chains are the bare names (`read_url`, `firecrawl_scrape`). Servers installed through `web-search-dev` register them as `mcp__plugin_web-search-dev_<server>__<tool>` with the servers `jina`, `exa`, `firecrawl`, `perplexity`. Argument shapes and the full tool lists live in `web-search-dev` (`mcp-patterns` skill, `references/*-tools.md`) and in `docs/tool_reference.md`.

## FALLBACK Rule

Every action goes through ALL available providers for that category, one by one:
1. Try provider 1 — if it works, use the result
2. If error, empty result, rate limit, or timeout — try provider 2
3. If error — try provider 3
4. Continue until one succeeds or all are exhausted
5. Only report "not found" when ALL providers failed

**Error from a provider = skip it, try the next one. Never stop at first failure.**

A tool that is not in your tool list (a server not installed, an opt-in tool not enabled, a hosted tier without an API key) counts as an error — skip it silently and note it in Methodology.

## Connectors for this plugin

| Category | Placeholder | Fallback chain (live tools) | Other options |
|----------|-------------|-----------------------------|---------------|
| Web search | `~~search` | `web_search_exa` → `perplexity_search` → `search_web` (Jina) → `firecrawl_search` (`sources: ["web"]`) | Tavily, Brave Search, SerpAPI |
| Scrape / read page | `~~scrape` | `read_url` (Jina) → `firecrawl_scrape` → `web_fetch_exa` | Browserbase, Apify |
| Targeted read (only the relevant passages) | `~~scrape` with `question` | `read_url({url, question, topk})` → `firecrawl_scrape({formats: ["query"], queryOptions})` → full read, then pick passages yourself | — |
| Parallel search | `~~batch_search` | `search_web({query: [≤5 queries]})` → one `web_search_exa` call per query → one `perplexity_search` call per query | — |
| Parallel scrape | `~~batch_scrape` | `read_url({url: [≤5 URLs]})` → `web_fetch_exa({urls})` → one `firecrawl_scrape` call per URL | — |
| Crawl site | `~~crawl` | `firecrawl_crawl` → `firecrawl_map` + `~~batch_scrape` on the chosen URLs | — |
| Structured extraction | `~~extract` | `firecrawl_scrape({formats: ["json"], jsonOptions: {prompt, schema}})` per URL → `firecrawl_agent` (unknown URLs or several sites) → `~~scrape`, then extract the fields yourself | — |
| Academic papers | `~~academic_search` | `firecrawl_research_search_papers` (+ `firecrawl_research_read_paper`, `firecrawl_research_related_papers`) → `search_arxiv` / `search_ssrn` (Jina) → `perplexity_search` with `search_domain_filter` | Semantic Scholar |
| Code search | `~~code_search` | `firecrawl_developer_search` → `web_search_advanced_exa` with `includeDomains` (opt-in) → `~~search` + "github" | — |
| Deep agent (heavy tier) | `~~deep_agent` | `agent_run` (Exa, needs API key or OAuth) → `firecrawl_agent` + `firecrawl_agent_status` → `perplexity_research` | — |

### Notes on the chains

- **`~~batch_search` / `~~batch_scrape`** — Jina takes up to 5 queries in `query` and up to 5 URLs in `url`; every item runs concurrently in one call. `search_arxiv` and `search_ssrn` take the same array.
- **Targeted read** — `read_url` with `question` (and `topk`, default 1) returns only the passages that answer it. It costs a fraction of a full page read. Use it for READ by default; read a page in full only for exact quotes, tables, or when the passages are not enough.
- **`~~extract`** — `firecrawl_scrape` takes plain-string `formats` (`["json"]`); the schema goes in `jsonOptions`. One call per URL. For URLs you do not know yet, or data spread across several sites, `firecrawl_agent` returns a job id — poll `firecrawl_agent_status` every 15–30 seconds until `completed` or `failed`, and set `maxCredits`.
- **`~~academic_search`** — `firecrawl_research_search_papers` covers PubMed, bioRxiv, medRxiv and arXiv; `firecrawl_research_read_paper` returns the passages of one paper that answer a `question`; `firecrawl_research_related_papers` walks the citation graph (`mode`: `similar`, `citers`, `references`). Jina covers arXiv and SSRN as the next step.
- **`~~code_search`** — `firecrawl_developer_search` searches repositories, GitHub issues, merged PRs, READMEs and docs; `skills: "only"` limits it to agent-skill files. Exa has no code-search tool; `web_search_advanced_exa` is opt-in.
- **`~~deep_agent`** — runs for minutes and spends credits. Use it only for depth `deep`, as an extra pass next to the normal chain, never as the only source.
- **Perplexity** — `perplexity_search` takes `query`; `perplexity_ask`, `perplexity_reason` and `perplexity_research` take `messages` (`[{role, content}]`). They run on the Perplexity Agent API presets `fast`, `medium` and `high`.

## General workflow

```
Step 1: SEARCH — find pages on the internet
  → Use ~~search on every available provider, one by one
  → First success = take the URLs
  → Provider error = skip, next provider

Step 2: SCRAPE — read the found pages
  → Use ~~scrape on every available provider, one by one
  → First success = take the content
  → Provider error = skip, next provider
```

This same pattern applies to every capability: crawl, extract, academic_search, code_search, deep_agent.

## Utility tools (unique per provider, no fallback)

| Category | Tool | Provider |
|----------|------|----------|
| Relevance ranking | `sort_by_relevance` | Jina |
| Deduplication (text) | `deduplicate_strings` | Jina |
| PDF figures, tables, equations | `extract_pdf` | Jina |
| Screenshots | `capture_screenshot_url` (pass `return_url: true`) | Jina |
| Page date detection | `guess_datetime_url` | Jina |
| Image search | `search_images` (pass `return_url: true`) | Jina |
| Current time and location | `primer` | Jina |
| Site URL map | `firecrawl_map` | Firecrawl |
| Browser automation | `firecrawl_interact`, `firecrawl_interact_stop` | Firecrawl |

There are no tools for query expansion, text classification or BibTeX search: planning queries and classifying content are steps the model performs itself.

## Where the tools come from

| Server | Provided by | Capabilities |
|--------|-------------|--------------|
| Exa | `web-search-dev` | search, scrape, deep agent (`agent_run`, opt-in/OAuth), advanced search (opt-in) |
| Perplexity | `web-search-dev` | search, AI answers with citations, deep research |
| Jina | `web-search-dev` | search, scrape, batch search, batch scrape, arXiv/SSRN, utilities |
| Firecrawl | `web-search-dev` | search, scrape, crawl, extract, agent, interact, developer search, paper research |
