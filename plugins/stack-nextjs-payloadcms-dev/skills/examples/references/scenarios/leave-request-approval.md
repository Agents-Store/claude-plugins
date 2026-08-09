# Scenario: Leave Request Approval

Employees submit leave requests; HR approves/rejects; working days are computed against company holidays; the employee is emailed on decision. Every layer of the stack participates.

## 1. Collection — `src/collections/leave-requests.ts`

```ts
import type { CollectionConfig } from 'payload'
import { authenticated, hrOrAdmin, adminOnly, ownByEmployeeRelation } from '@/access/roles'
import { computeLeaveDays, handleLeaveReview, onLeaveDecided } from '@/hooks/leave-requests'

export const LeaveRequests: CollectionConfig = {
  slug: 'leave-requests',
  admin: { useAsTitle: 'id', defaultColumns: ['employee', 'start_date', 'end_date', 'days', 'status'] },
  access: {
    create: authenticated,
    read: ownByEmployeeRelation(),   // HR/admin: all rows; employee: only their own
    update: hrOrAdmin,
    delete: adminOnly,
  },
  hooks: {
    beforeChange: [computeLeaveDays, handleLeaveReview],
    afterChange: [onLeaveDecided],
  },
  fields: [
    { name: 'employee', type: 'relationship', relationTo: 'employees', required: true },
    { name: 'start_date', type: 'date', required: true },
    { name: 'end_date', type: 'date', required: true },
    { name: 'days', type: 'number', admin: { readOnly: true } },   // derived by hook
    { name: 'status', type: 'select', defaultValue: 'pending',
      options: ['pending', 'approved', 'rejected', 'cancelled'] },
    { name: 'reason', type: 'textarea' },
    { name: 'reviewed_by', type: 'relationship', relationTo: 'users', admin: { readOnly: true } },
    { name: 'reviewed_at', type: 'date', admin: { readOnly: true } },
  ],
}
```

## 2. Pure State Machine — `src/hooks/leave-status.ts`

```ts
export type LeaveStatus = 'pending' | 'approved' | 'rejected' | 'cancelled'

const TRANSITIONS: Record<LeaveStatus, LeaveStatus[]> = {
  pending: ['approved', 'rejected', 'cancelled'],
  approved: ['cancelled'],
  rejected: [],
  cancelled: [],
}

export const isValidLeaveTransition = (from: LeaveStatus, to: LeaveStatus): boolean =>
  from === to || TRANSITIONS[from].includes(to)
```

Unit test (`leave-status.test.ts`) covers the matrix without a database.

## 3. Hooks — `src/hooks/leave-requests.ts`

```ts
import { APIError, type CollectionBeforeChangeHook, type CollectionAfterChangeHook } from 'payload'
import type { LeaveRequest } from '@/payload-types'
import { workingDaysBetween } from '@/lib/date-utils'
import { isValidLeaveTransition, type LeaveStatus } from './leave-status'

/** Derive working days, honoring public holidays from the company_settings global. */
export const computeLeaveDays: CollectionBeforeChangeHook<LeaveRequest> = async ({ data, req }) => {
  if (data.start_date && data.end_date) {
    if (new Date(data.end_date) < new Date(data.start_date)) {
      throw new APIError('end_date must be on or after start_date', 400)
    }
    const settings = await req.payload.findGlobal({ slug: 'company_settings', depth: 0 })
    const holidays = (settings.public_holidays ?? []).map((h) => String(h.date).slice(0, 10))
    data.days = workingDaysBetween(new Date(data.start_date), new Date(data.end_date), holidays)
  }
  return data
}

/** Enforce the state machine; stamp the reviewer when leaving 'pending'. */
export const handleLeaveReview: CollectionBeforeChangeHook<LeaveRequest> = ({ data, originalDoc, req, operation }) => {
  if (operation !== 'update' || !originalDoc) return data
  const from = (originalDoc.status ?? 'pending') as LeaveStatus
  const to = (data.status ?? from) as LeaveStatus
  if (!isValidLeaveTransition(from, to)) {
    throw new APIError(`Invalid leave status transition: ${from} -> ${to}`, 400)
  }
  if (from === 'pending' && to !== 'pending') {
    data.reviewed_by = req.user?.id
    data.reviewed_at = new Date().toISOString()
  }
  return data
}

/** Queue the notification when a decision lands. IDs only in job input. */
export const onLeaveDecided: CollectionAfterChangeHook<LeaveRequest> = async ({ doc, previousDoc, req, operation }) => {
  if (operation === 'update' && previousDoc.status === 'pending' && doc.status !== 'pending') {
    await req.payload.jobs.queue({ task: 'notifyLeaveDecision', input: { leaveId: doc.id } })
  }
  return doc
}
```

