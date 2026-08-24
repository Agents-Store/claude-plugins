---
name: test-cases
description: This skill should be used when the user asks to "make test cases", "составить тест-кейсы", "generate tests from the user cases", "как это проверять", "написать сценарии проверки", "acceptance checklist", "what do we test for C-04", "обновить тест-кейсы под новую версию кейсов", or wants a QA/acceptance plan derived from USER-CASES.md. Derives TEST-CASES.md from the acceptance bullets of USER-CASES.md — one test per bullet, each tagged auto or manual — and keeps the two in step.
---

# Test Cases — derived from the acceptance bullets

Three documents form a chain, and this one is the middle link:

| Document | Answers |
|---|---|
| `USER-CASES.md` | What must be true for a person — the bar |
| **`TEST-CASES.md`** | **How each of those statements is verified** |
| `reviews/*-conformance.md` | What was actually found the day someone checked |

`TEST-CASES.md` is standing and versioned; a review is dated and disposable. Never
merge them, and never let a review become the only place a check is written down.

Open `${CLAUDE_PLUGIN_ROOT}/skills/project-docs/references/doc-contracts.json`
(`documents.test_cases`) for the anchors, the id pattern and the required item fields.
Headings and prose follow `docs.language`; anchors and ids never translate.

## The derivation rule

**Every acceptance bullet under "Готово, если" gets at least one test.** The bullet is
the assertion; the test is how you check it. A bullet with no test is an unverified
promise, and lint reports it.

Section order mirrors `USER-CASES.md` exactly (`crosscutting`, `roles`, `scenarios`,
`prohibitions`) so the two read side by side.

## Ids

`<case-id>.T<n>` — `C-06.T3`, `Z-08.T1`, `S-02.T4`. Traceability is built into the id:
`grep 'C-06\.'` finds every test for that case. ASCII only, per the folder standard.
Numbers are never reused once struck.

## Anatomy of one test

```
### C-06.T3 · Предупреждение без геолокации   [manual]

Покрывает: C-06, пункт «предупреждение написано спокойно».

**Предусловия:** коуч авторизован; геолокация в браузере запрещена.
**Шаги:** 1. открыть первый экран · 2. нажать «Начать занятие».
**Ожидаемо:** показан текст, объясняющий последствие — ручная проверка и возможная
задержка оплаты; формулировка не обвиняет и не выглядит отказом.
**Чем доказано:** — (человек)
```

`covers` and `expected` are always required. A `manual` test additionally needs
`preconditions` and `steps`; an `auto` test additionally needs `evidence`.

## auto or manual

| Tag | Use when | Evidence |
|---|---|---|
| `auto` | The assertion is decidable by a machine: a state change, a refusal, an arithmetic result, a field value, a permission boundary | The **title** of the automated test that proves it — never a `file.ts:214` pointer, which rots. `attendance.int.spec.ts — "allows check-in without geolocation"` |
| `manual` | The assertion is about tone, layout, readability, a real device, a third-party surface, or anything needing a person's judgement | `— (человек)`. Steps must be followable by someone who has never seen the code |

Do not tag something `auto` because it *could* be automated one day. The tag describes
how it is checked today; an untagged aspiration is how a coverage table starts lying.

## Three shapes worth naming

- **`Z-` prohibitions** need two assertions, not one: the platform refuses, **and** the
  refusal explains itself. A refusal that succeeds silently fails the case.
- **`S-` end-to-end scenarios** are ordered, and each step names the case it exercises.
  They are the only place ordering between cases is asserted.
- **`X-` cross-cutting cases** apply to every role. Either write one test per role, or
  one test that names the roles it must be run as — say which, do not leave it implied.

## Regenerating without destroying work

Update **by id**, never by rewriting the file.

1. Read `USER-CASES.md`, its version, and the `derived_from` version in the
   `TEST-CASES.md` header. Equal → nothing to do unless asked.
2. For each acceptance bullet: an existing test that covers it stays as written —
   hand-refined steps are the point of this document and are never regenerated over.
3. A bullet with no test → add one, numbered after the highest `.T<n>` for that case.
4. A test whose bullet no longer exists → **strike, do not delete**:
   `~~C-04.T2~~ · СНЯТ в v1.9 — пункт удалён`. Struck ids are never reused.
5. Bump the header to the `USER-CASES.md` version derived from and add a journal row.
6. Refresh the `coverage` table: per role, cases · bullets · tests · auto/manual split ·
   bullets with no test.

## When a test cannot be written

If verifying a bullet requires a fact the case does not state — a threshold, a message,
a deadline — **do not invent it here.** The gap is in `USER-CASES.md`, not in the tests.
Raise it: a question for the client goes to `OPEN-QUESTIONS.md §A`; a wording change to
an agreed case goes through `macstack-dev:docs-merge` as a contradiction. A test case
that quietly invents its own acceptance criterion becomes a second specification, and
the folder exists to prevent exactly that.

## Routing

| Situation | Do |
|---|---|
| No `TEST-CASES.md` yet | Generate the full set from the current `USER-CASES.md` |
| `USER-CASES.md` bumped a version | Re-derive incrementally per the steps above |
| A bullet is untestable as written | `docs-merge` (contradiction) or `OPEN-QUESTIONS.md §A` |
| Recording what a test run actually found | `reviews/<date>-<slug>-conformance.md`, not here |
| After any change | `macstack-dev:lint` |
