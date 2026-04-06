---
description: Generate a professional cost estimate / quotation (PDF)
allowed-tools: ["Bash", "Read", "Write", "Glob"]
argument-hint: <estimate-number> [--company <name>] [--client <name>]
---

# Generate Estimate

Generate a detailed, professional cost estimate with phase-based pricing, team composition, timeline, scope, and payment schedule.

## Arguments

Format: `<estimate-number> [--company <name>] [--client <name>]`
- estimate-number: Estimate reference number (required)
- --company: Your company name (optional, loaded from preferences)
- --client: Client name (optional)

Parse from "$ARGUMENTS".

## Process

1. **Resolve plugin directory:**
   Find the plugin dir by globbing for `**/document-generator/scripts/generate_pdf.js`.

2. **Check dependencies.**

3. **Gather data from user (structured for detailed estimate):**

   **Required:**
   - Company info (from preferences or ask): name, address, email, phone
   - Client info: company name, contact person, address, email
   - Estimate number and date
   - Project executive summary (2-4 sentences)
   - Scope of work:
     - Description (what the project is)
     - Inclusions list (what IS included)
     - Exclusions list (what is NOT included)
     - Assumptions list (conditions/prerequisites)
   - Team composition: role, hourly rate, allocation % for each member
   - Phases with tasks: for each phase:
     - Phase name (e.g., "Phase 1: Discovery & Planning")
     - Phase color (optional, defaults provided)
     - Tasks: description, role, hours, rate for each task
   - Timeline: total duration + phases with start/end weeks and milestones
   - Payment schedule: milestones with percentage splits

   **Optional:**
   - Optional items / add-ons (shown separately from total)
   - Contingency percentage and label (default: 10%)
   - Tax amount
   - Discount amount
   - Validity period (default: 30 days)
   - Terms and conditions (array of {title, text})
   - Acceptance/signature block (default: enabled)
   - Notes

4. **Read template:**
   ```bash
   cat <plugin_dir>/templates/estimate_template.json
   ```

5. **Build JSON input:**
   ALWAYS use `"phases"` format (not flat `"items"`). Structure:
   ```json
   {
     "type": "estimate",
     "outputPath": "...",
     "data": {
       "estimateNumber": "EST-2026-001",
       "date": "...",
       "validDays": 30,
       "companyInfo": { "name": "", "address": "", "email": "", "phone": "" },
       "recipient": { "name": "", "contactPerson": "", "address": "", "email": "" },
       "executiveSummary": "...",
       "scope": {
         "description": "...",
         "inclusions": ["..."],
         "exclusions": ["..."],
         "assumptions": ["..."]
       },
       "team": [
         { "role": "Project Manager", "rate": 120, "rateUnit": "hour", "allocation": "25%" }
       ],
       "phases": [
         {
           "name": "Phase 1: Discovery",
           "color": "#6366F1",
           "tasks": [
             { "description": "Requirements gathering", "role": "Project Manager", "hours": 16, "rate": 120 }
           ]
         }
       ],
       "optionalItems": [
         { "description": "...", "hours": 40, "rate": 175, "total": 7000 }
       ],
       "contingency": { "percent": 10, "label": "Risk contingency" },
       "timeline": {
         "totalDuration": "12 weeks",
         "phases": [
           { "name": "Discovery", "startWeek": 1, "endWeek": 3, "milestones": ["..."], "color": "#6366F1" }
         ]
       },
       "paymentSchedule": [
         { "milestone": "Project kickoff", "percent": 30, "dueDate": "Upon signing" }
       ],
       "terms": [
         { "title": "Payment Terms", "text": "..." }
       ],
       "acceptance": { "enabled": true }
     }
   }
   ```
   Write to `.doc_input.json`.

6. **Generate PDF:**
   ```bash
   cd <plugin_dir> && node scripts/generate_pdf.js /absolute/path/.doc_input.json
   ```

7. **Deliver result:**
   Show file path, size, and summary (total, phases count, timeline, team size).

## Phase Color Palette (suggested defaults)
- Phase 1: `#6366F1` (indigo)
- Phase 2: `#8B5CF6` (violet)
- Phase 3: `#A78BFA` (purple)
- Phase 4: `#C4B5FD` (lavender)
- Phase 5: `#818CF8` (blue-indigo)

## Example Usage
```
/generate-estimate "EST-2026-001" --company "TechCo" --client "Acme Corp"
/generate-estimate "Q-042"
```
