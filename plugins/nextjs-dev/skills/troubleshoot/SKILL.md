---
name: troubleshoot
description: Next.js common errors, debugging techniques, and solutions. This skill should be used when the user asks about "Next.js errors", "hydration error", "Next.js not working", "build errors", "debug Next.js", "'use client' errors", "deployment issues", or encounters problems during Next.js development.
---

# Troubleshooting Next.js

Diagnostics and fixes for common Next.js issues. Start with the quick diagnostics checklist, then check the categorized error tables.

## Quick Diagnostics Checklist

1. **Check Next.js version**: `npx next --version` — ensure 14+ for stable App Router
2. **Check Node.js version**: `node -v` — ensure 20+ for Next.js 16
3. **Clear cache**: `rm -rf .next && npm run dev`
4. **Check TypeScript**: `npx tsc --noEmit` — catch type errors early
5. **Check console**: Both browser console and terminal for error messages
6. **Check MCP**: If using `next-devtools-mcp`, call `nextjs_call` with `get_errors`

## Hydration Errors

The most common Next.js issue. Occurs when server-rendered HTML doesn't match client-rendered output.

| Error | Cause | Fix |
|-------|-------|-----|
| "Text content does not match" | Different text on server vs client | Avoid `Date.now()`, `Math.random()` in Server Components. Use `useEffect` for client-only values |
| "Expected server HTML to contain a matching `<div>`" | DOM structure mismatch | Check for `<p>` inside `<p>`, `<div>` inside `<p>`, or conditional rendering based on `window` |
| "Hydration failed because the initial UI does not match" | Browser extensions or invalid HTML nesting | Validate HTML nesting. Suppress specific elements with `suppressHydrationWarning` |

### Common Hydration Causes

```tsx
// BAD: Different output on server vs client
export default function Clock() {
  return <p>Time: {new Date().toLocaleTimeString()}</p>
}

// GOOD: Use client-only rendering for dynamic values
'use client'
import { useState, useEffect } from 'react'

export default function Clock() {
  const [time, setTime] = useState<string>()
  useEffect(() => {
    setTime(new Date().toLocaleTimeString())
  }, [])
  return <p>Time: {time ?? 'Loading...'}</p>
}
```

```tsx
// BAD: Checking window in render
export default function Component() {
  const isDesktop = window.innerWidth > 768  // Fails on server
  return isDesktop ? <Desktop /> : <Mobile />
}

// GOOD: Use CSS media queries or useEffect
'use client'
import { useState, useEffect } from 'react'

export default function Component() {
  const [isDesktop, setIsDesktop] = useState(false)
  useEffect(() => {
    setIsDesktop(window.innerWidth > 768)
  }, [])
  return isDesktop ? <Desktop /> : <Mobile />
}
```

## `'use client'` Errors

| Error | Cause | Fix |
|-------|-------|-----|
| "useState is not a function" | Using hooks in a Server Component | Add `'use client'` to the file |
| "You're importing a component that needs useState" | Importing a client library in a Server Component | Create a wrapper Client Component |
| "Event handlers cannot be passed to Client Component props from Server Components" | Passing `onClick` from Server to Client Component | Define event handlers inside the Client Component |
| "Functions cannot be passed directly to Client Components" | Trying to pass a function as props | Move the function into the Client Component or use Server Actions |

## Build Errors

| Error | Cause | Fix |
|-------|-------|-----|
| "Dynamic server usage" | Using `cookies()`, `headers()`, or `searchParams` in a statically generated page | Add `export const dynamic = 'force-dynamic'` or restructure to fetch dynamically |
| "generateStaticParams is required for dynamic routes with output: export" | Missing static params for static export | Add `generateStaticParams` or remove `output: 'export'` |
| "Module not found: Can't resolve 'fs'" | Using Node.js modules in client code | Move to Server Component or Route Handler |
| "`params` is now a Promise" | Next.js 15+ async params not awaited | `const { id } = await params` |

## Data Fetching Errors

| Error | Cause | Fix |
|-------|-------|-----|
| "async/await is not yet supported in Client Components" | Using `async` in a Client Component | Fetch in a Server Component and pass data as props, or use `use()` hook |
| "cookies was called outside a request scope" | Accessing `cookies()` at build time | Ensure it's inside a request handler (page, layout, route handler, or Server Action) |
| "Error: NEXT_REDIRECT" | `redirect()` caught in try/catch | Call `redirect()` outside try/catch blocks — it throws intentionally |
| Stale data after mutation | Cache not revalidated | Call `revalidatePath()` or `revalidateTag()` after mutations |

## Performance Issues

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Slow initial load | Large client bundle | Move components to Server Components; use `dynamic()` for heavy libraries |
| Layout shift on load | Images without dimensions | Add `width`/`height` to `<Image>` or use `fill` |
| Flash of unstyled text | External font stylesheet | Use `next/font` instead of `<link>` |
| Slow navigation | No prefetching | Ensure `<Link>` is used (auto-prefetch); check `prefetch={false}` isn't set |
| High memory in production | Memory leaks in middleware | Avoid storing state in middleware closure; check for global variable accumulation |

## Deployment Issues

### Vercel

| Issue | Fix |
|-------|-----|
| Build fails with memory error | Add `NODE_OPTIONS=--max_old_space_size=4096` to build env |
| Environment variables not available | Use `NEXT_PUBLIC_` prefix for client-side vars; redeploy after adding env vars |
| API routes timing out | Move to Edge Runtime: `export const runtime = 'edge'` or increase timeout |

### Self-Hosted (Docker/Node.js)

| Issue | Fix |
|-------|-----|
| `output: 'standalone'` not generating `server.js` | Verify config, clear `.next/`, rebuild |
| Static files not found | Copy `public/` and `.next/static/` to the standalone output |
| Port conflicts | Set `PORT` env var or use `-p` flag |
| CORS errors | Add headers in `next.config.ts` `headers()` or middleware |

## Diagnostic Commands

```bash
# Check Next.js version
npx next --version

# Full type check
npx tsc --noEmit

# Lint
npx next lint

# Clean build
rm -rf .next node_modules/.cache && npm run build

# Check bundle
ANALYZE=true npm run build

# Debug with verbose output
NODE_OPTIONS='--inspect' next dev
```

## When to Escalate

- **Persistent 500 errors**: Check server logs, not just browser. Use `next-devtools-mcp` `get_errors` tool
- **Memory leaks**: Profile with `--inspect` flag and Chrome DevTools
- **MCP connection failures**: Verify Next.js 16+, dev server running, and `next-devtools-mcp` in `.mcp.json`
- **Webpack/Turbopack crashes**: Check for incompatible packages, try `--turbopack` flag or disable it
- **Deployment-specific bugs**: Test with `next build && next start` locally before deploying
