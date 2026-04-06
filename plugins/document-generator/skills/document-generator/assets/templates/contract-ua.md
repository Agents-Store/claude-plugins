# Contract Template — Localized (PDF)

A corporate service contract template. Used when generating contracts between business entities. Supports any language for content — the template structure is universal.

## Required Fields

```
title: "SERVICE AGREEMENT"
number: "001"
date: "March 19, 2026"
city: "Kyiv"
governingLaw: "Ukraine"

companyInfo:
  name: "Your Company"
  address: "1 Khreshchatyk St, Kyiv, 01001"
  reg: "Reg. No.: 12345678"
  email: "info@company.com"
  # Optional: logoBase64 (base64 PNG) or logoUrl

party1:
  name: "FOP Ivanenko Ivan Ivanovych"
  address: "55 Velyka Vasylkivska St, Kyiv, 03150"
  reg: "Tax ID: 1234567890"
  representative: "Ivanenko I.I."
  title: "Individual Entrepreneur"

party2:
  name: "Client Company LLC"
  address: "26 Peremohy Ave, Kyiv, 03055"
  reg: "Reg. No.: 98765432"
  representative: "Petrenko P.P."
  title: "Director"

clauses:
  - number: "1"
    title: "Subject of Agreement"
    paragraphs:
      - "The Contractor agrees to provide the Customer with software development services in accordance with the technical specification (Annex 1 to this Agreement)."
      - "The Customer agrees to accept and pay for the services rendered in the manner and within the timeframe set forth in this Agreement."
  - number: "2"
    title: "Price and Payment Terms"
    paragraphs:
      - "The total fee for services under this Agreement is $70,000 (seventy thousand US dollars), VAT inclusive where applicable."
      - "Payment shall be made within 5 (five) business days of signing the Act of Completed Works."
  - number: "3"
    title: "Service Duration"
    paragraphs:
      - "Services shall be provided within 30 (thirty) calendar days from the date of signing this Agreement."
  - number: "4"
    title: "Confidentiality"
    paragraphs:
      - "Both parties agree to maintain the confidentiality of any information received in the course of performing this Agreement."
  - number: "5"
    title: "Liability"
    paragraphs:
      - "In case of late payment, the Customer shall pay a penalty of 0.1% of the outstanding amount for each day of delay."
  - number: "6"
    title: "Dispute Resolution"
    paragraphs:
      - "All disputes shall be resolved through negotiation. If no agreement is reached, disputes shall be submitted to the competent court in accordance with the governing law."
  - number: "7"
    title: "General Provisions"
    paragraphs:
      - "This Agreement becomes effective upon signing by both Parties and remains in force until all obligations are fully performed."
      - "This Agreement is executed in two counterparts of equal legal force."
```

## JSON Input Structure

```json
{
  "type": "contract",
  "engine": "puppeteer",
  "outputPath": "./contract_service_agreement_2026-03-19.pdf",
  "template": {
    "styling": {
      "primaryColor": "#1E293B",
      "accentColor": "#1E3A5F"
    }
  },
  "data": {
    "title": "SERVICE AGREEMENT",
    "number": "001/2026",
    "date": "March 19, 2026",
    "city": "Kyiv",
    "governingLaw": "Ukraine",
    "companyInfo": {
      "name": "FOP Ivanenko Ivan Ivanovych",
      "address": "55 Velyka Vasylkivska St, Kyiv",
      "reg": "Tax ID: 1234567890",
      "email": "ivan@example.com"
    },
    "party1": {
      "name": "FOP Ivanenko Ivan Ivanovych",
      "address": "55 Velyka Vasylkivska St, Kyiv, 03150",
      "reg": "Tax ID: 1234567890",
      "representative": "Ivanenko I.I.",
      "title": "Individual Entrepreneur"
    },
    "party2": {
      "name": "Client Company LLC",
      "address": "26 Peremohy Ave, Kyiv, 03055",
      "reg": "Reg. No.: 98765432",
      "representative": "Petrenko P.P.",
      "title": "Director"
    },
    "clauses": []
  }
}
```

## Notes

- Logo: add `"logoBase64": "<base64 string>"` inside `companyInfo`
- For NDA: add clauses covering Confidential Information definition, Obligations, Exclusions, Term, Remedies
- For localized content: simply write clause titles and paragraphs in the target language — the rendering engine handles any Unicode text
