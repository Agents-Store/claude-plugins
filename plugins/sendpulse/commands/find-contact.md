---
description: Find a CRM contact by email address
allowed-tools: mcp__sendpulse__crm_contacts_list_by_email, mcp__sendpulse__crm_contacts_show, mcp__sendpulse__crm_contacts_deals_list
argument-hint: <email>
---

# Find Contact

Find a CRM contact by email and show their details and deals.

## Arguments
Format: `<email>`
- email: The email address to search for

Parse from "$ARGUMENTS".

## Process

1. **Search by email:**
   ```
   crm_contacts_list_by_email(email=<email>)
   ```

2. **If found, get full details:**
   ```
   crm_contacts_show(id=<contact-id>)
   ```

3. **Show associated deals:**
   ```
   crm_contacts_deals_list(id=<contact-id>)
   ```

4. **Report result:**
   - Contact name, email, phone
   - Custom fields
   - Associated deals with amounts and stages

## Example Usage
```
/find-contact user@example.com
/find-contact cto@bigcorp.com
```

## Notes
- Shows full contact details including custom fields
- Lists all associated deals
- Returns "not found" if no contact matches the email
