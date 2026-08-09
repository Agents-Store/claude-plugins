---
name: auth-and-access
description: This skill should be used when the user asks to "protect a Next.js page with Payload auth", "get the logged-in user in a server component", "add roles to the app", "restrict data per company/tenant", "secure server actions", or wires authentication and authorization across the nextjs-payloadcms stack.
---

# Auth & Access — One Identity System for Admin and Frontend

Use Payload's auth-enabled `users` collection as the **single identity system** for the whole app: the admin panel, the custom frontend, Server Actions, and API access all authenticate against it. Authorization lives in Payload access-control functions, so the same rules protect every entry point.

## The Session Helper

Centralize "who is calling?" in one helper used by every page and action:

```ts
// src/lib/session.ts
import { headers as nextHeaders } from 'next/headers'
import { getPayload, type Payload } from 'payload'
import config from '@payload-config'
import type { User } from '@/payload-types'

export interface Session { payload: Payload; user: User | null }

export const getSession = async (): Promise<Session> => {
  const payload = await getPayload({ config })
  const { user } = await payload.auth({ headers: await nextHeaders() })
  return { payload, user: (user as User) ?? null }
}
```

`payload.auth({ headers })` reads the HTTP-only cookie Payload set at login and returns the typed user (or `null`). It works in Server Components, Server Actions, Route Handlers, and `generateMetadata` — anywhere `next/headers` is available.

## Gating Pages

Check the session in the page or layout of the protected segment and redirect:

```tsx
// src/app/(frontend)/hr/layout.tsx — protects the whole /hr section
import { redirect } from 'next/navigation'
import { getSession } from '@/lib/session'
import { isHrOrAdmin } from '@/access/roles'

export default async function HrLayout({ children }: { children: React.ReactNode }) {
  const { user } = await getSession()
  if (!user) redirect('/login')
  if (!isHrOrAdmin(user)) redirect('/dashboard')
  return <>{children}</>
}
```

Keep `proxy.ts` (Next 16) / `middleware.ts` (Next 15) out of real auth decisions — it runs on every request without full session context and its docs warn against session management there. Use it only for cheap cosmetic redirects; the authoritative check is the layout/page + access control on the data itself. Login/logout themselves are Server Actions calling `payload.login({ collection: 'users', data, req })` and clearing cookies, or plain POSTs to Payload's `/api/users/login`.

## The Roles Module

Define roles once on the users collection and export typed helpers from `src/access/roles.ts` — the module both access functions and UI code import:

```ts
import type { Access, FieldAccess, Where } from 'payload'
import type { User } from '@/payload-types'

export type Role = 'super_admin' | 'admin' | 'hr_manager' | 'employee'

export const hasRole = (user: User | null | undefined, role: Role): boolean =>
  Boolean(user?.roles?.includes(role))

export const isHrOrAdmin = (u: User | null | undefined): boolean =>
  hasRole(u, 'admin') || hasRole(u, 'hr_manager') || hasRole(u, 'super_admin')

export const adminOnly: Access = ({ req }) => hasRole(req.user, 'admin')
export const authenticated: Access = ({ req }) => Boolean(req.user)

/** Field-level: only HR/admin may read or update (e.g. salary). Booleans only. */
export const hrOrAdminField: FieldAccess = ({ req }) => isHrOrAdmin(req.user)
```

Sharing one module keeps UI visibility (`{isHrOrAdmin(user) && <AdminNav />}`) and data enforcement from drifting apart — the UI check is convenience, the access function is the guarantee.

## Access Functions: Booleans and Row Filters

Collection access (`create`, `read`, `update`, `delete`) returns a boolean **or a `Where` constraint** that row-filters what the user can touch:

```ts
/** HR/admin see all; an employee sees only rows linked to them. */
export const ownByEmployeeRelation = (field = 'employee'): Access => ({ req }) => {
  if (isHrOrAdmin(req.user)) return true
  if (!req.user) return false
  return { [`${field}.user`]: { equals: req.user.id } } satisfies Where
}
```

Wire into collections:

```ts
export const LeaveRequests: CollectionConfig = {
  slug: 'leave-requests',
  access: {
    read: ownByEmployeeRelation(),
    create: authenticated,
    update: hrOrAdmin,
    delete: adminOnly,
  },
  fields: [
    { name: 'salary_note', type: 'textarea', access: { read: hrOrAdminField, update: hrOrAdminField } },
  ],
}
```

Facts that shape correct rules:

- Query constraints work on `read`/`update`/`delete` — **field-level access is boolean-only**, and `update: false` on a field silently discards submitted values rather than erroring.
- During the Admin-panel permissions probe, access functions run with `id`/`data` **undefined** — guard before using them (`if (!id) return true` for the indeterminate case, or return a safe default).
- Access functions may be async and query other collections via `req.payload` (e.g. "deletable only when no contracts reference it").

## Multi-Tenant Scoping

Scope every tenant-owned collection with one factory:

```ts
export const resolveActorCompanyId = (user: User | null | undefined): number | null => {
  const c = user?.company
  return c == null ? null : typeof c === 'object' ? (c.id as number) : (c as number)
}

/** super_admin sees all; everyone else only their company's rows. */
export const companyScopedAccess = (field = 'company'): Access => ({ req }) => {
  if (hasRole(req.user, 'super_admin')) return true
  const companyId = resolveActorCompanyId(req.user)
  if (!companyId) return false
  return { [field]: { equals: companyId } } satisfies Where
}
```

Pair it with a `beforeChange` hook (or field `defaultValue`) that pins the `company` field to the actor's company on create — access filters reads, the hook prevents cross-tenant writes. Handle the relation being either a raw ID or a populated doc (`resolveActorCompanyId` does this) — depth settings change the shape.

## Enforcing Access in Server Code

The Local API **skips access control by default** (`overrideAccess: true`). Every user-facing call must opt back in:

```ts
await payload.find({ collection: 'leave-requests', where, overrideAccess: false, user })
await payload.create({ collection: 'recognitions', data, overrideAccess: false, user })
```

Reserve the default (system mode) for seeds, migrations, jobs, and deliberate admin utilities — and leave a comment when you do, because a reviewer cannot tell an intentional bypass from a forgotten flag.

## Machine-to-Machine Access

For external services and MCP clients, use **API keys** instead of cookie sessions: enable `auth: { useAPIKey: true }` on a dedicated collection (or users), send `Authorization: users API-Key <key>` (header format is case-sensitive: `{collection-slug} API-Key`). Keys are encrypted with `PAYLOAD_SECRET` — rotating the secret invalidates every key, so plan rotations. Scope API-key users with the same roles/access functions as humans; there is no separate permission system to maintain.

## Cookie/CORS Checklist

- Browser `fetch` to Payload REST needs `credentials: 'include'`.
- Whitelist the frontend origin in both `cors: []` and `csrf: []` in `buildConfig` (same-app deployments list their own `NEXT_PUBLIC_SERVER_URL`).
- Cross-domain frontends need `auth: { cookies: { sameSite: 'None', secure: true } }` — set conditionally, `secure` breaks plain-HTTP localhost.

Related: where auth checks sit in actions → `backend-logic`; per-user reads on pages → `payload-to-nextjs`.
