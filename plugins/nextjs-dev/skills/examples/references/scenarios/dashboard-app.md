# Scenario: Authenticated Dashboard App

Build a multi-page dashboard with authentication, nested layouts, streaming data, and Server Actions.

## Project Structure

```
app/
├── layout.tsx                 # Root layout (fonts, providers)
├── page.tsx                   # Public landing page
├── login/
│   └── page.tsx               # Login form
├── (dashboard)/
│   ├── layout.tsx             # Dashboard layout (sidebar, nav, auth check)
│   ├── page.tsx               # Dashboard home (overview cards)
│   ├── loading.tsx            # Skeleton for dashboard pages
│   ├── analytics/
│   │   ├── page.tsx           # Analytics with streaming charts
│   │   └── loading.tsx        # Chart skeletons
│   ├── users/
│   │   ├── page.tsx           # User list with search
│   │   ├── [id]/
│   │   │   └── page.tsx       # User detail
│   │   └── new/
│   │       └── page.tsx       # Create user form
│   └── settings/
│       └── page.tsx           # Account settings
├── api/
│   └── auth/
│       └── [...nextauth]/
│           └── route.ts       # NextAuth.js handlers
├── middleware.ts               # Auth middleware
└── lib/
    ├── auth.ts                # Auth config
    ├── db.ts                  # Database client
    └── actions/
        ├── users.ts           # User CRUD actions
        └── settings.ts        # Settings actions
```

## Step 1: Root Layout with Providers

```tsx
// app/layout.tsx
import { Inter } from 'next/font/google'
import { SessionProvider } from './providers'
import './globals.css'

const inter = Inter({ subsets: ['latin'], variable: '--font-sans' })

export const metadata = {
  title: { default: 'Dashboard', template: '%s | Dashboard' },
  description: 'Admin dashboard',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body>
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  )
}
```

```tsx
// app/providers.tsx
'use client'

import { SessionProvider as NextAuthProvider } from 'next-auth/react'

export function SessionProvider({ children }: { children: React.ReactNode }) {
  return <NextAuthProvider>{children}</NextAuthProvider>
}
```

## Step 2: Authentication Middleware

Middleware runs at the edge and provides the first layer of auth protection. It checks for a session cookie and redirects unauthenticated users before the page even starts rendering:

```ts
// middleware.ts — at project root, NOT inside app/
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  // Check both standard and secure cookie variants
  const sessionToken =
    request.cookies.get('next-auth.session-token') ||
    request.cookies.get('__Secure-next-auth.session-token')

  if (!sessionToken) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('callbackUrl', request.nextUrl.pathname)
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/(dashboard)/:path*'],
}
```

## Step 3: Dashboard Layout with Sidebar (Double-Layer Auth)

The layout performs a **secondary server-side auth check**. While middleware catches most unauthenticated requests at the edge, the layout check provides defense in depth — it verifies the session is valid (not just that a cookie exists) and gives access to the full session object for rendering user info:

```tsx
// app/(dashboard)/layout.tsx
import { getServerSession } from 'next-auth'
import { redirect } from 'next/navigation'
import { authOptions } from '@/lib/auth'
import { Sidebar } from '@/components/sidebar'
import { TopNav } from '@/components/top-nav'

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  // Second auth layer: verifies session validity, not just cookie existence
  const session = await getServerSession(authOptions)
  if (!session) redirect('/login')

  return (
    <div className="flex h-screen">
      <Sidebar user={session.user} />
      <div className="flex-1 flex flex-col">
        <TopNav user={session.user} />
        <main className="flex-1 overflow-auto p-6">{children}</main>
      </div>
    </div>
  )
}
```

## Step 4: Dashboard Home with Streaming

```tsx
// app/(dashboard)/page.tsx
import { Suspense } from 'react'
import { StatsCards } from '@/components/stats-cards'
import { RecentActivity } from '@/components/recent-activity'
import { CardsSkeleton, ActivitySkeleton } from '@/components/skeletons'

export const metadata = { title: 'Overview' }

export default function DashboardHome() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      <Suspense fallback={<CardsSkeleton />}>
        <StatsCards />
      </Suspense>

      <Suspense fallback={<ActivitySkeleton />}>
        <RecentActivity />
      </Suspense>
    </div>
  )
}
```

```tsx
// components/stats-cards.tsx — Server Component
import { getStats } from '@/lib/db'

export async function StatsCards() {
  const stats = await getStats()

  return (
    <div className="grid grid-cols-4 gap-4">
      {stats.map(stat => (
        <div key={stat.label} className="rounded-lg border p-4">
          <p className="text-sm text-gray-500">{stat.label}</p>
          <p className="text-2xl font-bold">{stat.value}</p>
          <p className={stat.change > 0 ? 'text-green-600' : 'text-red-600'}>
            {stat.change > 0 ? '+' : ''}{stat.change}%
          </p>
        </div>
      ))}
    </div>
  )
}
```

## Step 5: Users Page with Search

The search page demonstrates two important patterns: the **Suspense key pattern** (re-showing the fallback when search params change) and **debounced URL updates** (preventing excessive navigation on every keystroke):

