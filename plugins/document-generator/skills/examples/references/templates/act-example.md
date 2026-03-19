# Act of Completed Works — JSON Examples

## Minimal Example (3 service rows, no VAT)

```json
{
  "type": "act",
  "engine": "puppeteer",
  "outputPath": "./act_akt-001_2026-03-19.pdf",
  "template": { "currencySymbol": "₴" },
  "data": {
    "actNumber": "АКТ-001",
    "date": "19 березня 2026 р.",
    "city": "Київ",
    "contractor": {
      "name": "ФОП Іваненко Іван Іванович",
      "representative": "Іваненко І.І.",
      "title": "ФОП"
    },
    "customer": {
      "name": "ТОВ «Компанія»",
      "representative": "Петренко П.П.",
      "title": "Директор"
    },
    "services": [
      { "description": "Розробка веб-сайту", "unit": "послуга", "quantity": 1, "unitPrice": 50000, "total": 50000 },
      { "description": "SEO-оптимізація", "unit": "год", "quantity": 10, "unitPrice": 800, "total": 8000 },
      { "description": "Технічна підтримка", "unit": "год", "quantity": 5, "unitPrice": 600, "total": 3000 }
    ],
    "totalAmount": 61000,
    "vatRate": 0
  }
}
```

---

## Full Example (5 rows, VAT 20%, contract reference)

```json
{
  "type": "act",
  "engine": "puppeteer",
  "outputPath": "./act_akt-002-2026_2026-03-31.pdf",
  "template": {
    "currencySymbol": "₴",
    "styling": {
      "primaryColor": "#1E293B",
      "accentColor": "#1E3A5F",
      "textColor": "#1E293B",
      "mutedColor": "#64748B",
      "borderColor": "#E2E8F0",
      "backgroundColor": "#F8FAFC"
    }
  },
  "data": {
    "actNumber": "АКТ-002/2026",
    "date": "31 березня 2026 р.",
    "city": "Київ",
    "contractRef": "Договору №002/2026 від 01 лютого 2026 р.",
    "currencySymbol": "₴",
    "vatRate": 20,
    "contractor": {
      "name": "ТОВ «Розробка Плюс»",
      "representative": "Сидоренко О.В.",
      "title": "Директор",
      "reg": "ЄДРПОУ: 12345678",
      "address": "вул. Хрещатик, 1, м. Київ, 01001"
    },
    "customer": {
      "name": "ТОВ «Великий Замовник»",
      "representative": "Коваленко М.І.",
      "title": "Генеральний директор",
      "reg": "ЄДРПОУ: 87654321",
      "address": "пр. Перемоги, 100, м. Київ, 03055"
    },
    "services": [
      { "description": "Аналіз вимог та технічне завдання", "unit": "год", "quantity": 20, "unitPrice": 1200, "total": 24000 },
      { "description": "Розробка backend (Node.js, PostgreSQL)", "unit": "год", "quantity": 80, "unitPrice": 1500, "total": 120000 },
      { "description": "Розробка frontend (React)", "unit": "год", "quantity": 60, "unitPrice": 1400, "total": 84000 },
      { "description": "Тестування та QA", "unit": "год", "quantity": 20, "unitPrice": 1000, "total": 20000 },
      { "description": "Розгортання та документація", "unit": "год", "quantity": 10, "unitPrice": 1200, "total": 12000 }
    ],
    "totalAmount": 260000,
    "notes": "Всі роботи виконані відповідно до технічного завдання. Зауважень від замовника немає."
  }
}
```

**Calculated totals for full example:**
- Subtotal: ₴260,000
- VAT (20%): ₴52,000
- Grand total: ₴312,000
