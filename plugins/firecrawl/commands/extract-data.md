---
description: Extract structured data from URLs
allowed-tools: ["mcp__firecrawl__extract_data"]
argument-hint: <url> [url2...] --schema <json-schema>
---

# Extract Data

Extract structured data from a URL using a JSON schema definition.

## Arguments
Format: `<url> [url2...] --schema <json-schema>`
- urls: One or more URLs to extract data from (required)
- --schema: JSON schema describing the data to extract (required)

Parse from "$ARGUMENTS".

## Process

1. **Extract data:**
   ```
   extract_data({
     urls: [<url>, ...],
     schema: <parsed JSON schema>
   })
   ```

2. **Display results:**
   Show extracted data in a formatted table.

## Example Usage
```
/extract-data "https://example.com/product/123" --schema '{"type":"object","properties":{"name":{"type":"string"},"price":{"type":"number"},"description":{"type":"string"}}}'
```
