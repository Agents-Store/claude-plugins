---
name: deployment
description: This skill should be used when the user wants to "deploy Directus + Next.js + Trigger.dev", "set up Docker for the full stack", "deploy to Vercel with trigger.dev", "run self-hosted trigger.dev locally", "deploy trigger tasks", "configure dokploy for the stack", "auto-rebuild on content change with background tasks", or needs deployment patterns for the Directus + Next.js + Trigger.dev stack.
---

# Deployment: Next.js + Directus + Self-Hosted Trigger.dev

Deploy three services together: the Next.js frontend (Vercel or Dokploy), Directus (Docker/Dokploy), and self-hosted Trigger.dev (Docker webapp + supervisor). Automate production rebuilds when Directus content changes, and deploy Trigger.dev tasks separately from the Next.js app.

## Docker Compose for Local Directus

Create `docker-compose.yml` in the project root:

```yaml
services:
  directus:
    image: directus/directus:latest
    ports:
      - '8055:8055'
    environment:
      SECRET: 'change-this-to-a-random-secret'
      ADMIN_EMAIL: 'admin@example.com'
      ADMIN_PASSWORD: 'change-this-password'
      DB_CLIENT: 'postgres'
      DB_HOST: 'postgres'
      DB_PORT: '5432'
      DB_DATABASE: 'directus'
      DB_USER: 'directus'
      DB_PASSWORD: 'directus'
      CORS_ENABLED: 'true'
      CORS_ORIGIN: 'http://localhost:3000'
      CONTENT_SECURITY_POLICY_DIRECTIVES__FRAME_SRC: 'http://localhost:3000'
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./directus/uploads:/directus/uploads
      - ./directus/extensions:/directus/extensions

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: 'directus'
      POSTGRES_USER: 'directus'
      POSTGRES_PASSWORD: 'directus'
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ['CMD-SHELL', 'pg_isready -U directus']
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

### Start Local Development

```bash
# Start Directus + PostgreSQL
docker compose up -d

# Verify Directus is running
curl http://localhost:8055/server/health

# Start the Trigger.dev dev server (watches /trigger)
npx trigger.dev@latest dev

# Start Next.js dev server (in a third terminal)
npm run dev
```

Access points:
- Directus Admin: `http://localhost:8055`
- Next.js App: `http://localhost:3000`
- Trigger.dev dashboard: whatever `TRIGGER_API_URL` points at (usually a separate self-hosted instance, not local)

### Local .env.local

```bash
NEXT_PUBLIC_DIRECTUS_URL=http://localhost:8055
DIRECTUS_ADMIN_TOKEN=your-local-static-token
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=dev-secret-change-in-production
TRIGGER_SECRET_KEY=tr_dev_local_or_shared_dev_env_secret
TRIGGER_API_URL=https://trigger.your-domain.com
TRIGGER_PROJECT_REF=proj_xxxxxxxxxxx
```

Create the Directus admin static token after first startup. Re-use a shared dev env secret from the self-hosted Trigger.dev dashboard — local dev workloads show up in the **development** environment.

## Next.js Production Deployment

### Option A: Vercel

#### Set Environment Variables

In Vercel project dashboard → Settings → Environment Variables, add:

| Variable | Value | Environment |
|----------|-------|-------------|
| `NEXT_PUBLIC_DIRECTUS_URL` | `https://cms.yourdomain.com` | Production, Preview |
| `DIRECTUS_ADMIN_TOKEN` | Production static token | Production, Preview |
| `NEXTAUTH_URL` | `https://yourdomain.com` | Production |
| `NEXTAUTH_SECRET` | Result of `openssl rand -base64 32` | Production, Preview |
| `REVALIDATION_SECRET` | Random secret | Production, Preview |
| `TRIGGER_SECRET_KEY` | Production env secret key `tr_prod_xxx` | Production |
| `TRIGGER_SECRET_KEY` | Staging env secret key `tr_dev_xxx` | Preview |
| `TRIGGER_API_URL` | `https://trigger.your-domain.com` | Production, Preview |
| `TRIGGER_PROJECT_REF` | `proj_xxxxx` | Production, Preview |

