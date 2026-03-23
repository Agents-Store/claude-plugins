# Multi-Bank Account Manager

A Claude Code plugin for managing multiple Ukrainian bank accounts via MCP. Uses the **BROADCAST** architecture pattern — queries all connected banks simultaneously and combines results.

## Features

- Unified view of balances across all connected banks
- Combined transaction history with chronological sorting
- Payment preparation and tracking
- Salary project management (contacts, registries, payslips)
- Electronic document management (EDO)
- Currency exchange rates
- Budget tracking and alerts
- Encrypted local storage for sensitive data
- CSV/PDF report export
- Broadcast pattern: query all banks, never ask "which one?"

## Installation

```bash
claude --plugin-dir /path/to/multi-bank
```

Or copy the `multi-bank` directory to your project's `.claude-plugin/` folder.

## MCP Server Configuration

Edit `.mcp.json` and replace placeholder URLs with your actual MCP server endpoints:

```json
{
  "mcpServers": {
    "monobank": {
      "type": "http",
      "url": "https://your-mcp-server.example.com/mcp/monobank"
    },
    "privatbank": {
      "type": "http",
      "url": "https://your-mcp-server.example.com/mcp/privatbank"
    }
  }
}
```

Or use environment variables:

```json
{
  "mcpServers": {
    "monobank": { "type": "http", "url": "${MONOBANK_MCP_URL}" },
    "privatbank": { "type": "http", "url": "${PRIVATBANK_MCP_URL}" }
  }
}
```

**IMPORTANT:** Never commit real MCP server URLs to the repository.

## Commands

| Command | Description |
|---------|-------------|
| `/balances` | Show balances across all connected banks |
| `/transactions` | List transactions for a period |
| `/sync-accounts` | Force-sync all accounts via MCP |
| `/connect-bank` | Verify MCP server connectivity |
| `/set-budget` | Set a spending budget with alert thresholds |
| `/budget-status` | Show budget utilization and alerts |
| `/export-report` | Export financial report as CSV or PDF |
| `/prepare-payment` | Prepare a payment via bank MCP |
| `/salary-registry` | Manage salary registries |
| `/payslips` | Manage payslips (upload, send, PDF) |
| `/edoc-journal` | Browse electronic documents (EDO) |
| `/currency-rates` | Show currency exchange rates |
| `/corporate-cards` | List corporate cards |
| `/broadcast-status` | Show broadcast system event status |

## Skills

| Skill | Description |
|-------|-------------|
| bank-balances | Unified balance view across all banks (BROADCAST) |
| bank-transactions | Merged transaction history from all banks (BROADCAST) |
| bank-reports | Financial analytics: spending by category, income/expenses, period comparison |
| bank-statements | Bank statement (виписка) for a specific account and period |
| bank-api-integration | MCP tool discovery, API domains, bank-specific formats |
| broadcast-pattern | Pub/sub architecture, event types, delivery mechanisms |
| payments | Payment preparation, tracking, budget payments |
| salary-management | Salary contacts, registries, Maspay, payslips |
| e-documents | Electronic document exchange (EDO) |
| currency-rates | Currency exchange rate queries |
| transaction-categorization | Auto-categorization with Ukrainian merchant patterns |
| budget-alerts | Budget thresholds, alert logic, periods |
| encrypted-storage | AES-256-GCM encryption for sensitive data |
| report-export | CSV/PDF report generation |
| examples | Workflow walkthroughs, architecture diagrams, scenario references |

## Supported Banks

| Bank | Domains |
|------|---------|
| Monobank | Accounts, Statements, Payments, Salary, Payslips |
| PrivatBank | Accounts, Statements, Payments, Salary (Maspay), Paysheets, EDO, Currency Rates, Corporate Cards |

The plugin works with **any** MCP server for these banks, regardless of tool naming conventions. Tools are discovered dynamically at runtime.

## Architecture

See [CONNECTORS.md](CONNECTORS.md) for the BROADCAST strategy documentation.
See [assets/architecture-diagram.md](assets/architecture-diagram.md) for the system architecture diagram.

## Security

- All financial data encrypted at rest (AES-256-GCM)
- Account numbers always masked (****1234)
- No real credentials or URLs stored in the repository
- Rate limiting with exponential backoff
- Confirmation required before payments and batch operations

## Dependencies

```bash
cd /path/to/multi-bank && npm install
```

Only `pdfkit` is required (for PDF report generation). CSV and encryption use Node.js built-ins.
