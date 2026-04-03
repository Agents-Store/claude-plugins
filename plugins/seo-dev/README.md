# seo-dev

SEO development plugin for Agents Store. Knowledge base for implementing technical SEO, structured data, metadata, Core Web Vitals optimization, and content SEO in Next.js App Router projects.

**Type:** Technology (dev)

## Skills

| Skill | Description |
|-------|-------------|
| `setup` | SEO audit and initial setup — metadataBase, robots.ts, sitemap.ts, schema-dts |
| `meta-tags` | Next.js Metadata API, Open Graph, Twitter Cards, OG image generation |
| `structured-data` | Schema.org JSON-LD implementation with schema-dts type safety |
| `sitemap-robots` | Sitemap generation, robots.txt, AI crawler management |
| `performance` | Core Web Vitals (LCP, INP, CLS), next/image, next/font optimization |
| `technical-seo` | Crawlability, indexability, redirects, hreflang, security headers |
| `content-seo` | Heading hierarchy, image SEO, internal linking, URL structure |
| `audit` | SEO audit checklist, automated Playwright tests, Lighthouse CI |
| `troubleshoot` | Diagnostic trees for common SEO problems |
| `examples` | Complete SEO recipes for blog, e-commerce, landing page, SaaS |

## Agent

| Agent | Description |
|-------|-------------|
| `seo-specialist` | SEO specialist for auditing, implementing, and troubleshooting SEO |

## Prerequisites

- Next.js 15+ with App Router
- TypeScript

## Installation

Add `seo-dev` to your Claude Code settings:

```json
{
  "enabledPlugins": ["seo-dev"]
}
```

## Key Dependencies

- `schema-dts` (dev dependency) — TypeScript types for Schema.org structured data (zero bundle impact)

No other SEO packages needed — Next.js Metadata API replaces `next-seo` entirely.

## What This Plugin Covers

- Next.js Metadata API (static, dynamic, file-based conventions)
- Structured data (JSON-LD) for all common schema types
- Core Web Vitals optimization (LCP, INP, CLS)
- Sitemap and robots.txt generation
- Open Graph and Twitter Card configuration
- Dynamic OG image generation
- International SEO (hreflang)
- SEO auditing and automated testing
- Content optimization (headings, images, linking)

## What This Plugin Does NOT Cover

- Google Ads / paid search
- Google Analytics setup (see vercel-dev plugin)
- Content writing / copywriting
- Backlink building strategy
- Local SEO for physical businesses (covered in structured-data examples only)
