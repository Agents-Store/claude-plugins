---
name: background-job
description: This skill should be used when the user asks to "run background jobs in Payload", "schedule a cron task", "set up a worker for Next.js + Payload", "jobs are not running", "queue emails or AI processing", or configures async/scheduled work in the nextjs-payloadcms stack.
---

# Background Jobs — Payload Jobs Queue as the Stack's Workflow Engine

Run all asynchronous, scheduled, and multi-step work on the **Payload Jobs Queue** — it is the stack's built-in workflow engine, persisted in the database, with retries, resume-from-failure workflows, and cron scheduling. No external queue (n8n, Trigger.dev, BullMQ) is needed for typical product workloads.

## Two Halves: Queuing and Running

The queue only stores work. **Nothing executes unless a runner with a matching queue name is configured** — a schedule/queue mismatch is the #1 "my jobs never run" cause.

```
QUEUING                                   RUNNING
payload.jobs.queue({ task, input })       autoRun cron (in-process)
schedule: [{ cron, queue }] on a task     payload jobs:run bin script (worker process)
waitUntil: futureDate                     GET /api/payload-jobs/run (serverless cron)
                                          payload.jobs.run() (tests/manual)
```

## Defining Work

Tasks live in `src/jobs/`, one file each, registered in `buildConfig({ jobs: { tasks } })`:

```ts
import type { TaskConfig } from 'payload'
import { selectExpiringDocuments } from './select-expiring'   // pure, unit-testable

export const notifyExpiringDocuments: TaskConfig<{
  input: Record<string, never>
  output: { count: number }
}> = {
  slug: 'notify-expiring-documents',
  outputSchema: [{ name: 'count', type: 'number' }],
  schedule: [{ cron: '0 8 * * *', queue: 'nightly' }],   // QUEUES daily; a runner must drain 'nightly'
  retries: 2,
  handler: async ({ req }) => {
    const { docs } = await req.payload.find({ collection: 'employee_documents', limit: 1000, depth: 0 })
    const expiring = selectExpiringDocuments(docs, new Date(), 30)
    if (expiring.length > 0) {
      await req.payload.sendEmail({ to: process.env.HR_NOTIFY_EMAIL, subject: `Expiring: ${expiring.length}`, html: render(expiring) })
    }
    return { output: { count: expiring.length } }
  },
}
```

Multi-step processes use **workflows** — completed steps return cached output when the handler retries, so the flow resumes where it failed:

```ts
import type { WorkflowConfig } from 'payload'

export const onboardEmployee: WorkflowConfig<'onboardEmployee'> = {
  slug: 'onboardEmployee',
  inputSchema: [{ name: 'employeeId', type: 'number', required: true }],
  queue: 'default',
  handler: async ({ job, tasks }) => {
    await tasks.createAccounts('1', { input: { employeeId: job.input.employeeId } })
    await tasks.sendWelcomeEmail('2', { input: { employeeId: job.input.employeeId } })
    await tasks.scheduleProbationReview('3', { input: { employeeId: job.input.employeeId } })
  },
}
```

Rules with reasons: give task invocations **stable string IDs** (`'1'`, `'2'`) — they key the resume cache; make handlers **idempotent** — retries re-run them; pass **IDs, not documents**, as input — the job re-reads fresh state; prefer **inline handler functions** over string file paths — string paths need separate transpilation outside Next.js.

## Choosing the Runner (Deployment Topology)

| Deployment | Runner | Configuration |
|---|---|---|
| Local dev | `autoRun` in the Next.js process | Gate with env so dev machines don't run prod-like crons |
| Docker, single container | `autoRun` in the web process | Simplest; jobs share web CPU |
| Docker, serious workloads | **Separate worker container** running the bin script | Isolates job load from request latency |
| Serverless (Vercel) | HTTP endpoint + platform cron | `autoRun` never works on serverless — instances are ephemeral |

**autoRun (in-process):**

```ts
jobs: {
  tasks: [notifyExpiringDocuments],
  autoRun: [{ cron: '*/5 * * * *', queue: 'default', limit: 10 },
            { cron: '0 8 * * *', queue: 'nightly', limit: 10 }],
  shouldAutoRun: async () => process.env.ENABLE_JOBS === 'true',
}
```

The `ENABLE_JOBS` gate lets one env var decide which instance processes jobs. Dev note: HMR breaks autoRun's cron — restart `next dev` after config changes.

**Worker container (recommended for Docker):**

```yaml
# docker-compose.yml
services:
  web:
    build: .
    environment: { ENABLE_JOBS: 'false' }   # web serves requests only
  worker:
    build: .
    command: pnpm payload jobs:run --cron "*/1 * * * *" --all-queues --handle-schedules
    environment: { ENABLE_JOBS: 'false' }
    depends_on: [db]
```

`--handle-schedules` makes the worker also evaluate `schedule:` crons (queuing); `--queue nightly` scopes a worker to one queue when workloads need isolation.

**Serverless:**

```json
// vercel.json
{ "crons": [{ "path": "/api/payload-jobs/run?limit=50&allQueues=true", "schedule": "*/5 * * * *" }] }
```

Secure the endpoint via `jobs.access.run` checking `Authorization: Bearer ${CRON_SECRET}`, because it is reachable by anyone otherwise.

## Multi-Instance Safety

When several replicas run, enable schedule handling on **one** instance only (`disableScheduling: true` on the others' autoRun entries) — otherwise each replica queues its own copy of every scheduled job. Job *execution* is safe to parallelize; Payload locks jobs via the `processing` flag. For per-entity serialization (e.g. one sync per document at a time), enable `jobs.enableConcurrencyControl: true` (adds an indexed column — create a migration) and set `concurrency: ({ input }) => \`sync:${input.docId}\`` on the task; `supersedes: true` makes last-queued-wins for debounce patterns.

## Observability & Debugging

Jobs persist in the hidden `payload-jobs` collection. Unhide it in dev to debug:

```ts
jobs: { jobsCollectionOverrides: ({ defaultJobsCollection }) => ({
  ...defaultJobsCollection,
  admin: { ...defaultJobsCollection.admin, hidden: false },
}) }
```

Inspect `hasError`, `totalTried`, `log` (per-task inputs/outputs/errors), `processing`, `waitUntil`. Common diagnoses:

- Job queued, never runs → no runner for that queue name, or serverless with autoRun.
- Scheduled task never queues → no runner has `--handle-schedules` / `disableScheduling` everywhere.
- Job runs twice per tick → multiple instances handling schedules.
- Task retried but external effect duplicated → handler not idempotent; add an idempotency check or move the effect after the write.
- One-off future work → `payload.jobs.queue({ task, input, waitUntil: date })`, not a schedule.

## Testing Jobs

Run the queue synchronously in integration tests: `await payload.jobs.queue({ task: 'x', input })` then `await payload.jobs.run({ queue: 'default' })` and assert on effects. Keep heavy logic in pure helpers (`select-expiring.ts`) so most coverage is DB-free unit tests.

Related: queueing from hooks and actions → `backend-logic`; deciding job vs hook vs action → `architecture`.
