---
description: Full SEO optimization — audit, fix, and enhance SEO across Next.js and Directus
argument-hint: [--skip-directus] [--skip-build] [--report-only]
---

# SEO Optimize

End-to-end SEO optimization for a Directus + Next.js project. Audits the current state, implements all fixes, extends Directus schema with SEO fields, and produces a final report.

## Arguments

- `--skip-directus` (optional) — Skip Directus schema changes and field population
- `--skip-build` (optional) — Skip the final `pnpm build` verification
- `--report-only` (optional) — Audit only, do not make changes. Show what needs fixing

## Skills Used

This command orchestrates all seo-dev skills plus Directus MCP tools:

| Skill | Used In |
|-------|---------|
| `seo-dev:setup` | Phase 1: Audit foundations |
| `seo-dev:meta-tags` | Phase 2: Metadata & OG |
| `seo-dev:structured-data` | Phase 3: JSON-LD |
| `seo-dev:sitemap-robots` | Phase 4: Sitemap & Robots |
| `seo-dev:performance` | Phase 5: Core Web Vitals |
| `seo-dev:technical-seo` | Phase 6: Technical SEO |
| `seo-dev:content-seo` | Phase 7: Content optimization |
| `seo-dev:audit` | Phase 1 & Phase 8: Audit & Report |
| `directus-dev:schema-design` | Phase 3D: Directus SEO fields |
| `directus-dev:field-relations` | Phase 3D: Field creation |
| `stack-directus-nextjs-dev:directus-to-nextjs` | Phase 3D: Data fetching |

## Process

### Phase 1: SEO Audit (read-only)

Scan the entire project to understand the current SEO state. Do NOT make changes yet — collect findings first.

#### 1a. Project Structure Discovery

```bash
# Find the app directory
ls -d src/app 2>/dev/null || ls -d app 2>/dev/null

# Identify all page routes
find src/app -name "page.tsx" -o -name "page.ts" 2>/dev/null || find app -name "page.tsx" -o -name "page.ts" 2>/dev/null

# Find root layout
find src/app -name "layout.tsx" -maxdepth 1 2>/dev/null || find app -name "layout.tsx" -maxdepth 1 2>/dev/null
```

#### 1b. Metadata Audit

Check every page and layout for metadata:

```bash
# Pages with metadata
grep -rl "export const metadata\|export async function generateMetadata" src/app --include="*.tsx" --include="*.ts"

# Pages WITHOUT metadata (these need fixing)
find src/app -name "page.tsx" | while read f; do
  grep -qE "metadata|generateMetadata" "$f" || echo "MISSING: $f"
done

# Check metadataBase
grep -r "metadataBase" src/app/layout.tsx

# Check title template
grep -r "template:" src/app/layout.tsx

# Check NEXT_PUBLIC_SITE_URL
grep "NEXT_PUBLIC_SITE_URL" .env .env.local 2>/dev/null
```

#### 1c. Sitemap & Robots Audit

```bash
ls src/app/sitemap.ts src/app/robots.ts 2>/dev/null
```

#### 1d. Structured Data Audit

```bash
# Check for existing JSON-LD
grep -rl "application/ld+json" src/ --include="*.tsx" --include="*.ts"

# Check for schema-dts
grep "schema-dts" package.json

# Check for JsonLd component
grep -rl "JsonLd" src/components/ --include="*.tsx" 2>/dev/null
```

#### 1e. Images Audit

```bash
# Images without alt text
grep -rn "<Image\|<img" src/ --include="*.tsx" | grep -v "alt=" | head -30

# Images without sizes prop
grep -rn "<Image" src/ --include="*.tsx" | grep -v "sizes=" | head -20

# Images with priority prop (should be only LCP images)
grep -rn "priority" src/ --include="*.tsx" | grep "<Image\|Image " | head -10

# Check next.config for image formats
grep -A5 "images:" next.config.ts 2>/dev/null || grep -A5 "images:" next.config.js 2>/dev/null
```

