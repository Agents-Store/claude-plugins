---
name: examples
description: This skill should be used when the user asks to "show a complete Next.js + Payload example", "walk through a real feature on this stack", "example of an approval workflow in Payload", "content publishing example", or wants a worked end-to-end scenario for the nextjs-payloadcms stack.
---

# Examples — Worked Scenarios

Complete walkthroughs of real features built on the Next.js + Payload stack, each applying the `full-feature` recipe across all layers (collection → access → hooks → jobs → actions → queries → UI → tests). Read the scenario closest to the task at hand and adapt it.

## Available Scenarios

### 1. Leave Request Approval — `references/scenarios/leave-request-approval.md`

An HR-portal feature: employees submit leave requests, HR approves or rejects, days are computed against company holidays, a notification job emails the decision. Demonstrates:

- Status state machine enforced in a `beforeChange` hook (pure helper + `APIError`)
- Derived field computation reading a global (`company_settings.public_holidays`)
- Row-filtered access (`employee sees own, HR sees all`)
- Reviewer stamping from `req.user`
- `afterChange` → job queue → email
- Server Action with friendly pre-checks mirroring hook rules
- Integration test asserting cross-role behavior

Use it as the pattern for any **record + review/approve workflow**: expense claims, time-off, document sign-off, moderation queues.

### 2. Content Publishing with Revalidation — `references/scenarios/content-publishing.md`

A marketing-site feature: posts with drafts and scheduled publishing, statically generated pages that update the moment an editor hits Publish. Demonstrates:

- Drafts/versions (`_status`) and scheduled publish via Jobs Queue (`waitUntil`)
- Slug generation field hook
- Cached, tagged reads (`unstable_cache` + tags; `'use cache'` variant noted)
- The admin-edit bridge: `afterChange` hook calling `revalidatePath`/`revalidateTag`
- `generateStaticParams` + on-demand revalidation working together
- Public read access returning a `Where` constraint (`_status: published`)

Use it as the pattern for any **content-shaped, cache-sensitive surface**: blogs, landing pages, docs, catalogs.

## How to Apply a Scenario

1. Map the scenario's collections onto the domain at hand (leave-requests → expense-claims, posts → products).
2. Keep the layer placement identical — only the field lists and rule contents change.
3. Copy the test structure: one pure-helper unit test, one cross-role integration test.
4. Re-run the `full-feature` Definition of Done checklist before calling it complete.
