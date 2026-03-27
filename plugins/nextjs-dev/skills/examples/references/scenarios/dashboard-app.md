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

```ts
// middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const sessionToken = request.cookies.get('next-auth.session-token')

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

## Step 3: Dashboard Layout with Sidebar

```tsx
// app/(dashboard)/layout.tsx
import { getServerSession } from 'next-auth'
import { redirect } from 'next/navigation'
import { authOptions } from '@/lib/auth'
import { Sidebar } from '@/components/sidebar'
import { TopNav } from '@/components/top-nav'

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
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

      <Suspense key={`${q}-${page}`} fallback={<TableSkeleton />}>
        <UserTable query={q} page={Number(page) || 1} />
      </Suspense>
    </div>
  )
}
```

## Step 6: Server Actions for CRUD

```tsx
// lib/actions/users.ts
'use server'

import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'
import { z } from 'zod'
import { db } from '@/lib/db'

const userSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Invalid email'),
  role: z.enum(['admin', 'member', 'viewer']),
})

export type UserActionState = { errors?: Record<string, string[]>; message?: string } | null

export async function createUser(prevState: UserActionState, formData: FormData): Promise<UserActionState> {
  const parsed = userSchema.safeParse(Object.fromEntries(formData))

  if (!parsed.success) {
    return { errors: parsed.error.flatten().fieldErrors }
  }

  await db.user.create({ data: parsed.data })
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
2. **Middleware** — authentication guard on all dashboard routes
3. **Streaming** — `<Suspense>` for slow data (stats, activity feed)
4. **Server Actions** — form mutations with validation and revalidation
5. **URL state** — search query in searchParams (bookmarkable, shareable)
6. **`useActionState`** — form state management with loading and error states
7. **Metadata API** — per-page titles with template