#### 1f. Heading Hierarchy Audit

```bash
# Count H1 tags per page
find src/app -name "page.tsx" | while read f; do
  count=$(grep -c "<h1\|<H1" "$f" 2>/dev/null || echo "0")
  [ "$count" != "1" ] && echo "H1 count=$count: $f"
done
```

#### 1g. Directus Schema Audit (skip if --skip-directus)

Use Directus MCP tools to check existing collections for SEO fields:

For each content collection (blog posts, pages, products, etc.):

1. Call `schema` tool with `keys: ["<collection>"]` to list all fields
2. Check if these SEO fields exist:
   - `meta_title` (string, input)
   - `meta_description` (text, textarea)
   - `og_image` (file, single image)
   - `slug` (string, input — may already exist)
   - `canonical_url` (string, input)
3. Record which collections need SEO fields added

#### 1h. Compile Audit Report

Present findings in this format before proceeding:

```
## SEO Audit Results

### Foundations
- [ ] metadataBase: [present/missing]
- [ ] Title template: [present/missing]
- [ ] NEXT_PUBLIC_SITE_URL: [present/missing]
- [ ] sitemap.ts: [present/missing]
- [ ] robots.ts: [present/missing]
- [ ] schema-dts: [installed/missing]

### Pages (X total)
- Pages with metadata: X/Y
- Pages without metadata: [list]
- Pages missing canonical: [list]

### Structured Data
- JSON-LD present: [yes/no]
- Organization schema: [yes/no]
- WebSite schema: [yes/no]
- Page-specific schemas: [list]

### Images
- Images without alt: X
- Images without sizes: X
- LCP images without priority: X

### Headings
- Pages with wrong H1 count: [list]

### Directus
- Collections needing SEO fields: [list]
- Collections with SEO fields: [list]

### Estimated changes: X files to create/modify
```

**If --report-only**: stop here, show the report, and exit.

Ask the user to confirm before proceeding with changes.

### Phase 2: SEO Foundations

Apply `seo-dev:setup` patterns.

#### 2a. Install schema-dts

```bash
pnpm add -D schema-dts
```

#### 2b. Set NEXT_PUBLIC_SITE_URL

If missing from `.env` / `.env.local`, add it:
```
NEXT_PUBLIC_SITE_URL=https://yourdomain.com
```

Ask the user for their production domain if not already set.

#### 2c. Configure Root Layout Metadata

Read the current root layout. Add or update:

```tsx
import type { Metadata } from 'next'

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'),
  title: {
    template: '%s | Site Name',
    default: 'Site Name',
  },
  description: 'Site description',
  openGraph: {
    type: 'website',
    siteName: 'Site Name',
    locale: 'en_US',
  },
  twitter: {
    card: 'summary_large_image',
  },
}
```

Preserve any existing metadata fields. Merge, do not replace.

#### 2d. Create robots.ts (if missing)

Apply `seo-dev:sitemap-robots` pattern with environment-aware blocking and AI crawler rules.

#### 2e. Create sitemap.ts (if missing)

Apply `seo-dev:sitemap-robots` dynamic pattern. Fetch pages from Directus:

```tsx
import type { MetadataRoute } from 'next'
import directus from '@/lib/directus'
import { readItems } from '@directus/sdk'

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://yourdomain.com'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  // Static pages
  const staticPages: MetadataRoute.Sitemap = [
    { url: BASE_URL, lastModified: new Date(), changeFrequency: 'daily', priority: 1 },
  ]

  // Dynamic pages from Directus
  // Adapt collection names and slugs to the actual project
  try {
    const posts = await directus.request(
      readItems('posts', {
        fields: ['slug', 'date_updated'],
        filter: { status: { _eq: 'published' } },
      })
    )

    const postEntries: MetadataRoute.Sitemap = posts.map((post) => ({
      url: `${BASE_URL}/blog/${post.slug}`,
      lastModified: post.date_updated ? new Date(post.date_updated) : new Date(),
      changeFrequency: 'weekly' as const,
      priority: 0.7,
    }))

    return [...staticPages, ...postEntries]
  } catch {
    return staticPages
  }
}
```

