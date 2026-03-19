# Invoice Template — With Logo (PDF)

Invoice variant that includes a company logo in the header. Uses the same corporate layout as the standard invoice, but with the logo displayed above the company name.

## Logo support

Two ways to provide a logo:

**Option 1 — Base64 encoded (recommended, works offline):**
```json
"companyInfo": {
  "name": "Acme Ltd.",
  "logoBase64": "iVBORw0KGgoAAAANSUhEUg..."
}
```

**Option 2 — URL (requires internet during PDF generation):**
```json
"companyInfo": {
  "name": "Acme Ltd.",
  "logoUrl": "https://yoursite.com/logo.png"
}
```

To convert a logo file to base64 (run in terminal):
```bash
base64 -i logo.png | tr -d '\n'
```

## Required fields

Same as `invoice-standard.md`, plus one of:
- `companyInfo.logoBase64` — base64 encoded PNG/JPEG image
- `companyInfo.logoUrl` — URL to logo image

## JSON input structure

```json
{
  "type": "invoice",
  "engine": "puppeteer",
  "outputPath": "./invoice_inv-001_2026-03-19.pdf",
  "template": {
    "currencySymbol": "₴",
    "styling": {
      "primaryColor": "#1E3A5F",
      "accentColor": "#2563EB"
    }
  },
  "data": {
    "invoiceNumber": "INV-001",
    "date": "19 березня 2026",
    "dueDate": "2 квітня 2026",
    "companyInfo": {
      "name": "ФОП Іваненко І.І.",
      "address": "м. Київ, вул. Хрещатик, 1",
      "phone": "+380 67 000 0000",
      "email": "info@company.ua",
      "logoBase64": "<base64 string here>"
    },
    "recipientInfo": {
      "name": "ТОВ «Замовник»",
      "address": "м. Київ, вул. Велика Васильківська, 50",
      "email": "pay@zamovnyk.ua"
    },
    "items": [
      {
        "description": "Розробка сайту",
        "quantity": 1,
        "unitPrice": 30000,
        "total": 30000
      }
    ],
    "currencySymbol": "₴",
    "paymentDetails": {
      "bank": "ПриватБанк",
      "accountName": "ФОП Іваненко І.І.",
      "iban": "UA21 3006 5000 0000 0026 2001 0000 1"
    },
    "notes": "Оплата протягом 5 робочих днів."
  }
}
```

## Logo size

The logo is automatically constrained to `max-height: 56px, max-width: 160px`. Use a PNG with transparent background for best results.
