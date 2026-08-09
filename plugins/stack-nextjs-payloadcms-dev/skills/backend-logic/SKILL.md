---
name: backend-logic
description: This skill should be used when the user asks to "implement business logic in Next.js + Payload", "write a server action with Payload", "add a Payload hook for a rule", "server action or hook?", "trigger a workflow on record change", or builds any mutation/workflow logic in the nextjs-payloadcms stack.
---

# Backend Logic — Server Actions, Hooks, and Jobs Composition

Implement all backend logic in this stack with three composable primitives: **Server Actions** (user-triggered mutations), **Payload hooks** (rules that fire on every write), and **Jobs Queue** (async and scheduled work). This skill covers how they compose; the `background-job` skill covers running the queue.

## The Composition Pattern

Every mutation flows through the same pipeline, and each stage has a distinct job:

```
UI form → Server Action → payload.create/update (overrideAccess: false, user)
              │                       │
     friendly pre-checks      access control (allow/deny/row-filter)
     revalidatePath           beforeValidate/beforeChange hooks (enforce rules)
                              afterChange hooks (side effects, queue jobs)
                                        │
                              Jobs Queue (email, external APIs, workflows)
```

**Enforce in hooks, pre-check in actions.** The action returns friendly, localized error messages for the UI; the hooks throw `APIError` as the authoritative gate — because the admin panel, REST, and GraphQL bypass your actions entirely and hit the same hooks. Duplicating a check in the action is UX; owning it in the hook is correctness.

## Server Actions

One file per domain in `src/actions/`, `'use server'` at the top. Canonical shape:

```ts
'use server'

import { revalidatePath } from 'next/cache'
import { getSession } from '@/lib/session'

export type ActionResult = { ok: true } | { ok: false; error: string }

export const createRecognitionAction = async (formData: FormData): Promise<ActionResult> => {
  const { payload, user } = await getSession()
  if (!user) return { ok: false, error: 'Not authorized' }

  const recipient = Number(formData.get('recipient'))
  const message = String(formData.get('message') ?? '').trim()
  if (!recipient) return { ok: false, error: 'Choose a recipient' }
  if (!message) return { ok: false, error: 'Write a message' }
  if (recipient === user.id) return { ok: false, error: 'Cannot thank yourself' }

  try {
    await payload.create({
      collection: 'recognitions',
      data: { recipient, message },
      overrideAccess: false,   // re-enable access control — Local API skips it by default
      user,                    // run as the actor, not as system
    })
    revalidatePath('/thanks')
    return { ok: true }
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : 'Error' }
  }
}
```

Rules, each with its reason:

- **Authenticate inside every action** (`getSession()`, bail if no user) — actions are plain POST endpoints reachable without your UI.
- **Pass `overrideAccess: false` + `user`** on every user-facing Local API call — the Local API defaults to `overrideAccess: true`, which silently skips all access control; forgetting this is the stack's #1 security foot-gun. Omit them only for deliberate system-level operations (seeds, jobs, admin utilities).
- **Return expected errors as values, throw nothing** — pair with `useActionState` on the client; `redirect()` throws by design, so call `revalidatePath`/`revalidateTag` before it.
- **Call `revalidatePath`/`revalidateTag` after successful writes** — fetches and the router cache are uncached-by-default in Next 15/16, but cached pages and tagged queries must be invalidated explicitly.

## Hooks: Rules on the Write Path

Hooks live in `src/hooks/`, imported by collection configs. Key signatures (all hook keys accept an **array** of functions):