Adapt collection names (`posts`, `pages`, `products`) to match the actual project schema discovered in Phase 1.

### Phase 3: Structured Data

Apply `seo-dev:structured-data` patterns.

#### 3a. Create JsonLd Component

```tsx
// components/json-ld.tsx
import type { Thing, WithContext } from 'schema-dts'

export function JsonLd<T extends Thing>({ data }: { data: WithContext<T> }) {
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{
        __html: JSON.stringify(data).replace(/</g, '\\u003c'),
      }}
    />
  )
}
```

#### 3b. Create Schema Factory Functions

Create `lib/schema.ts` with factory functions from the `seo-dev:structured-data` skill:
- `createOrganization`
- `createWebSite`
- `createBreadcrumbList`
- `createArticle` (if blog/news exists)
- `createProduct` (if e-commerce exists)

#### 3c. Add Sitewide Schemas to Root Layout

Add `<JsonLd>` for Organization and WebSite to the root layout `<body>`.

#### 3d. Add Page-Specific Schemas

For each content page type discovered in Phase 1:
- Blog posts → Article schema
- Product pages → Product schema
- All inner pages → BreadcrumbList schema

### Phase 3D: Directus SEO Fields (skip if --skip-directus)

For each content collection that lacks SEO fields:

1. **Add fields via MCP** — Call the Directus `fields` tool:

   ```
   Tool: fields
   Input: {
     "action": "create",
     "collection": "<collection_name>",
     "field": "meta_title",
     "type": "string",
     "meta": {
       "interface": "input",
       "display": "raw",
       "note": "SEO title for search engines (50-60 chars). Falls back to main title if empty.",
       "options": { "trim": true },
       "group": null,
       "sort": 100,
       "width": "half"
     }
   }
   ```

   Repeat for each field:

   | Field | Type | Interface | Width | Note |
   |-------|------|-----------|-------|------|
   | `meta_title` | string | input | half | SEO title (50-60 chars) |
   | `meta_description` | text | textarea | full | SEO description (150-160 chars) |
   | `og_image` | uuid | file-image | half | Open Graph image (1200x630) |
   | `canonical_url` | string | input | half | Custom canonical URL (optional) |

   Only create fields that do not already exist. Skip `slug` if the collection already has one.

2. **Auto-populate SEO fields** for existing items that have empty SEO fields:

   - Read all items with empty `meta_title`
   - For each, derive `meta_title` from the item's main title field (truncate to 60 chars)
   - Derive `meta_description` from the item's content/description field (truncate to 160 chars)
   - Call `items` tool with `action: "update"` to save

3. **Update Next.js data fetching** to include SEO fields in `readItems` calls:

   ```tsx
   const post = await directus.request(
     readItems('posts', {
       fields: ['*', 'meta_title', 'meta_description', 'og_image', 'canonical_url'],
       filter: { slug: { _eq: slug } },
       limit: 1,
     })
   )
   ```

4. **Update generateMetadata** on dynamic pages to use Directus SEO fields:

   ```tsx
   export async function generateMetadata({ params }: Props): Promise<Metadata> {
     const { slug } = await params
     const post = await getPost(slug)

     return {
       title: post.meta_title || post.title,
       description: post.meta_description || post.excerpt,
       openGraph: {
         title: post.meta_title || post.title,
         description: post.meta_description || post.excerpt,
         images: post.og_image
           ? [{ url: getDirectusAssetUrl(post.og_image), width: 1200, height: 630 }]
           : undefined,
       },
       alternates: {
         canonical: post.canonical_url || `/blog/${slug}`,
       },
     }
   }
   ```

### Phase 4: Meta Tags & OG Images

Apply `seo-dev:meta-tags` patterns.

For every page discovered in Phase 1 that lacks metadata:

