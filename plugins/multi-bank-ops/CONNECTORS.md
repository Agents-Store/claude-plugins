# Connectors

## Bank services (broadcast strategy)

This plugin uses the **BROADCAST** pattern: it queries **ALL** connected bank MCP servers and combines results into a unified view.

| .mcp.json key | Service     | Country  |
|---------------|-------------|----------|
| monobank      | Monobank    | Ukraine  |
| privatbank    | PrivatBank  | Ukraine  |

Add more banks by adding their MCP server to `.mcp.json`.

## Strategy: BROADCAST

- **Query ALL** connected banks simultaneously
- **Combine results** into a single table/view
- **Graceful degradation**: if a bank MCP server is unavailable, skip it, note the failure, and show results from the remaining banks
- **Never ask "which bank?"** — always broadcast to all connected servers

## How it works

1. Plugin discovers available MCP tools at runtime using keyword matching
2. For each connected bank, it identifies tools by domain (accounts, statements, payments, etc.)
3. Calls are made to ALL connected banks in parallel
4. Results are merged: balances combined into one table, transactions sorted chronologically
5. Failed banks are noted but don't block results from others

## Adding a new bank

1. Add the bank's MCP server to `.mcp.json`:
   ```json
   {
     "mcpServers": {
       "newbank": {
         "type": "http",
         "url": "https://your-mcp-server.example.com/mcp/newbank"
       }
     }
   }
   ```
2. The plugin will auto-discover the bank's tools using keyword matching
3. No code changes needed — the broadcast pattern handles any number of banks

## Environment variables (alternative)

Instead of hardcoding URLs, you can use environment variables:

```json
{
  "mcpServers": {
    "monobank": { "type": "http", "url": "${MONOBANK_MCP_URL}" },
    "privatbank": { "type": "http", "url": "${PRIVATBANK_MCP_URL}" }
  }
}
```

## Tool discovery by domain

The plugin identifies bank tools by matching keywords in tool names and descriptions:

| Domain | Keywords |
|--------|----------|
| Accounts | account, balance, iban |
| Statements | statement, transaction, extract |
| Payments | payment, prepare, pay |
| Salary | salary, contact, registry, maspay |
| Payslips | payslip, paysheet, import, mobile |
| E-Documents | edoc, document, journal |
| Currency | currency, rate, exchange |
| Cards | corporate, card |