## 4. Job — `src/jobs/notify-leave-decision.ts`

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
    const leave = await req.payload.findByID({ collection: 'leave-requests', id: input.leaveId, depth: 2 })
    const email = typeof leave.employee === 'object' && typeof leave.employee.user === 'object'
      ? leave.employee.user.email : null
    if (!email) return { output: { sent: false } }
    await req.payload.sendEmail({
      to: email,
      subject: `Leave request ${leave.status}`,
      html: `<p>Your leave request (${leave.days} days) was <b>${leave.status}</b>.</p>`,
    })
    return { output: { sent: true } }
  },
}
```

Register: `jobs: { tasks: [notifyLeaveDecision], autoRun: [{ cron: '*/2 * * * *', queue: 'default', limit: 10 }], shouldAutoRun: async () => process.env.ENABLE_JOBS === 'true' }`.

## 5. Actions — `src/actions/leave.ts`

```ts
'use server'

import { revalidatePath } from 'next/cache'
import { getSession } from '@/lib/session'
import { isHrOrAdmin } from '@/access/roles'
import type { ActionResult } from '@/lib/action-result'

export const submitLeaveAction = async (formData: FormData): Promise<ActionResult> => {
  const { payload, user } = await getSession()
  if (!user) return { ok: false, error: 'Not authorized' }
  const start = String(formData.get('start_date') ?? '')
  const end = String(formData.get('end_date') ?? '')
  if (!start || !end) return { ok: false, error: 'Pick both dates' }
  try {
    await payload.create({
      collection: 'leave-requests',
      data: { employee: Number(formData.get('employee')), start_date: start, end_date: end,
              reason: String(formData.get('reason') ?? '') },
      overrideAccess: false, user,
    })
    revalidatePath('/profile')
    return { ok: true }
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : 'Error' }
  }
}

export const reviewLeaveAction = async (id: number, decision: 'approved' | 'rejected'): Promise<ActionResult> => {
  const { payload, user } = await getSession()
  if (!user || !isHrOrAdmin(user)) return { ok: false, error: 'HR only' }   // friendly pre-check
  try {
    // handleLeaveReview enforces the transition + stamps reviewer at the hook layer
    await payload.update({ collection: 'leave-requests', id, data: { status: decision },
                           overrideAccess: false, user })
    revalidatePath('/hr')
    return { ok: true }
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : 'Error' }
  }
}
```

## 6. Query + Page — `src/lib/queries/leave.ts`, `src/app/(frontend)/hr/page.tsx`

```ts
export const listPendingLeave = async (payload: Payload) => {
  const res = await payload.find({
    collection: 'leave-requests',
    where: { status: { equals: 'pending' } },
    depth: 1, sort: 'start_date', limit: 100,
  })
  return res.docs.map((d) => ({ id: d.id, days: d.days ?? 0, start: d.start_date, end: d.end_date,
    employeeName: typeof d.employee === 'object' ? d.employee.full_name : String(d.employee) }))
}
```

The HR page is role-gated by `src/app/(frontend)/hr/layout.tsx` (redirect unless `isHrOrAdmin`); rows render approve/reject buttons wired to `reviewLeaveAction` via a client component.

## 7. Integration Test — `src/collections/leave-requests.integration.test.ts`

Assert cross-role behavior through the Local API:

- employee creates a request → `status: 'pending'`, `days` computed
- employee `find` with `overrideAccess: false` → sees only own rows; HR sees all
- HR updates `pending → approved` → `reviewed_by` stamped; job appears in `payload-jobs`
- HR updates `rejected → approved` → throws (invalid transition)

## Adaptation Notes

Rename the collection and states for any review workflow (expenses, sign-offs, moderation). Keep: the pure state machine, hook-level enforcement, action-level pre-checks, job-per-notification, cross-role integration test.
