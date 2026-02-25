# trigger.config.ts Reference

Configuration file reference for Trigger.dev projects.

## Minimal Configuration

```typescript
import { defineConfig } from "@trigger.dev/sdk/v3";

export default defineConfig({
  project: "proj_xxx",
});
```

## Full Configuration

```typescript
import { defineConfig } from "@trigger.dev/sdk/v3";
import { prismaExtension } from "@trigger.dev/build/extensions/prisma";
import { syncEnvVars } from "@trigger.dev/build/extensions";

export default defineConfig({
  project: "proj_xxx",
  runtime: "node",             // "node" | "bun"
  logLevel: "info",            // "debug" | "info" | "warn" | "error"
  maxDuration: 300,            // Default max duration in seconds
  retries: {
    enabledInDev: false,       // Disable retries in dev
    default: {
      maxAttempts: 3,
      factor: 2,
      minTimeoutInMs: 1000,
      maxTimeoutInMs: 30000,
    },
  },
  dirs: ["src/trigger"],       // Directories to scan for tasks
  machine: "small-1x",        // Default machine preset
  build: {
    extensions: [
      prismaExtension({ version: "5.x" }),
      syncEnvVars(),
    ],
  },
});
```

## Machine Presets

| Preset | vCPUs | Memory | Use Case |
|--------|-------|--------|----------|
| micro | 0.25 | 0.25 GB | Simple tasks |
| small-1x | 0.5 | 0.5 GB | API calls |
| small-2x | 1 | 1 GB | Data processing |
| medium-1x | 1 | 2 GB | AI inference |
| medium-2x | 2 | 4 GB | Heavy processing |
| large-1x | 2 | 8 GB | Large datasets |
| large-2x | 4 | 8 GB | ML training |

## Build Extensions

### Prisma
```typescript
import { prismaExtension } from "@trigger.dev/build/extensions/prisma";
prismaExtension({ version: "5.x", schema: "prisma/schema.prisma" })
```

### Puppeteer
```typescript
import { puppeteer } from "@trigger.dev/build/extensions/puppeteer";
puppeteer()
```

### FFmpeg
```typescript
import { ffmpeg } from "@trigger.dev/build/extensions/ffmpeg";
ffmpeg()
```

### Python
```typescript
import { pythonExtension } from "@trigger.dev/build/extensions/python";
pythonExtension({ requirements: ["numpy", "pandas"] })
```

### Sync Environment Variables
```typescript
import { syncEnvVars } from "@trigger.dev/build/extensions";
syncEnvVars()
```

### Additional Packages
```typescript
import { additionalPackages } from "@trigger.dev/build/extensions";
additionalPackages({ packages: ["sharp", "canvas"] })
```

### Additional Files
```typescript
import { additionalFiles } from "@trigger.dev/build/extensions";
additionalFiles({ files: ["templates/**/*", "data/*.json"] })
```

Search docs for all available extensions:
```
Tool: tds-search_docs
Input: {"query": "build extensions list all available"}
```
