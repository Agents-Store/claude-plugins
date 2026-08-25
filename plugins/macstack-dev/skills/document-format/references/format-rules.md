# Document templates and a worked conversion

Templates below are shown with English prose. In a real project the prose follows
`docs.language`; the anchors, YAML keys and ids never change.

Every document opens with its header anchor and closes with its journal:

````markdown
<!-- macstack:doc=user_cases lang=ru version=2.0 -->
# ...

...

<!-- macstack:section=journal -->
## Document journal

| version | date | what changed | source |
|---|---|---|---|
| 2.0 | 2026-08-25 | converted to the v2 block format | migration |
````

---

## The worked conversion

This is the single row that made the case for v2. From a live project, one row of
a six-column table, 876 characters:

```markdown
| Период коуча — детали и спор | /zeitraeume?period= | coach | Сводка периода (рабочих дней,
подтверждено, в разъяснении) и таблица по дням: дата, город, роль, отработанное время,
назначение с адресом, статус. Спорные дни выделены | Открыть диалог разъяснения по
конкретному дню: обязательный текст плюс вложения; отправить на проверку | Правки
подтверждённых часов напрямую — только через Sonderänderung. Молчаливого изменения без
автора и причины |
```

The same information as an entity:

````markdown
<!-- macstack:screen=coach-period-detail -->
### coach-period-detail · Период коуча — детали и спор

```yaml
path: /zeitraeume?period=
roles: [coach]
cases: [C-08, C-09]
```

<!-- macstack:content -->
**Что на экране**
- Сводка периода: рабочих дней, подтверждено, в разъяснении.
- Таблица по дням: дата, город, роль, отработанное время, назначение с адресом, статус.
- Спорные дни выделены.

<!-- macstack:actions -->
**Что можно сделать**
- Открыть диалог разъяснения по конкретному дню — обязательный текст плюс вложения.
- Отправить разъяснение на проверку.

<!-- macstack:forbidden -->
**Чего здесь быть не должно**
- Правки подтверждённых часов напрямую: только через `Sonderänderung`.
- Молчаливого изменения без автора и причины.
````

Same facts, same machine-readability, and a client can now correct one line
without editing a 900-character cell.

---

## client/OVERVIEW.md

Sections: `howto` · `product` · `goals` · `audience` · `processes` · `invariants`
· `refuses` · `glossary` · `related` · `journal`.

````markdown
<!-- macstack:section=goals -->
## Goals

<!-- macstack:goal=grow-inbound -->
### grow-inbound · Grow the inbound channel

```yaml
horizon: 2026-12-31
metric: { unit: "% new clients from site", target: 50 }
owner: owner
status: in_progress
```

<!-- macstack:statement -->
By the end of the year, half of all new clients arrive through the site.

<!-- macstack:section=audience -->
## Who this is for

- **`coach`** — the person who runs the sessions and gets paid for them.
- **`traeger-contact`** — the client's coordinator, who confirms hours.
- **`ohawo-admin`** — the operator who invoices and resolves disputes.

> Roles are defined in `AUTOMATION.md`. This section names them; that document
> says what each one sees, may do and is responsible for.

<!-- macstack:section=processes -->
## How a month runs

<!-- macstack:process=period-close -->
### period-close · Closing a period

```yaml
automation: hybrid
produces: [confirmed-hours]
roles: [traeger-contact, ohawo-admin]
schedule: "twice a month"
```

<!-- macstack:flow -->
1. The system projects the hours worked in the half-month that ended.
2. The client's coordinator confirms or disputes them.
3. Confirmed hours become an invoicing fact and can no longer be edited silently.

<!-- macstack:section=glossary -->
## Terms

- **Период** — `period`. Half a calendar month, the unit hours are confirmed in.
- **Назначение** — `einsatz`. One coach assigned to one centre for one stretch of time.
````

---

## client/USER-CASES.md

Sections: `howto` · `crosscutting` · `roles` · `scenarios` · `prohibitions` ·
`outofscope` · `maintaining` · `journal`.

The per-case shape is in `SKILL.md`. Two things it does not show:

**Acceptance bullets are addressable.** The renderer allocates `C-04.a1`,
`C-04.a2` … in order. That id is what a test's `covers` names and what a client's
comment resolves against, so bullets are appended, never inserted above an
existing one without a version bump saying so.

