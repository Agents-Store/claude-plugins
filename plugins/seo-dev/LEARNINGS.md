# LEARNINGS.md

Accumulated fixes and discoveries for the `seo-dev` plugin. Append entries chronologically (newest first). Format:

```
## [DATE] — [skill-name]: Brief description

**Problem:** What went wrong
**Fix:** What was changed
**Root cause:** Why the original was wrong
**Severity:** Critical / Major / Minor
```

## 2026-10-03 — examples: CMS HTML reached dangerouslySetInnerHTML unsanitized

**Problem:** The blog post recipe rendered `post.content` with `dangerouslySetInnerHTML` as it came out of the CMS. HTML written by editors is untrusted input: one compromised editor account, or a pasted snippet, is stored XSS on every visitor of a page the SEO work is meant to bring traffic to.
**Fix:** The recipe sanitizes the HTML on the server with `sanitize-html` (allowing the headings, links and images a post needs, with `https`, `http` and `mailto` links only) and says that rendering Markdown with a renderer that escapes raw HTML is the alternative. Checked: `<script>`, `<iframe>`, `onerror` / `onclick` and `javascript:` links are removed and the rest of the markup survives. The `JsonLd` component keeps its `<` escape because its payload is JSON, not HTML.
**Root cause:** The recipe was written to show metadata and structured data, and the content line was filler that nobody read as a security surface.
**Severity:** Major

## 2026-10-03 — structured-data, meta-tags, performance, robots, audit: Rich-result and Next.js guidance had gone stale (1.1.0)

**Problem:** The plugin promised SERP features that no longer exist and taught Next.js behaviour that changed. The FAQ rich result stopped appearing on 2026-05-07, HowTo is removed on desktop and mobile, and the sitelinks search box under brand results ended on 2024-11-21, yet the guidance listed them with a CTR lift. `robots.ts` disallowed `/_next/`, which blocks the assets Google needs to render a page; `generateSitemaps` was shown building a sitemap index it does not build; `next-seo` was called deprecated although v7 is a JSON-LD component set; `priority` on `next/image` was taught instead of `loading="eager"` with `fetchPriority="high"`; `revalidateTag(tag)` ran with one argument; streaming metadata was described as applying everywhere, and when different images are LCP at different viewports both a preload and `loading="eager"` were suggested, which downloads both.
**Fix:** FAQ, HowTo and the search box are marked as harmless markup that earns no SERP feature, and the table follows the Search Gallery list of 2026-06-15; WebSite markup sits on the home page (site name, no `SearchAction`); `/_next/` is no longer disallowed; the sitemap index is a route handler recipe; `next-seo` v7 is an optional alternative; images use `loading="eager"` plus `fetchPriority="high"`, and `fetchPriority` alone when the LCP image differs per breakpoint; `revalidateTag(tag, 'max')`; streaming metadata is scoped to request-time rendered pages (prerendered pages with a non-dynamic `generateMetadata` keep metadata in the initial `<head>`), with `htmlLimitedBots` marked abbreviated and verification through the rendered DOM or `curl` as a social bot; the AI crawler table gains ClaudeBot, Claude-SearchBot, Claude-User, ChatGPT-User and Google-Extended; the Googlebot 2 MB limit is noted; the Twitter Card Validator and `X-XSS-Protection` are gone; the CI examples use `actions/checkout@v7`, `setup-node@v7` and Node 22. Version 1.0.0 -> 1.1.0 in `plugin.json` and the marketplace.
**Root cause:** The plugin was written once from the state of search and Next.js at that time and had no date on any claim, so every change upstream turned a recommendation into a mistake without a visible trace.
**Severity:** Major
