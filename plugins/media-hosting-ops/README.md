# media-hosting-ops

Media hosting operations plugin for Agents Store. Upload images by public URL to MinIO-based media hosting.

## Skills

| Skill | Description |
|-------|-------------|
| `upload-image` | Upload an image from a public URL to MinIO media hosting |
| `examples` | Scenario walkthroughs for common upload patterns |

## Agent

- **media-assistant** — Helps upload images and returns hosted URLs

## Prerequisites

The `mcpware-dev-tools` MCP server must be connected. This plugin provides knowledge about using the `uploadImageToMinio` tool — it does not bundle its own MCP server.
