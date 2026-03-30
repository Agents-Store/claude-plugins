# Environment Setup

Complete guide to environment variables and self-hosted configuration.

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `TRIGGER_SECRET_KEY` | Per-environment secret key | `tr_dev_xxx` or `tr_prod_xxx` |

### Self-Hosted

| Variable | Description | Example |
|----------|-------------|---------|
| `TRIGGER_API_URL` | Self-hosted instance URL | `https://trigger.example.com` |
| `TRIGGER_ACCESS_TOKEN` | Personal access token (CI/CD) | `tr_pat_xxx` |
| `TRIGGER_PREVIEW_BRANCH` | Preview branch name (optional) | `feature/my-task` |

### Key Formats

| Format | Environment | Usage |
|--------|-------------|-------|
| `tr_dev_xxx` | Development | Local dev, dev environment tasks |
| `tr_prod_xxx` | Production | Production tasks |
| `tr_pat_xxx` | All environments | CI/CD, Management API |
| `tr_wgt_xxx` | Worker | Worker token for separate machine setup |

## Self-Hosted v4 Architecture

Trigger.dev v4 self-hosted has two main Docker Compose stacks:

### Webapp Stack
- **webapp** — Dashboard, API, background workers
- **PostgreSQL** — Primary database
- **Redis** — Queue and caching
- **Container Registry** — Stores deployed task images
- **MinIO** — Object storage for task packets and artifacts

### Worker Stack (Supervisor)
- **supervisor** — Manages task execution containers
- **Docker Socket Proxy** — Secure Docker access (replaces direct socket)

The v3 coordinator+provider are replaced by a single **supervisor** in v4.

## Worker Token

When running webapp and worker on separate machines:

1. First start of webapp prints the worker token in logs:
   ```
   TRIGGER_WORKER_TOKEN=tr_wgt_xxxxxxxxxxxxx
   ```
2. Set this in the worker's `.env` file
3. Restart the worker: `docker compose down && docker compose up -d`

## Docker Compose Quick Start

```bash
# Clone the repo
git clone --depth=1 https://github.com/triggerdotdev/trigger.dev
cd trigger.dev/hosting/docker

# Start webapp stack
cd webapp && docker compose up -d

# Start worker stack (same or separate machine)
cd ../worker && docker compose up -d
```

## Registry Configuration

Trigger.dev v4 uses a built-in container registry for task deployments:

```bash
# Default registry credentials (CHANGE IN PRODUCTION)
docker login -u registry-user localhost:5000
# Password: very-secure-indeed
```

Update credentials in `hosting/docker/registry/auth.htpasswd`.

## MinIO Object Storage

MinIO provides S3-compatible storage for task packets:
- UI available at port 9001
- Ensure the `packets` bucket exists
- Default credentials in webapp `.env`

## Version Locking

Pin Docker image versions in your `.env`:

```bash
TRIGGER_IMAGE_TAG=v4.0.0
```

## Telemetry Opt-Out

```yaml
services:
  webapp:
    environment:
      TRIGGER_TELEMETRY_DISABLED: 1
```

## Upgrading Self-Hosted

1. Pull new images: `docker compose pull`
2. Stop services: `docker compose down`
3. Start services: `docker compose up -d` (migrations run automatically)
4. Redeploy tasks: `npx trigger.dev@latest deploy --env production`

## SDK Configuration (programmatic)

```ts
import { configure } from "@trigger.dev/sdk";

configure({
  secretKey: process.env.TRIGGER_SECRET_KEY,
  baseURL: process.env.TRIGGER_API_URL,
});
```
