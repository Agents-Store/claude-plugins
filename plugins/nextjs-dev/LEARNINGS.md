# LEARNINGS.md — nextjs-dev

Accumulated fixes, discoveries, and improvements for the nextjs-dev plugin.

## 2026-03-28 — docker-patterns: New skill for Docker containerization

**Problem:** No skill covered Docker patterns for Next.js. Users had to manually write Dockerfiles, configure standalone output, and set up docker-compose for dev/prod — common tasks with well-established patterns.
**Fix:** Created new `docker-patterns` skill covering: standalone output config, multi-stage production Dockerfile, dev Dockerfile with hot reload, docker-compose with dev/prod services, .dockerignore, external services integration, build args for NEXT_PUBLIC_* vars, health checks, and troubleshooting.
**Root cause:** Missing skill — Docker containerization is a standard part of Next.js deployment but was not covered.
**Severity:** Major
