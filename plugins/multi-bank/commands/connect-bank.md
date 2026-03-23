---
description: Connect a bank account — verify MCP server connectivity
allowed-tools: ["Bash", "Read", "Glob", "mcp__monobank__*", "mcp__privatbank__*"]
argument-hint: <bank-name>
---

# Connect Bank

Verify connectivity to a bank's MCP server and list available accounts.

## Arguments
Format: `<bank-name>`
- bank-name: "monobank" or "privatbank"

Parse from "$ARGUMENTS".

## Process

1. **Verify MCP server:**
   - List available MCP tools to check if the bank's server is connected
   - If no tools found for the bank, inform user to configure .mcp.json with the correct URL

2. **Fetch accounts:**
   - Call the bank's account listing MCP tool
   - Display available accounts with masked numbers

3. **Confirm connection:**
   ```
   Monobank connected!
   Accounts found:
     • Чорна картка ****1234  Balance: ₴15 432,10
     • Біла картка ****5678   Balance: ₴8 200,00
   ```

4. **If MCP server not configured:**
   ```
   Monobank MCP server not found.
   Configure .mcp.json in the plugin directory:
   {
     "mcpServers": {
       "monobank": {
         "type": "http",
         "url": "https://your-mcp-server.example.com/mcp/monobank"
       }
     }
   }
   ```

## Example Usage
```
/connect-bank monobank
/connect-bank privatbank
```