#### Deploy via Vercel CLI

```bash
npm i -g vercel
vercel link
vercel          # preview
vercel --prod   # production
```

#### syncVercelEnvVars Build Extension (Optional)

Trigger.dev can automatically sync Vercel env vars so deployed tasks pick up the same values the Next.js app uses. In `trigger.config.ts`:

```typescript
import { defineConfig } from '@trigger.dev/sdk/v3';
import { syncVercelEnvVars } from '@trigger.dev/build/extensions/core';

export default defineConfig({
  project: process.env.TRIGGER_PROJECT_REF!,
  runtime: 'node',
  dirs: ['./trigger'],
  build: {
    extensions: [syncVercelEnvVars()],
  },
});
```

Set `VERCEL_ACCESS_TOKEN`, `VERCEL_PROJECT_ID`, and `VERCEL_TEAM_ID` in the Trigger.dev project's environment variables page — then `npx trigger.dev@latest deploy` pulls Vercel env vars into the task runtime.

### Option B: Dokploy (Self-Hosted)

If you're already running Directus and Trigger.dev on a self-hosted Dokploy instance, deploy Next.js there too for a fully on-prem stack. See the `dokploy-dev` plugin for application creation, domain binding, and auto-deploy-on-push. Set the same env vars listed above in Dokploy's application environment page.

### next.config.ts for Production

Ensure the production Directus domain is in `images.remotePatterns`:

```typescript
const nextConfig = {
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: 'cms.yourdomain.com' },
      { protocol: 'http', hostname: 'localhost', port: '8055' },
    ],
  },
};
```

## Deploying Trigger.dev Tasks

Trigger.dev tasks deploy **separately** from the Next.js app. The task code lives in `/trigger/` and runs on the Trigger.dev platform — not on Vercel.

### Production Deploy

```bash
# Deploy to the production environment on the self-hosted instance
npx trigger.dev@latest deploy --self-hosted --profile prod
```

The CLI reads `trigger.config.ts`, bundles everything under `/trigger/`, pushes the image to the self-hosted registry, and the supervisor spins up task workers.

Required for this command to succeed:
- `TRIGGER_API_URL` set in the environment
- Authenticated via `npx trigger.dev@latest login --api-url $TRIGGER_API_URL` OR a Personal Access Token in `TRIGGER_ACCESS_TOKEN`
- The self-hosted registry reachable from the machine running the deploy

### CI/CD (GitHub Actions)

```yaml
# .github/workflows/trigger-deploy.yml
name: Deploy Trigger.dev tasks
on:
  push:
    branches: [main]
    paths:
      - 'trigger/**'
      - 'trigger.config.ts'
      - 'package.json'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npx trigger.dev@latest deploy --self-hosted
        env:
          TRIGGER_ACCESS_TOKEN: ${{ secrets.TRIGGER_ACCESS_TOKEN }}
          TRIGGER_API_URL: ${{ secrets.TRIGGER_API_URL }}
```

**Important:** `TRIGGER_ACCESS_TOKEN` in CI must be a Personal Access Token (`tr_pat_...`), not an environment secret key. Create it in the Trigger.dev dashboard → Personal Access Tokens. The PAT is what lets the deploy command push new versions.

### Environment Variables for Deployed Tasks

Set environment variables that tasks need (e.g. `DIRECTUS_ADMIN_TOKEN`, `NEXT_PUBLIC_DIRECTUS_URL`, third-party API keys) in the Trigger.dev dashboard:

- Go to the project → Environment Variables
- Add each variable per environment (development / staging / production)
- Deployed tasks read them via `process.env.*` inside the `run()` function

Alternatively, use the `syncVercelEnvVars` build extension (see Option A above) to pull from Vercel automatically.

## Self-Hosted Trigger.dev Infrastructure

