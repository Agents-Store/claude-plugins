---
name: deployment
description: This skill should be used when the user wants to "deploy Directus + Next.js", "set up Docker for Directus", "deploy to Vercel", "run Directus locally with Docker", "configure Vercel deploy hooks", "set up production deployment", "auto-rebuild on content change", or needs deployment patterns for the Directus + Next.js stack.
---

# Deployment: Vercel (Production) + Docker (Local)

Deploy the Next.js frontend to Vercel and run Directus locally via Docker Compose. Automate production rebuilds when Directus content changes.

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

# Start Next.js dev server
npm run dev
```

Access points:
- Directus Admin: `http://localhost:8055`
- Next.js App: `http://localhost:3000`

### Local .env.local

```bash
NEXT_PUBLIC_DIRECTUS_URL=http://localhost:8055
DIRECTUS_ADMIN_TOKEN=your-local-static-token
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=dev-secret-change-in-production
```

Create the admin static token in Directus Admin → Settings → Access Tokens after first startup.

## Vercel Production Deployment

### Set Environment Variables

In Vercel project dashboard → Settings → Environment Variables, add:

| Variable | Value | Environment |
|----------|-------|-------------|
| `NEXT_PUBLIC_DIRECTUS_URL` | `https://cms.yourdomain.com` | Production, Preview |
| `DIRECTUS_ADMIN_TOKEN` | Your production static token | Production, Preview |
| `NEXTAUTH_URL` | `https://yourdomain.com` | Production |
| `NEXTAUTH_SECRET` | Result of `openssl rand -base64 32` | Production, Preview |

### Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Link project (first time)
vercel link

# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

Set `VERCEL_TOKEN`, `VERCEL_ORG_ID`, and `VERCEL_PROJECT_ID` in `.env.local` for CI/CD or programmatic deploys:

```bash
vercel --prod --token=$VERCEL_TOKEN
```

### next.config.ts for Production

Ensure the production Directus domain is in `images.remotePatterns`:

```typescript
const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'cms.yourdomain.com',
      },
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8055',
      },
    ],
  },
};
```

## Auto-Rebuild on Content Changes

### Vercel Deploy Hooks

1. In Vercel: project Settings → Git → Deploy Hooks → create a hook (e.g. "Directus Content Update"). Copy the hook URL.

2. In Directus: Settings → Flows → create a new Flow:
   - **Trigger**: Event Hook → `items.create`, `items.update` on content collections (e.g. `posts`, `pages`)
   - **Condition** (optional): Check `{{ $trigger.payload.status }} == "published"` to only rebuild on publish
   - **Operation**: Webhook → POST to the Vercel Deploy Hook URL

This triggers a Vercel rebuild whenever content is published in Directus.

### On-Demand ISR Revalidation

For faster updates without a full rebuild, use Next.js on-demand revalidation:

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

2. In Directus Flow: add a Webhook operation pointing to:
   ```
   https://yourdomain.com/api/revalidate?secret=YOUR_REVALIDATION_SECRET
   ```
   With body: `{ "collection": "{{ $trigger.collection }}" }`

3. Add `REVALIDATION_SECRET` to Vercel environment variables.

## Production Directus Hosting

Directus in production can run on:
- **Docker on a VPS** (DigitalOcean, Hetzner, etc.) — same docker-compose with production secrets and a reverse proxy (nginx/Caddy)
- **Directus Cloud** — managed hosting at `directus.cloud`
- **Railway / Render** — container hosting platforms

Ensure production Directus has:
- `CORS_ORIGIN` set to your Vercel domain
- A static access token for the Next.js backend
- SSL/TLS enabled (required for Vercel → Directus communication)
- File storage configured (S3, Cloudflare R2, or local with persistent volume)

## Production Checklist

- [ ] Directus running with SSL and persistent storage
- [ ] `CORS_ORIGIN` includes the production Vercel domain
- [ ] Static token created with appropriate permissions (not full admin for production)
- [ ] All environment variables set in Vercel dashboard
- [ ] `next.config.ts` `images.remotePatterns` includes the production Directus hostname
- [ ] Deploy hook configured for auto-rebuild on content changes
- [ ] ISR revalidation webhook set up for instant updates
- [ ] `NEXTAUTH_SECRET` is a strong random value (not the dev placeholder)
- [ ] Docker volumes backed up for Directus uploads