```tsx
// app/(dashboard)/users/page.tsx
import { Suspense } from 'react'
import { SearchInput } from '@/components/search-input'
import { UserTable } from '@/components/user-table'
import { TableSkeleton } from '@/components/skeletons'

export const metadata = { title: 'Users' }

export default async function UsersPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; page?: string }>
}) {
  const { q, page } = await searchParams

  return (
    <div className="space-y-4">
      <div className="flex justify-between">
        <h1 className="text-2xl font-bold">Users</h1>
        <a href="/users/new" className="btn-primary">Add User</a>
      </div>

      <SearchInput defaultValue={q} />

      {/* key changes when params change → Suspense remounts → skeleton shows → fresh data streams */}
      <Suspense key={`${q}-${page}`} fallback={<TableSkeleton />}>
        <UserTable query={q} page={Number(page) || 1} />
      </Suspense>
    </div>
  )
}
```

```tsx
// components/search-input.tsx — Client Component with debounced URL updates
'use client'

import { useRouter, useSearchParams, usePathname } from 'next/navigation'
import { useDebouncedCallback } from 'use-debounce'

export function SearchInput({ defaultValue }: { defaultValue?: string }) {
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()

  // Debounce prevents a navigation on every keystroke — waits 300ms after typing stops
  const handleSearch = useDebouncedCallback((term: string) => {
    const params = new URLSearchParams(searchParams.toString())
    if (term) {
      params.set('q', term)
    } else {
      params.delete('q')
    }
    params.delete('page')  // Reset pagination on new search
    router.replace(`${pathname}?${params.toString()}`)
  }, 300)

  return (
    <input
      type="search"
      placeholder="Search users..."
      defaultValue={defaultValue}
      onChange={e => handleSearch(e.target.value)}
      className="w-full rounded-md border px-3 py-2"
    />
  )
}
```

## Step 6: Server Actions for CRUD

The Server Action validates with zod, returns user-friendly field errors, and handles the mutation. Note two critical patterns: `redirect()` is called **outside** try/catch (it throws `NEXT_REDIRECT` internally, which try/catch would swallow), and `.trim()` is used on string inputs to avoid whitespace-only submissions:

```tsx
// lib/actions/users.ts
'use server'

import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'
import { z } from 'zod'
import { db } from '@/lib/db'

const userSchema = z.object({
  name: z.string().trim().min(2, 'Name must be at least 2 characters').max(100, 'Name must be 100 characters or fewer'),
  email: z.string().trim().email('Please enter a valid email address'),
  role: z.enum(['admin', 'member', 'viewer'], { errorMap: () => ({ message: 'Please select a role' }) }),
})

export type UserActionState = { errors?: Record<string, string[]>; message?: string } | null

export async function createUser(prevState: UserActionState, formData: FormData): Promise<UserActionState> {
  const parsed = userSchema.safeParse(Object.fromEntries(formData))

  if (!parsed.success) {
    return { errors: parsed.error.flatten().fieldErrors }
  }

  try {
    await db.user.create({ data: parsed.data })
  } catch (error) {
    return { message: 'Failed to create user. Please try again.' }
  }

  // IMPORTANT: redirect() throws NEXT_REDIRECT — keep it outside try/catch
  revalidatePath('/users')
  redirect('/users')
}

export async function deleteUser(id: string) {
  await db.user.delete({ where: { id } })
  revalidatePath('/users')
}
```

## Step 7: Create User Form

```tsx
// app/(dashboard)/users/new/page.tsx
import { CreateUserForm } from '@/components/create-user-form'

export const metadata = { title: 'Add User' }

export default function NewUserPage() {
  return (
    <div className="max-w-md">
      <h1 className="text-2xl font-bold mb-4">Add User</h1>
      <CreateUserForm />
    </div>
  )
}
```

```tsx
// components/create-user-form.tsx
'use client'

import { useActionState } from 'react'
import { createUser, type UserActionState } from '@/lib/actions/users'

export function CreateUserForm() {
  const [state, action, pending] = useActionState<UserActionState, FormData>(createUser, null)

  return (
    <form action={action} className="space-y-4">
      <div>
        <label htmlFor="name">Name</label>
        <input id="name" name="name" required className="input" />
        {state?.errors?.name && <p className="text-red-500 text-sm">{state.errors.name[0]}</p>}
      </div>

      <div>
        <label htmlFor="email">Email</label>
        <input id="email" name="email" type="email" required className="input" />
        {state?.errors?.email && <p className="text-red-500 text-sm">{state.errors.email[0]}</p>}
      </div>

      <div>
        <label htmlFor="role">Role</label>
        <select id="role" name="role" className="input">
          <option value="member">Member</option>
          <option value="admin">Admin</option>
          <option value="viewer">Viewer</option>
        </select>
      </div>

      <button type="submit" disabled={pending} className="btn-primary">
        {pending ? 'Creating...' : 'Create User'}
      </button>
    </form>
  )
}
```

## Key Patterns Used

1. **Route groups** `(dashboard)` — shared layout without affecting URL
2. **Double-layer auth** — middleware (edge cookie check) + layout (server session validation)
3. **Streaming** — `<Suspense>` for slow data (stats, activity feed)
4. **Suspense key pattern** — `key={q-page}` forces fallback re-display when search params change
5. **Debounced search** — `useDebouncedCallback` prevents navigation on every keystroke
6. **Server Actions** — form mutations with zod validation, user-friendly messages, `.trim()` on inputs
7. **`redirect()` outside try/catch** — `redirect` throws `NEXT_REDIRECT`, which try/catch would swallow
8. **URL state** — search query in searchParams (bookmarkable, shareable)
9. **`useActionState`** — form state management with loading and error states
10. **Metadata API** — per-page titles with template