The Trigger.dev webapp + supervisor run on your own server. For the compose files, network topology, and update procedure, **defer to the `trigger-dev` plugin's `deployment` skill** — do not re-derive that content here. This stack plugin only covers integration with a self-hosted instance that is already running.

A typical self-hosted setup:
- `webapp` container (Next.js app serving the dashboard + API)
- `supervisor` container (orchestrates task workers)
- PostgreSQL for the platform's state
- Redis for the job queue
- Docker registry for task deploy images (self-hosted via `registry:2` or a managed one)

Run all of the above via Dokploy for a clean HTTPS-terminated setup — the `dokploy-dev` plugin covers the application/service creation flow.

## Auto-Rebuild on Content Changes

### Vercel Deploy Hooks (full rebuild)

1. In Vercel: project Settings → Git → Deploy Hooks → create a hook (e.g. "Directus Content Update"). Copy the hook URL.
2. In Directus: Settings → Flows → create a new Flow:
   - **Trigger**: Event Hook → `items.create`, `items.update` on content collections
   - **Condition** (optional): `{{ $trigger.payload.status }} == "published"`
   - **Operation**: Webhook → POST to the Vercel Deploy Hook URL

### On-Demand ISR Revalidation (recommended — faster)

1. Create `app/api/revalidate/route.ts`:

```typescript
import { revalidateTag } from 'next/cache';
import { NextRequest } from 'next/server';

export async function POST(request: NextRequest) {
  const secret = request.nextUrl.searchParams.get('secret');
  if (secret !== process.env.REVALIDATION_SECRET) {
    return Response.json({ error: 'Invalid secret' }, { status: 401 });
  }
  const body = await request.json();
  const collection = body.collection || body.payload?.collection;
  if (collection) {
    revalidateTag(collection);
    return Response.json({ revalidated: true, collection });
  }
  return Response.json({ error: 'No collection specified' }, { status: 400 });
}
```

2. In Directus Flow: Webhook operation pointing to:
   ```
   https://yourdomain.com/api/revalidate?secret=YOUR_REVALIDATION_SECRET
   ```
   Body: `{ "collection": "{{ $trigger.collection }}" }`

3. Add `REVALIDATION_SECRET` to Vercel/Dokploy environment variables.

### Trigger Task → Revalidate

When a Trigger.dev task mutates Directus (AI enrichment, scheduled sync), the task itself should POST to `/api/revalidate` to invalidate the affected routes:

```typescript
// inside a Trigger task's run() function
await fetch(`${process.env.NEXT_PUBLIC_SITE_URL}/api/revalidate?secret=${process.env.REVALIDATION_SECRET}`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ collection: 'posts' }),
});
```

This closes the loop: task writes → revalidation → users see fresh content.

## Production Checklist

- [ ] Directus running with SSL and persistent storage
- [ ] `CORS_ORIGIN` on Directus includes the production Next.js domain
- [ ] Directus static token created with appropriate permissions (not full admin)
- [ ] All Next.js env vars set in Vercel/Dokploy dashboard (including 3 Trigger vars)
- [ ] `next.config.ts` `images.remotePatterns` includes the production Directus hostname
- [ ] Deploy hook OR `/api/revalidate` configured for content-change rebuilds
- [ ] Self-hosted Trigger.dev webapp + supervisor running (separate infra)
- [ ] `TRIGGER_ACCESS_TOKEN` (PAT) stored as a CI secret for task deploys
- [ ] Task env vars set in Trigger.dev dashboard (Directus URL, admin token, revalidation secret, any third-party keys)
- [ ] Route handlers that call `tasks.trigger()` have `export const dynamic = 'force-dynamic'`
- [ ] Scheduled tasks attached to production environment in the Trigger.dev dashboard
- [ ] `NEXTAUTH_SECRET` is a strong random value (not the dev placeholder)
- [ ] Docker volumes backed up for Directus uploads AND the Trigger.dev postgres/redis state