```ts
import { APIError, type CollectionBeforeChangeHook, type CollectionAfterChangeHook } from 'payload'
import type { LeaveRequest } from '@/payload-types'

// beforeChange: validate + derive. `data` is a PARTIAL delta; originalDoc is the full pre-change doc.
export const handleLeaveReview: CollectionBeforeChangeHook<LeaveRequest> = ({ data, originalDoc, req, operation }) => {
  if (operation !== 'update' || !originalDoc) return data
  const from = originalDoc.status ?? 'pending'
  const to = data.status ?? from
  if (!isValidLeaveTransition(from, to)) {
    throw new APIError(`Invalid leave status transition: ${from} -> ${to}`, 400)
  }
  if (from === 'pending' && to !== 'pending') {
    data.reviewed_by = req.user?.id          // stamp the actor — works from admin AND actions
    data.reviewed_at = new Date().toISOString()
  }
  return data
}

// afterChange: side effects. Has the final doc (id exists even on create).
export const onLeaveDecided: CollectionAfterChangeHook<LeaveRequest> = async ({ doc, previousDoc, req, operation }) => {
  if (operation === 'update' && previousDoc.status === 'pending' && doc.status !== 'pending') {
    await req.payload.jobs.queue({ task: 'notifyLeaveDecision', input: { leaveId: doc.id } })
  }
  return doc
}
```

Hook discipline:

- **State machines belong in pure helpers** (`isValidLeaveTransition` in its own file) — unit-testable without a database, reusable from actions for pre-checks.
- **Guard self-updates with `context`** — an `afterChange` that calls `req.payload.update()` on its own collection recurses forever; pass `context: { skipHooks: true }` and return early when the flag is set.
- **Thread `req` into nested Local API calls inside hooks** (`req.payload.create({ req, ... })`) — Postgres wraps the whole request in a transaction; passing `req` makes nested writes commit/rollback atomically. Corollary: always `await` those calls — a fire-and-forget call riding the transaction can "succeed" on rolled-back data.
- **Queue anything slow** — hooks block the request lifecycle; emails, external APIs, and AI calls go to the Jobs Queue via `req.payload.jobs.queue(...)`. Pass IDs in job input, not whole documents — the job re-reads fresh state when it runs.

## Jobs: Async Work Triggered by Logic

Tasks are typed configs in `src/jobs/`, registered in `buildConfig({ jobs: { tasks } })`:

```ts
import type { TaskConfig } from 'payload'

export const notifyLeaveDecision: TaskConfig<{
  input: { leaveId: number }
  output: { sent: boolean }
}> = {
  slug: 'notifyLeaveDecision',
  inputSchema: [{ name: 'leaveId', type: 'number', required: true }],
  outputSchema: [{ name: 'sent', type: 'checkbox' }],
  retries: 2,
  handler: async ({ input, req }) => {
    const leave = await req.payload.findByID({ collection: 'leave-requests', id: input.leaveId, depth: 1 })
    await req.payload.sendEmail({ to: resolveEmail(leave), subject: `Leave ${leave.status}`, html: renderEmail(leave) })
    return { output: { sent: true } }
  },
}
```

Queue from anywhere server-side: hooks (`req.payload.jobs.queue`), actions (`payload.jobs.queue`), custom endpoints. Multi-step durable processes use **workflows** — a handler chaining `tasks.slug('stableId', { input })`; on retry, completed tasks return cached output so the workflow resumes where it failed. Make task handlers idempotent, since retries re-run them.

## Custom Endpoints: HTTP for External Callers

When an external system needs to call in (webhooks, integrations), add a custom endpoint rather than a Server Action:

```ts
// on a collection config
endpoints: [{
  path: '/:id/approve', method: 'post',
  handler: async (req) => {
    if (!req.user) return Response.json({ error: 'forbidden' }, { status: 403 })
    const body = await req.json()                     // body is NOT auto-parsed
    await req.payload.update({ collection: 'orders', id: req.routeParams.id, data: { status: 'approved' }, req })
    return Response.json({ ok: true })
  },
}]
```

Custom endpoints are **not authenticated by default** — check `req.user` (cookie/JWT/API-key auth all populate it). Use Next.js Route Handlers instead when the endpoint is frontend-shaped and does not need Payload request context.

## Choosing Quickly

- User clicks a button → **action**
- Rule must hold no matter who writes → **hook**
- Work is slow, retryable, or scheduled → **job**
- External system calls in → **custom endpoint**
- Several of the above → compose them; each stage stays small

Placement rationale and the full directory map live in the `architecture` skill; queue runtimes in `background-job`; access functions in `auth-and-access`.