**A prohibition has no flow and no experience.** It states the refusal and how the
refusal explains itself:

````markdown
<!-- macstack:case=Z-07 -->
### Z-07 · A training centre never sees the coach's rate

```yaml
role: traeger-contact
priority: critical
screens: [traeger-period, traeger-invoice]
```

<!-- macstack:acceptance -->
**Done when**
- no screen, export or email available to `traeger-contact` contains the coach's rate;
- an attempt to reach it by direct URL returns a refusal that says the data belongs
  to another party, rather than a blank page or a generic error.
````

The second bullet is the rule: **a prohibition needs two assertions** — the
platform refuses, and the refusal explains itself. A refusal that looks like a
bug is a bug.

---

## client/UX-UI.md

Sections: `howto` · `principles` · `navigation` · `states` · `responsive` ·
`accessibility` · `tone` · `screens` · `journal`.

The cross-cutting sections are written once, in prose, and apply to every screen:

````markdown
<!-- macstack:section=states -->
## Empty, loading, error

Every list, table and card declares all three:

- **Empty** — says what would appear here and what to do to make it appear. Never
  a bare "no data".
- **Loading** — the layout does not jump when content arrives.
- **Error** — says what failed and what the person can do now. Never a stack trace,
  never a code alone.
````

The per-screen shape is the worked conversion above.

---

## client/AUTOMATION.md

Sections: `howto` · `roles` · `tasks` · `triggers` · `journal`. Three entity
kinds.

````markdown
<!-- macstack:section=roles -->
## Roles

<!-- macstack:role=coach -->
### coach · Coach

```yaml
cases: ["C-*"]
isolation: own records only
```

<!-- macstack:sees -->
Own monthly schedule, calculated attendance, the client's confirmation state and own documents.

<!-- macstack:can -->
Check in and out of assigned sessions, request a commented correction before verification,
upload a monthly invoice. Cannot sign a period or edit a billing fact directly.

<!-- macstack:section=tasks -->
## Tasks

<!-- macstack:task=confirm-period -->
### confirm-period · Confirm the period's hours

```yaml
role: traeger-contact
gate: approve
trigger: trg-week-close
process: period-close
```

<!-- macstack:flow -->
The coordinator opens the projected period, checks the days and either confirms it
or opens a dispute on a specific day.

<!-- macstack:section=triggers -->
## Triggers

<!-- macstack:trigger=trg-week-close -->
### trg-week-close · Semi-monthly projection

```yaml
type: schedule
source: schedule
schedule: "0 6 1,16 * *"
raises: [wf-period-projection]
```

<!-- macstack:what_happens -->
On the 1st and the 16th the system projects the half-month that just ended and
prompts the client's coordinator. The coach is never prompted by this trigger.
````

**`type` and `source` answer different questions.** `type` is the mechanism —
cron, webhook, database event. `source` is who or what originates it:
`interface` (a person pressed something), `backend` (our own code decided),
`integration` (an outside system called us), `schedule` (the clock), `manual`
(an operator ran it by hand). The client cares about `source`; the engineer
cares about `type`. Both are declared because neither implies the other.

**A task is either a gate or a workflow.** `gate` + `role` means a person acts;
`workflow` means a machine acts. A task claiming both is a task nobody owns.

---

## client/HANDBOOK.md

Sections: `howto` · `start` · `roles` · `procedures` · `problems` · `glossary` ·
`journal`.

Seeded from the cases and the screens, then written by a human. The difference in
register matters: a case says *what must be possible*, a procedure says *how a
person does it on a Tuesday*.

````markdown
<!-- macstack:procedure=start-a-session -->
### start-a-session · Start a session

```yaml
role: coach
screens: [coach-today]
cases: [C-04]
frequency: every working day
```

<!-- macstack:steps -->
1. Open the app. The "Today" screen shows your next session.
2. Press **Start session**.
3. If the phone asks for location, allow it — it takes one tap and saves you a check later.

<!-- macstack:result -->
The session shows as started, and the time is recorded. You do not need to write anything down.
````

---

## client/OPEN-QUESTIONS.md

Sections: `howto` · `client-inputs` · `deferred` · `journal`.