1. **Static pages** (about, contact, etc.) — Add `export const metadata: Metadata` with title, description, OG tags, canonical
2. **Dynamic pages** (blog/[slug], products/[slug]) — Add `generateMetadata` function using Directus SEO fields
3. **Add OG image defaults** — Either static images or `opengraph-image.tsx` for dynamic generation

### Phase 5: Content Optimization

Apply `seo-dev:content-seo` patterns.

1. **Fix heading hierarchy** — Ensure single H1 per page, logical H2-H6 nesting
2. **Fix image alt texts** — Add descriptive alt text to all `<Image>` components missing it
3. **Add sizes prop** — Add responsive `sizes` attribute to all `<Image>` components
4. **Mark LCP images** — Add `priority` prop to above-the-fold hero/banner images (one per page max)
5. **Create Breadcrumbs component** — If inner pages lack breadcrumbs, create a reusable component with BreadcrumbList schema

### Phase 6: Performance & Technical SEO

Apply `seo-dev:performance` and `seo-dev:technical-seo` patterns.

#### 6a. next.config.ts Updates

Add security headers and image format optimization:

```ts
// Add to next.config.ts
const nextConfig = {
  images: {
    formats: ['image/avif', 'image/webp'],
    // Keep existing remotePatterns
  },
  async headers() {
    return [{
      source: '/(.*)',
      headers: [
        { key: 'X-Content-Type-Options', value: 'nosniff' },
        { key: 'X-Frame-Options', value: 'DENY' },
        { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
        { key: 'X-XSS-Protection', value: '1; mode=block' },
      ],
    }]
  },
}
```

Merge with existing config — do not overwrite.

#### 6b. Verify next/font Usage

Check that `next/font` is used in root layout (not external font links). If using Google Fonts via `<link>`, migrate to `next/font/google`.

#### 6c. Check Lazy Loading

Verify non-critical components use `dynamic()` imports where appropriate.

### Phase 7: Build Verification (skip if --skip-build)

```bash
pnpm build
```

Check for:
- Metadata-related build errors
- TypeScript errors in new/modified files
- Sitemap/robots generation warnings

If build fails, fix the errors and retry.

### Phase 8: Final Report

Present the complete report:

```
## SEO Optimization Report

### Before → After Summary

| Category | Before | After |
|----------|--------|-------|
| Pages with metadata | X/Y | Y/Y |
| Pages with canonical | X/Y | Y/Y |
| Structured data schemas | X | Y |
| Images with alt text | X/Y | Y/Y |
| Images with sizes | X/Y | Y/Y |
| sitemap.ts | missing/present | present |
| robots.ts | missing/present | present |
| schema-dts | missing/installed | installed |
| metadataBase | missing/set | set |
| Security headers | missing/set | set |
| AVIF/WebP | disabled/enabled | enabled |

### Files Created
- [list of new files]

### Files Modified
- [list of modified files with brief description of changes]

### Directus Changes (if applied)
- Collections updated: [list]
- SEO fields added: [list]
- Items auto-populated: X items

### Remaining Manual Tasks
- [ ] Set NEXT_PUBLIC_SITE_URL to production domain
- [ ] Submit sitemap in Google Search Console
- [ ] Add Google Search Console verification code
- [ ] Create custom OG images for key pages
- [ ] Review auto-generated meta_description values in Directus
- [ ] Test with Google Rich Results Test after deployment

### Build Status
- [PASS/FAIL] — pnpm build

### Next Steps
1. Deploy and test with PageSpeed Insights
2. Submit sitemap to Google Search Console
3. Verify rich results after 2-4 weeks
4. Run /seo-dev:optimize again after adding new content
```

## Example

Input: `/seo-dev:optimize`

Output: Runs full audit → shows report → asks for confirmation → implements all changes → shows final report.

Input: `/seo-dev:optimize --report-only`

Output: Runs full audit → shows report → exits without changes.

Input: `/seo-dev:optimize --skip-directus`

Output: Runs full optimization on Next.js side only, does not touch Directus schema or content.
