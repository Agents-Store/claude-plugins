---
name: payload-to-nextjs
description: This skill should be used when the user asks to "fetch Payload data in a server component", "show CMS content on a Next.js page", "revalidate pages when Payload content changes", "cache Payload queries", or wires any read path from Payload collections to the Next.js frontend.
---

# Payload → Next.js Data Flow

Wire every read path from Payload to the frontend through the **Local API** — direct in-process function calls, never `fetch` to your own REST API. This skill covers the query layer, page consumption, and the caching/revalidation bridge that keeps the frontend in sync with admin-panel edits.

## The Read Pipeline

```
RSC page / generateMetadata
      │  calls
lib/queries/<domain>.ts  ──  (payload, args) => typed DTOs
      │  uses
payload.find / findByID / findGlobal   (Local API, in-process)
      │  invalidated by
revalidatePath / revalidateTag  ←  Server Actions AND Payload afterChange hooks
```

## The Query Layer (`src/lib/queries/`)

Do not scatter `payload.find()` calls across pages. Centralize reads in helper functions that accept the `payload` instance and return typed row DTOs:

```ts
import type { Payload, Where } from 'payload'

export interface TaskRow { id: number; title: string; points: number; isActive: boolean }

export const listTaskTemplates = async (payload: Payload, companyId: number | null): Promise<TaskRow[]> => {
  const where: Where = companyId ? { company: { equals: companyId } } : {}
  const res = await payload.find({
    collection: 'tasks',
    where,
    limit: 200,
    depth: 0,          // IDs only — resolve relations explicitly when needed
    sort: '-createdAt',
  })
  return res.docs.map((t) => ({
    id: t.id, title: t.title ?? '', points: t.points ?? 0, isActive: Boolean(t.is_active),
  }))
}
```

Why this shape:

- **`depth: 0` by default** — the global default is 2, which populates every relationship two levels deep and bloats both the query and the payload passed to client components. Raise depth (or use `populate`) deliberately, per query.
- **Map to DTOs at the boundary** — pages and client components receive exactly the fields they render; schema changes surface as type errors in one file, and no unserializable or sensitive fields cross the RSC → client boundary.
- **Helpers take `payload` as an argument** — the same helper serves pages, actions, jobs, and integration tests.

Useful options on hot paths: `select: { title: true, points: true }` (DB-level projection), `pagination: false` with `limit: 1` for unique lookups, `count()` for badges. When selecting an upload's `url`, also select `filename: true` — otherwise `url` is `null`.

## Consuming in Pages

```tsx
// src/app/(frontend)/tasks/page.tsx
import { getSession } from '@/lib/session'
import { listTaskTemplates } from '@/lib/queries/tasks'

export default async function TasksPage() {
  const { payload, user } = await getSession()
  if (!user) redirect('/login')
  const tasks = await listTaskTemplates(payload, resolveActorCompanyId(user))
  return <TaskTable rows={tasks} />
}
```

- `params`/`searchParams` are **Promises** in Next 15+ — `const { slug } = await params`.
- Dedupe within one render pass with React `cache()` — wrap a query helper so page + `generateMetadata` hit the DB once.
- For user-scoped reads that must respect permissions, pass `overrideAccess: false, user` — access functions then row-filter results (see `auth-and-access`).

## Caching and Revalidation

Local API calls are plain async DB work — Next.js does **not** cache them by default (Next 15+ uncached-by-default model). Pages doing per-user reads should simply stay dynamic. Cache the shareable, content-shaped reads:

```ts
import { unstable_cache } from 'next/cache'

export const getPublishedPosts = unstable_cache(
  async () => {
    const payload = await getPayload({ config })
    const res = await payload.find({ collection: 'posts', where: { _status: { equals: 'published' } }, depth: 0 })
    return res.docs.map(toPostCard)
  },
  ['published-posts'],
  { tags: ['posts'], revalidate: 3600 },
)
```

On Next 16 with Cache Components enabled, the same helper uses `'use cache'` + `cacheTag('posts')` + `cacheLife('hours')` instead of `unstable_cache`.

### The Admin-Edit Bridge (the key integration)

`revalidatePath` in your Server Actions only covers *your* writes. Content edited in the **admin panel** must invalidate the frontend too — do it with an `afterChange`/`afterDelete` hook on the collection:

```ts
import { revalidatePath, revalidateTag } from 'next/cache'
import type { CollectionAfterChangeHook } from 'payload'
import type { Post } from '@/payload-types'

export const revalidatePost: CollectionAfterChangeHook<Post> = ({ doc, previousDoc }) => {
  if (doc._status === 'published') {
    revalidatePath(`/posts/${doc.slug}`)
    revalidateTag('posts', 'max')          // Next 16: second arg required; Next 15: revalidateTag('posts')
  }
  if (previousDoc?._status === 'published' && doc._status !== 'published') {
    revalidatePath(`/posts/${previousDoc.slug}`)   // unpublish clears the old page
  }
  return doc
}
```

This works because Payload runs inside Next.js — the hook executes in the same runtime that owns the cache. It is the reason the embedded architecture needs no webhook round-trip for cache invalidation.

## Rendering Rich Text (Lexical)

Store rich text as Lexical JSON; render it in RSCs with the official converter:

```tsx
import { RichText } from '@payloadcms/richtext-lexical/react'

<RichText data={post.content} />
```

For custom blocks inside rich text, pass `converters` mapping block slugs to React components. Never `dangerouslySetInnerHTML` hand-rolled HTML — the converter escapes content and keeps custom blocks typed.

## Media URLs

Uploads resolve to `doc.url`. With Payload access control kept on (default), files proxy through `/api/media/file/...` and respect read access; with `disablePayloadAccessControl: true` on the storage adapter, URLs point straight at the bucket/CDN. Choose per collection: private documents keep the proxy, public site media goes direct.

## Static Generation

For content-shaped routes, combine:

```tsx
export async function generateStaticParams() {
  const payload = await getPayload({ config })
  const posts = await payload.find({ collection: 'posts', select: {}, limit: 100, pagination: false })
  return posts.docs.map(({ slug }) => ({ slug }))
}
```

Docker note: SSG at build time needs a reachable database. Either build with `next build --experimental-build-mode compile` (no DB needed; pages render at runtime) or mark Payload-reading segments `export const dynamic = 'force-dynamic'`.

## Checklist for Every New Read Path

1. Helper in `src/lib/queries/` with explicit `depth`, `select`, `sort`, DTO mapping.
2. Page/RSC calls the helper; no inline `payload.find` in JSX files.
3. Decide: per-user (stay dynamic) vs shared content (cache + tag).
4. If cached: `afterChange` hook on the source collection revalidates the tag/path.
5. Regenerate types after schema changes so DTO mapping type-checks.

Related: mutations and hooks → `backend-logic`; sessions in pages → `auth-and-access`; full recipe → `full-feature`.
