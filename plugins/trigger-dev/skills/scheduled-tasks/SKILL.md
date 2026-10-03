---
name: scheduled-tasks
description: Schedule Trigger.dev tasks with cron — declarative schedules defined on schedules.task and imperative schedules created through the SDK or API. Use when the user asks to "schedule a trigger.dev task", "run a task on a cron", "create a schedule", "dynamic or per-user schedules", or why a schedule did not fire.
---

# Scheduled Tasks

Run Trigger.dev tasks on a cron. A schedule is either **declarative** (the cron lives on the task and is synced when you deploy) or **imperative** (created at runtime through the SDK or the API, for per-user or per-tenant schedules).

> This skill is being expanded (cron syntax, timezones, dynamic multi-tenant schedules, testing, and "when schedules won't trigger"). For now use the minimal example below and `skills/task-development/references/scheduled-tasks.md`.

## Declarative schedules

```ts
import { schedules } from "@trigger.dev/sdk";

export const dailyCleanup = schedules.task({
  id: "daily-cleanup",
  cron: "0 0 * * *",            // midnight UTC; or { pattern: "0 9 * * *", timezone: "Asia/Tokyo" }
  run: async (payload) => {
    // payload.timestamp, payload.timezone, payload.scheduleId
  },
});
```

The schedule syncs when you run `dev` or `deploy`; editing or removing `cron` updates it on the next run of either. There is no `schedules:attach` CLI command: a declarative schedule needs only the task. In dev a schedule fires only while the dev CLI runs; in staging and production only for the task in the current deployment.

## Imperative schedules

See `skills/task-development/references/scheduled-tasks.md` for `schedules.create()`, `schedules.list()` and `schedules.del()`.
