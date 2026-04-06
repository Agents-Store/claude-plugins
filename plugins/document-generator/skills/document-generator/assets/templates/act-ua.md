# Act of Completed Works Template (PDF)

A formal act of completed works (services). Includes a services table, totals, confirmation of no claims, and signature blocks for both parties. Commonly used in Ukrainian business but adaptable to any locale.

## Required Fields

```
actNumber: "ACT-001"
date: "March 19, 2026"
city: "Kyiv"

contractor:               # Service provider
  name: "FOP Ivanenko I.I."
  representative: "Ivanenko I.I."
  title: "Individual Entrepreneur"
  reg: "Tax ID: 1234567890"
  address: "1 Khreshchatyk St, Kyiv"

customer:                 # Client
  name: "Client Company LLC"
  representative: "Petrenko P.P."
  title: "Director"
  reg: "Reg. No.: 98765432"
  address: "50 Main St, Kyiv"

services:
  - description: "Service or work description"
    unit: "hrs"           # hrs / pcs / service / month
    quantity: 40
    unitPrice: 1500
    total: 60000
```

## Optional Fields

```
contractRef: "Contract No. 001 dated 01.01.2026"    # reference to contract
vatRate: 0                                            # VAT rate in %
currencySymbol: "$"                                   # currency symbol
totalAmount: 60000                                    # auto-calculated if omitted
notes: "Additional notes or conditions."
```

## JSON Input Structure

```json
{
  "type": "act",
  "engine": "puppeteer",
  "outputPath": "./act_act-001_2026-03-19.pdf",
  "template": {
    "currencySymbol": "$",
    "styling": {
      "primaryColor": "#1E293B",
      "accentColor": "#1E3A5F"
    }
  },
  "data": {
    "actNumber": "ACT-001/2026",
    "date": "March 19, 2026",
    "city": "Kyiv",
    "contractRef": "Contract No. 001/2026 dated March 1, 2026",
    "currencySymbol": "$",
    "vatRate": 0,
    "contractor": {
      "name": "FOP Ivanenko Ivan Ivanovych",
      "representative": "Ivanenko I.I.",
      "title": "Individual Entrepreneur",
      "reg": "Tax ID: 1234567890",
      "address": "55 Velyka Vasylkivska St, Kyiv, 03150"
    },
    "customer": {
      "name": "Client Company LLC",
      "representative": "Petrenko P.P.",
      "title": "Director",
      "reg": "Reg. No.: 98765432",
      "address": "26 Peremohy Ave, Kyiv, 03055"
    },
    "services": [
      {
        "description": "Frontend web application development",
        "unit": "hrs",
        "quantity": 40,
        "unitPrice": 1500,
        "total": 60000
      },
      {
        "description": "Technical support and testing",
        "unit": "hrs",
        "quantity": 10,
        "unitPrice": 1000,
        "total": 10000
      }
    ],
    "totalAmount": 70000,
    "notes": "All work completed in full and within the agreed timeline."
  }
}
```

## Common Units of Measure

| Abbreviation | Meaning |
|-------------|---------|
| hrs | Hours |
| pcs | Pieces / Units |
| service | Service (one-time) |
| month | Month |
| project | Project (lump sum) |

## VAT Notes

- Individual entrepreneur (simplified tax, no VAT): `"vatRate": 0`
- VAT payer: `"vatRate": 20` — VAT amount will be calculated and shown as a separate line
