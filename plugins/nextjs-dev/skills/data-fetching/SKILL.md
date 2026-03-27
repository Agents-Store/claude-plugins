---
name: data-fetching
description: Next.js data fetching, caching, and mutation patterns. This skill should be used when the user asks about "data fetching in Next.js", "Server Actions", "server-side data fetching", "caching strategies", "'use cache' directive", "revalidation", "ISR", "streaming with Suspense", "fetch in Server Components", or needs guidance on how to load and mutate data in Next.js App Router.
---

# Data Fetching, Caching & Mutations

Next.js App Router provides multiple approaches to fetch, cache, and mutate data. Server Components fetch data on the server by default. Server Actions handle mutations. The `use cache` directive (Next.js 16+) provides fine-grained caching control.

## Server Component Data Fetching

Fetch data directly in async Server Components. No `useEffect` or `getServerSideProps` needed:

```tsx
// app/posts/page.tsx — Server Component
export default async function PostsPage() {
  const posts = await db.post.findMany()

  return (
    <ul>
      {posts.map(post => (
        <li key={post.id}>{post.title}</li>
      ))}
    </ul>
  )
}
```

With the `fetch` API:

```tsx
export default async function Page() {
  const res = await fetch('https://api.example.com/posts')
  const posts = await res.json()
  return <PostList posts={posts} />
}
```

## Parallel vs Sequential Data Fetching

**Sequential** — requests run one after another (default when awaited inline):

```tsx
export default async function Page() {
  const user = await getUser()       // Waits for this...
  const posts = await getPosts(user.id)  // ...then this
  return <Profile user={user} posts={posts} />
}
```

**Parallel** — initiate all requests simultaneously with `Promise.all`:

```tsx
export default async function Page() {
  const [user, posts, comments] = await Promise.all([
    getUser(),
    getPosts(),
    getComments(),
  ])
  return <Dashboard user={user} posts={posts} comments={comments} />
}
```

Prefer parallel fetching when requests are independent. This reduces total loading time.

## Streaming with Suspense

Stream parts of the page as they become ready using `<Suspense>`:

```tsx
import { Suspense } from 'react'

export default function Page() {
  return (
    <div>
      <h1>Dashboard</h1>
      <Suspense fallback={<p>Loading analytics...</p>}>
        <Analytics />  {/* Streams in when ready */}
      </Suspense>
      <Suspense fallback={<p>Loading feed...</p>}>
        <ActivityFeed />  {/* Streams independently */}
      </Suspense>
    </div>
  )
}
```

Alternatively, use `loading.tsx` for route-level loading states (automatically wraps the page in `<Suspense>`).

Use the `use` API to stream data from Server to Client Components:

```tsx
// app/page.tsx — Server Component
import { Posts } from './posts'

export default function Page() {
  const postsPromise = getPosts()  // Start fetch, don't await
  return <Posts postsPromise={postsPromise} />
}
```

```tsx
// app/posts.tsx — Client Component
'use client'

import { use } from 'react'

export function Posts({ postsPromise }: { postsPromise: Promise<Post[]> }) {
  const posts = use(postsPromise)  // Suspends until resolved
  return <ul>{posts.map(p => <li key={p.id}>{p.title}</li>)}</ul>
}
```

## Server Actions & Mutations

Define server-side mutations with `'use server'`:

```tsx
// app/actions.ts
'use server'

import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'

export async function createPost(formData: FormData) {
  const title = formData.get('title') as string
  const content = formData.get('content') as string

  await db.post.create({ data: { title, content } })

  revalidatePath('/posts')
  redirect('/posts')
}
```

Use in forms (progressive enhancement — works without JavaScript):

```tsx
// app/posts/new/page.tsx
import { createPost } from '../actions'

export default function NewPostPage() {
  return (
    <form action={createPost}>
      <input name="title" required />
      <textarea name="content" required />
      <button type="submit">Create Post</button>
    </form>
  )
}
```

Use in Client Components for programmatic mutations:

```tsx
'use client'

import { createPost } from '../actions'
import { useActionState } from 'react'

export function CreatePostForm() {
  const [state, formAction, pending] = useActionState(createPost, null)

  return (
    <form action={formAction}>
      <input name="title" required />
      <button type="submit" disabled={pending}>
        {pending ? 'Creating...' : 'Create'}
      </button>
    </form>
  )
}
```

## Revalidation Strategies

### Path-based Revalidation

Invalidate all cached data for a specific route:

```tsx
'use server'
import { revalidatePath } from 'next/cache'

export async function updatePost(id: string, data: FormData) {
  await db.post.update({ where: { id }, data: { /* ... */ } })
  revalidatePath('/posts')         // Revalidate the list
  revalidatePath(`/posts/${id}`)   // Revalidate the specific page
}
```

### Tag-based Revalidation

Revalidate specific data across multiple routes:

```tsx
// Fetch with a tag
const posts = await fetch('https://api.example.com/posts', {
  next: { tags: ['posts'] },
})

// Later, revalidate by tag
'use server'
import { revalidateTag } from 'next/cache'

export async function refreshPosts() {
  revalidateTag('posts')
}
```

### Time-based Revalidation (ISR)

Automatically regenerate pages at a set interval:

```tsx
// app/posts/page.tsx
export const revalidate = 60  // Revalidate every 60 seconds

export default async function PostsPage() {
  const posts = await getPosts()
  return <PostList posts={posts} />
}
```

## `use cache` Directive (Next.js 16+)

Cache Components let you cache at the function or component level:

### Data-level Caching

```tsx
'use cache'

export async function getUser(id: string) {
  const user = await db.user.findUnique({ where: { id } })
  return user
}
```

### Component-level Caching

```tsx
'use cache'

export default async function UserProfile({ id }: { id: string }) {
  const user = await db.user.findUnique({ where: { id } })
  return <div>{user.name}</div>
}
```

### Cache with Lifetime

```tsx
import { cacheLife } from 'next/cache'

export async function getProducts() {
  'use cache'
  cacheLife('hours')
  const products = await db.product.findMany()
  return products
}
```

Cache lifetime profiles: `'default'`, `'seconds'`, `'minutes'`, `'hours'`, `'days'`, `'weeks'`, `'max'`.

### Cache with Tags

```tsx
import { cacheTag } from 'next/cache'

export async function getPost(id: string) {
  'use cache'
  cacheTag(`post-${id}`, 'posts')
  const post = await db.post.findUnique({ where: { id } })
  return post
}
```

## Request Memoization

React automatically memoizes `fetch` calls with the same URL and options during a single render pass. For non-fetch functions, use `React.cache`:

```tsx
import { cache } from 'react'

export const getUser = cache(async (id: string) => {
  const user = await db.user.findUnique({ where: { id } })
  return user
})
```

Now multiple components calling `getUser('123')` in the same request only execute the query once.

## Rendering Strategy Summary

| Strategy | When | How |
|----------|------|-----|
| Static (SSG) | Content rarely changes | Default for pages without dynamic data |
| ISR | Semi-dynamic content | `export const revalidate = 60` |
| Dynamic (SSR) | Per-request data | Use `cookies()`, `headers()`, or `searchParams` |
| Streaming | Progressive loading | `<Suspense>` boundaries or `loading.tsx` |
| `use cache` (16+) | Fine-grained cache control | `'use cache'` + `cacheLife()` + `cacheTag()` |
