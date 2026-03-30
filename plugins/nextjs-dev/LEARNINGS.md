# LEARNINGS.md — nextjs-dev

Accumulated fixes, discoveries, and improvements for the nextjs-dev plugin.

## 2026-03-30 — troubleshoot: Missing next/image debugging for authenticated upstream

**Problem:** Troubleshoot skill had no coverage of broken images from `next/image` when the upstream source requires authentication. Since `next/image` proxies through `/_next/image`, the 403 error is opaque — developers see broken images with no visible error message in the browser.
**Fix:** Added a new "Image Issues (next/image)" section with a table covering 403 from authenticated upstream, missing remotePatterns, private network issues, and quality/sizing problems. Added a debugging tip about checking `/_next/image` requests in the Network tab.
**Root cause:** Troubleshoot skill covered hydration, build, data fetching, and deployment errors but missed image optimization issues entirely.
**Severity:** Major

## 2026-03-28 — docker-patterns: New skill for Docker containerization

**Problem:** No skill covered Docker patterns for Next.js. Users had to manually write Dockerfiles, configure standalone output, and set up docker-compose for dev/prod — common tasks with well-established patterns.
**Fix:** Created new `docker-patterns` skill covering: standalone output config, multi-stage production Dockerfile, dev Dockerfile with hot reload, docker-compose with dev/prod services, .dockerignore, external services integration, build args for NEXT_PUBLIC_* vars, health checks, and troubleshooting.
**Root cause:** Missing skill — Docker containerization is a standard part of Next.js deployment but was not covered.
**Severity:** Major
