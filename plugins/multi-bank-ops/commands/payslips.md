---
description: Manage payslips — upload, send to employees, check status, generate PDF
allowed-tools: ["Bash", "Read", "Write", "Glob", "Grep", "mcp__monobank__*", "mcp__privatbank__*"]
argument-hint: <upload|send|status|pdf|delete> <period> [identification]
---

# Payslips (Розрахункові листки)

Manage employee payslips through bank MCP tools.

## Arguments
Format: `<action> <period> [identification]`
- `upload <YYYY-MM>` — upload payslips for a period
- `send <YYYY-MM>` — send payslips to employees' mobile apps
- `status <YYYY-MM>` — check import status
- `pdf <YYYY-MM> <identification>` — generate PDF for specific employee
- `delete <YYYY-MM>` — delete import for a period

Parse from "$ARGUMENTS". If empty, show available actions and ask for period.

## Process

### Action: upload

1. **Discover payslip tools** (keywords: `payslip`, `upload`, `import`, `batch`)
2. **Collect payslip data:**
   Ask user for source — JSON file path, CSV file path, or manual input.

   Each employee entry needs:
   - `identification` — ІПН (tax ID)
   - `attributes` — array of salary components:
     ```
     { attributeName: "Базова зарплата", value: "50000", attributeSuffix: "грн", sortOrder: 1 }
     { attributeName: "Премія", value: "5000", attributeSuffix: "грн", sortOrder: 2 }
     { attributeName: "ПДФО (18%)", value: "-9900", attributeSuffix: "грн", sortOrder: 3 }
     { attributeName: "До виплати", value: "45100", attributeSuffix: "грн", sortOrder: 4 }
     ```

3. **Validate:**
   - Period format: YYYY-MM
   - Max 1000 employees per batch
   - Each employee must have identification + at least 1 attribute

4. **Confirm:**
   ```
   Період:       2026-03
   Працівників:  45
   ```
   Ask: "Завантажити розрахункові листки?"

5. **Upload and report** — call batch upload MCP tool

### Action: send

1. **Confirm period** with user
2. **Warn:** "Розрахункові листки будуть надіслані всім працівникам у мобільний додаток"
3. Call send-to-mobile MCP tool with period
4. Report result

### Action: status

1. Call import status MCP tool with period
2. Display: upload state, employee count, errors if any

### Action: pdf

1. Call PDF generation MCP tool with identification and period
2. Save or display the generated PDF
3. Note: identification = ІПН of the employee

### Action: delete

1. **Confirm:** "Видалити всі розрахункові листки за {period}? Цю дію не можна скасувати."
2. Call delete import MCP tool with period
3. Report result

## PrivatBank Paysheets

PrivatBank uses a different paysheet model (journal-based via SFTP, not batch upload).
Discover paysheet tools with keywords: `paysheet`, `journal`, `savePaysheetFiles`.

If PrivatBank paysheet tools are detected:
- `getPaysheetJournal` — list payslip projects
- `savePaysheetFiles` — save uploaded files to SFTP

The workflow differs from Monobank — check available tools and adapt accordingly.

## Safety

- **Mask ІПН** in output — show only last 4 digits
- **Confirm before send** — payslips go to all employees at once
- **Confirm before delete** — irreversible
- **Validate period format** — must be YYYY-MM
