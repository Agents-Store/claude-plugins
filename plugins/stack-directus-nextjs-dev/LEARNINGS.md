# Learnings

## 2026-03-30 — directus-to-nextjs: Missing access_token in directusAsset helper

**Problem:** The `directusAsset()` helper function constructed image URLs without authentication. When the Directus public role doesn't have read access to `directus_files`, all images served via `next/image` break silently with 403 Forbidden — the most common integration gotcha.
**Fix:** Added `access_token` parameter to the helper function. Added a table documenting three authentication approaches (token in URL, public role, API route proxy) with guidance on when to use each.
**Root cause:** The skill assumed Directus files are publicly accessible by default. In practice, most Directus instances require authentication for file access.
**Severity:** Major
