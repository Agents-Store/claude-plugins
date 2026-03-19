# Act of Completed Works — Workflow Example

Step-by-step walkthrough: user requests an act → classify → gather data → build JSON → generate PDF → deliver.

---

## User Request

> "Зроби акт виконаних робіт за березень. Виконавець — ФОП Іваненко, замовник — ТОВ Клієнт."

---

## Step 1: CLASSIFY

Keywords: "акт виконаних робіт" → **act** type, default format **PDF**.

---

## Step 2: GATHER

Ask the user for required data:

```
Збираю дані для акта:

1. Номер акта: АКТ-003/2026
2. Дата: 31 березня 2026 р.
3. Місто: Київ
4. Посилання на договір: Договір №001/2026 від 01.01.2026

Виконавець:
- Назва: ФОП Іваненко Іван Іванович
- Представник: Іваненко І.І.
- Роль: Фізична особа-підприємець
- ІПН: 1234567890

Замовник:
- Назва: ТОВ «Клієнт»
- Представник: Петренко П.П.
- Роль: Директор
- ЄДРПОУ: 98765432

Послуги:
1. Розробка API (backend), 60 год × 1 500 ₴ = 90 000 ₴
2. Технічна підтримка, 10 год × 800 ₴ = 8 000 ₴

ПДВ: 0% (ФОП на єдиному податку)
Валюта: ₴
```

---

## Step 3: SELECT

| Type | Format | Engine | Script |
|------|--------|--------|--------|
| act | PDF | puppeteer | `generate_pdf.js` |

---

## Step 4: BUILD JSON

Read template:
```bash
cat <plugin_dir>/templates/act_template.json
```

Build `.doc_input.json`:
```json
{
  "type": "act",
  "engine": "puppeteer",
  "outputPath": "/Users/ivan/Documents/act_akt-003-2026_2026-03-31.pdf",
  "template": {
    "currencySymbol": "₴",
    "styling": {
      "primaryColor": "#1E293B",
      "accentColor": "#1E3A5F"
    }
  },
  "data": {
    "actNumber": "АКТ-003/2026",
    "date": "31 березня 2026 р.",
    "city": "Київ",
    "contractRef": "Договору №001/2026 від 01 січня 2026 р.",
    "currencySymbol": "₴",
    "vatRate": 0,
    "contractor": {
      "name": "ФОП Іваненко Іван Іванович",
      "representative": "Іваненко І.І.",
      "title": "Фізична особа-підприємець",
      "reg": "ІПН: 1234567890"
    },
    "customer": {
      "name": "ТОВ «Клієнт»",
      "representative": "Петренко П.П.",
      "title": "Директор",
      "reg": "ЄДРПОУ: 98765432"
    },
    "services": [
      {
        "description": "Розробка API (backend)",
        "unit": "год",
        "quantity": 60,
        "unitPrice": 1500,
        "total": 90000
      },
      {
        "description": "Технічна підтримка",
        "unit": "год",
        "quantity": 10,
        "unitPrice": 800,
        "total": 8000
      }
    ],
    "totalAmount": 98000
  }
}
```

---

## Step 5: GENERATE

```bash
cd <plugin_dir> && node scripts/generate_pdf.js /Users/ivan/Documents/.doc_input.json
```

Output:
```json
{ "success": true, "outputPath": "/Users/ivan/Documents/act_akt-003-2026_2026-03-31.pdf", "size": 124580 }
```

---

## Step 6: DELIVER

> Акт виконаних робіт згенеровано:
> 📄 `/Users/ivan/Documents/act_akt-003-2026_2026-03-31.pdf` (121 KB)
>
> Акт необхідно роздрукувати та підписати обома сторонами. Хочеш конвертувати у DOCX або внести зміни?
