---
description: Search GitHub repos and community platforms for n8n workflows
allowed-tools: ["Bash", "Read", "Grep"]
argument-hint: <query> [--source <github|community|all>]
---

# Search Community

Search GitHub repositories and community platforms for n8n workflows not in the official template library.

## Arguments
Format: `<query> [--source <github|community|all>]`
- query: Search text (required)
- --source: Where to search — github (repos only), community (platforms only), all (default)

Parse from "$ARGUMENTS".

## Process

1. **Search GitHub repos** (if source is github or all):
   - Use `~~search` with queries targeting known repos: `"<query> n8n workflow site:github.com"`
   - Target high-value repos: Zie619/n8n-workflows, enescingoz/awesome-n8n-templates, Danitilahun/n8n-workflow-templates
   - See `community-source-discovery` skill and `references/GITHUB_SOURCES.md` for repo details

2. **Search community platforms** (if source is community or all):
   - Use `~~search` with queries targeting known platforms: `"<query> n8n workflow site:n8nworkflows.xyz OR site:n8nfind.net"`
   - See `references/COMMUNITY_PLATFORMS.md` for platform details

3. **Display results:**
   - Source (GitHub repo or platform name), title, URL, description
   - Quality indicators: stars (for repos), freshness
   - Note if raw JSON is directly available or needs scraping

4. **Suggest next steps:**
   - "Use `/n8n-provision:analyze-workflow <url>` to analyze a found workflow"
   - "Official templates may also have what you need — try `/n8n-provision:search-templates`"

## Example Usage
```
/n8n-provision:search-community "notion google sheets sync"
/n8n-provision:search-community "AI agent" --source github
/n8n-provision:search-community "CRM pipeline" --source all
```
