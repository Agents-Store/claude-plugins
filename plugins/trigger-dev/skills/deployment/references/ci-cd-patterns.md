# CI/CD Patterns

## GitHub Actions — Cloud

```yaml
name: Deploy Trigger.dev
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm ci
      - name: Deploy to production
        run: npx trigger.dev@latest deploy --env production
        env:
          TRIGGER_ACCESS_TOKEN: ${{ secrets.TRIGGER_ACCESS_TOKEN }}
```

## GitHub Actions — Self-Hosted

```yaml
name: Deploy Trigger.dev (Self-Hosted)
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm ci
      - name: Deploy to production
        run: npx trigger.dev@latest deploy --env production
        env:
          TRIGGER_ACCESS_TOKEN: ${{ secrets.TRIGGER_ACCESS_TOKEN }}
          TRIGGER_API_URL: ${{ secrets.TRIGGER_API_URL }}
```

## GitHub Actions — Staging + Production

```yaml
name: Deploy Trigger.dev
on:
  push:
    branches:
      - main
      - develop

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm ci
      - name: Deploy to staging
        if: github.ref == 'refs/heads/develop'
        run: npx trigger.dev@latest deploy --env staging
        env:
          TRIGGER_ACCESS_TOKEN: ${{ secrets.TRIGGER_ACCESS_TOKEN }}
          TRIGGER_API_URL: ${{ secrets.TRIGGER_API_URL }}
      - name: Deploy to production
        if: github.ref == 'refs/heads/main'
        run: npx trigger.dev@latest deploy --env production
        env:
          TRIGGER_ACCESS_TOKEN: ${{ secrets.TRIGGER_ACCESS_TOKEN }}
          TRIGGER_API_URL: ${{ secrets.TRIGGER_API_URL }}
```

## GitLab CI

```yaml
deploy-trigger:
  stage: deploy
  image: node:20
  script:
    - npm ci
    - npx trigger.dev@latest deploy --env production
  variables:
    TRIGGER_ACCESS_TOKEN: $TRIGGER_ACCESS_TOKEN
    TRIGGER_API_URL: $TRIGGER_API_URL
  only:
    - main
```

## Generic CI

For any CI system, set these environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `TRIGGER_ACCESS_TOKEN` | Yes | Personal access token (tr_pat_xxx) |
| `TRIGGER_API_URL` | Self-hosted only | Your instance URL |

Then run:

```bash
npx trigger.dev@latest deploy --env production
```
