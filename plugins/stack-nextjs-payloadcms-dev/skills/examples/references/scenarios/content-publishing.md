# Scenario: Content Publishing with Revalidation

A marketing site: posts with drafts, scheduled publishing, statically generated pages that refresh the moment an editor publishes in the admin panel. The cache bridge between Payload and Next.js is the core of this scenario.

## 1. Collection — `src/collections/posts.ts`

```ts
import type { CollectionConfig } from 'payload'
import { slugifyTitle } from '@/hooks/slug'
import { revalidatePost } from '@/hooks/posts-revalidate'

export const Posts: CollectionConfig = {
  slug: 'posts',
  versions: { drafts: { autosave: true } },   // adds _status: 'draft' | 'published'
  admin: { useAsTitle: 'title', defaultColumns: ['title', 'slug', '_status', 'publishedAt'] },
  access: {
    read: ({ req }) => {
      if (req.user) return true                          // editors see drafts
      return { _status: { equals: 'published' } }        // guests: published only
    },
    create: ({ req }) => Boolean(req.user),
    update: ({ req }) => Boolean(req.user),
    delete: ({ req }) => Boolean(req.user),
  },
  hooks: { afterChange: [revalidatePost] },
  fields: [
    { name: 'title', type: 'text', required: true },
    { name: 'slug', type: 'text', unique: true, index: true,
      hooks: { beforeChange: [slugifyTitle] } },
    { name: 'content', type: 'richText' },
    { name: 'hero', type: 'upload', relationTo: 'media' },
    { name: 'publishedAt', type: 'date' },
  ],
}
```

Slug field hook (returns the field value — field hooks must not change the value's type):

```ts
import type { FieldHook } from 'payload'
import type { Post } from '@/payload-types'

export const slugifyTitle: FieldHook<Post, string | null | undefined, Post> = ({ value, siblingData }) => {
  if (!value && siblingData.title) {
    return siblingData.title.toLowerCase().replace(/[^\w\s-]/g, '').replace(/\s+/g, '-')
  }
  return value
}
```

## 2. The Cache Bridge — `src/hooks/posts-revalidate.ts`

Admin-panel edits must invalidate the frontend cache. Because Payload runs inside Next.js, a hook can call the cache APIs directly:

```ts
import { revalidatePath, revalidateTag } from 'next/cache'
import type { CollectionAfterChangeHook } from 'payload'
import type { Post } from '@/payload-types'

export const revalidatePost: CollectionAfterChangeHook<Post> = ({ doc, previousDoc }) => {
  if (doc._status === 'published') {
    revalidatePath(`/posts/${doc.slug}`)
    revalidateTag('posts', 'max')      // Next 16 signature; on Next 15: revalidateTag('posts')
  }
  if (previousDoc?._status === 'published' && doc._status !== 'published') {
    revalidatePath(`/posts/${previousDoc.slug}`)   // unpublish clears the stale page
    revalidateTag('posts', 'max')
  }
  return doc
}
```

Add a matching `afterDelete` hook so deletions also revalidate.

## 3. Cached Reads — `src/lib/queries/posts.ts`

```ts
import { unstable_cache } from 'next/cache'
import { getPayload } from 'payload'
import config from '@payload-config'

export const getPublishedPosts = unstable_cache(
  async () => {
    const payload = await getPayload({ config })
    const res = await payload.find({
      collection: 'posts',
      where: { _status: { equals: 'published' } },
      depth: 0, sort: '-publishedAt', limit: 50,
      select: { title: true, slug: true, publishedAt: true },
    })
    return res.docs.map((p) => ({ title: p.title, slug: p.slug, publishedAt: p.publishedAt }))
  },
  ['published-posts'],
  { tags: ['posts'] },
)
```

Next 16 + Cache Components variant: replace `unstable_cache` with `'use cache'` + `cacheTag('posts')` + `cacheLife('hours')` inside the helper.

## 4. Pages — `src/app/(frontend)/posts/`

```tsx
// [slug]/page.tsx
import { notFound } from 'next/navigation'
import { RichText } from '@payloadcms/richtext-lexical/react'
import { getPayload } from 'payload'
import config from '@payload-config'

export async function generateStaticParams() {
  const payload = await getPayload({ config })
  const posts = await payload.find({ collection: 'posts',
    where: { _status: { equals: 'published' } }, select: { slug: true }, limit: 100, pagination: false })
  return posts.docs.map(({ slug }) => ({ slug }))
}

export default async function PostPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params                             // params is a Promise in Next 15+
  const payload = await getPayload({ config })
  const res = await payload.find({ collection: 'posts',
    where: { slug: { equals: slug }, _status: { equals: 'published' } }, limit: 1, pagination: false })
  const post = res.docs[0]
  if (!post) notFound()
  return (
    <article>
      <h1>{post.title}</h1>
      <RichText data={post.content} />
    </article>
  )
}
```

The flow: `generateStaticParams` prerenders published slugs → editor publishes/edits → `revalidatePost` hook invalidates the path/tag → next request re-renders with fresh content. No webhooks, no polling — the hook runs in the same runtime that owns the cache.

## 5. Scheduled Publishing — `src/jobs/publish-post.ts`

One-time future work uses `waitUntil`, not a cron schedule:

```ts
import type { TaskConfig } from 'payload'

export const publishPost: TaskConfig<{ input: { postId: number }; output: { published: boolean } }> = {
  slug: 'publishPost',
  inputSchema: [{ name: 'postId', type: 'number', required: true }],
  outputSchema: [{ name: 'published', type: 'checkbox' }],
  handler: async ({ input, req }) => {
    await req.payload.update({ collection: 'posts', id: input.postId,
      data: { _status: 'published', publishedAt: new Date().toISOString() }, req })
    return { output: { published: true } }
  },
}
```

Queue it when an editor sets a future `publishedAt` (from an `afterChange` hook or an action):

```ts
await payload.jobs.queue({ task: 'publishPost', input: { postId: doc.id }, waitUntil: new Date(doc.publishedAt) })
```

Publishing via the task fires the collection's `afterChange` → `revalidatePost` → the page goes live at the scheduled moment. Ensure a runner drains the queue (`background-job` skill).

## 6. Verification

- Guest `find` returns only published posts (access constraint), editor sees drafts.
- Publish in admin → page content changes without redeploy.
- Unpublish → page 404s (revalidated + access-filtered).
- Scheduled post flips at `waitUntil` and revalidates.

## Adaptation Notes

Same pattern for products, docs, landing blocks: drafts + access constraint + revalidate hook + tagged cached queries. Swap `RichText` rendering for block-based layouts when using a blocks field.