````markdown
<!-- macstack:section=client-inputs -->
## What we are waiting for from you

<!-- macstack:open=A5 -->
### A5 · VAT wording for invoices

```yaml
owner: client
asked_on: 2026-08-14
goes_to: company.vat_note_exempt_4nr21
blocks: [M6-T12]
```

<!-- macstack:what -->
Which VAT exemption clause should appear on issued invoices, in the exact wording
your accountant expects.

<!-- macstack:if_wrong -->
Invoices go out with a clause that does not match your tax position. They are
valid documents, so nobody notices until an audit does.

<!-- macstack:section=deferred -->
## What we deliberately postponed

<!-- macstack:open=B7 -->
### B7 · No rate limiting on the public form

```yaml
owner: team
```

<!-- macstack:what -->
The public enquiry form accepts unlimited submissions from one address.

<!-- macstack:reason_safe_to_defer -->
The form is not linked from anywhere public yet and reaches a human inbox that a
person reads. Abuse would be visible the same day.

<!-- macstack:trigger_that_makes_it_unsafe -->
The moment the form is linked from the marketing site, or the moment it starts
creating records automatically.
````

Both §B fields argue *against* acting now. That is the point, and it is why §B is
not a backlog: an item can sit here for a year and only becomes a task when its
trigger fires.

---

## history/TASKS.md

````markdown
<!-- macstack:milestone=M11 -->
## M11 · Auth hardening

```yaml
status: doing
target: 2026-09-15
```

<!-- macstack:done_when -->
- works in every role area at both narrow and wide viewport
- migrations proven, up and down, against a seeded snapshot
- `auth.pinning.spec.ts` unchanged and green
- full suite, zero skipped
- the `AuthContext` shape frozen for M12

<!-- macstack:task=M11-T9 -->
### M11-T9 · Verify email before first login

```yaml
status: doing
tracker: TRACK-142
milestone: M11
spec: client/USER-CASES.md#C-02
files: [src/auth/verify.ts, src/auth/routes.ts]
acceptance: 'auth.int.spec.ts — "rejects unverified login"'
blocked_by: [A5]
```

<!-- macstack:notes -->
Remove the verify guard and that named test reddens. That is the check.
````

`done_when` items are falsifiable: each one either passes or it does not. "Works
well" is not a check.

`acceptance` in its strongest form names the mutation that breaks it — *remove X
and this named test reddens*. A bare filename is not acceptance, and a
`file.ts:120` pointer is banned outright: line numbers rot the moment the file
above them grows.

---

## history/log.md

````markdown
<!-- macstack:entry=2026-08-25-work -->
## [2026-08-25] work | M11 — split the export run in two

```yaml
kind: work
tasks: [M11-T42, M11-T43]
```

<!-- macstack:what -->
The export now runs as two independent jobs — metadata, then rows — instead of one.

<!-- macstack:notes -->
Tried one job with an internal checkpoint first. Rows outnumber metadata 400:1, so a
mid-job crash always looked like a metadata failure and sent every investigation the
wrong way.
````

A `work` entry with an empty `notes` is usually a work entry not worth writing:
`what` is the half git already knows, `notes` is the half it cannot hold.

---

## inbox/README.md

````markdown
<!-- macstack:intake=client-portal-spec-2026-08-24.pdf -->
### client-portal-spec-2026-08-24.pdf

```yaml
received: 2026-08-24
from: OHAWO
channel: email
supersedes: —
processed_in: history/deltas/2026-08-24-client-portal.md
size_mb: 9.5
pages: 18
```

<!-- macstack:what -->
Page screenshots of the client portal, not text. Over the 5 MB warning threshold —
ask for the source document if it is ever needed again.
````

---

## Conversion checklist

When turning an old table-shaped document into this format:

1. One row becomes one entity. The first column becomes the id and the title.
2. Short factual columns become YAML keys. Long prose columns become anchored
   sections.
3. A column holding the same value on every row is not a column — state it once
   in the section's intro and drop it.
4. An index table above the entities is deleted, not converted. It regenerates.
5. Anything that survives as a table must fit the budget. Re-measure; do not
   assume.
6. Append one journal row saying the document was converted, and bump the version
   in the header, the journal and `docs.files`.
