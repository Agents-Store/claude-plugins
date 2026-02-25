---
description: Create a new CRM contact
allowed-tools: mcp__sendpulse__crm_contacts_create, mcp__sendpulse__crm_contacts_list_by_email
argument-hint: <email> [--name <name>] [--phone <phone>]
---

# Create Contact

Create a new CRM contact with email, name, and phone.

## Arguments
Format: `<email> [--name <name>] [--phone <phone>]`
- email: Contact email address (required)
- --name: Contact full name (optional)
- --phone: Contact phone number (optional)

Parse from "$ARGUMENTS".

## Process

1. **Check for duplicates:**
   ```
   crm_contacts_list_by_email(email=<email>)
   ```
   If contact exists, show it and ask if user wants to update instead.

2. **Create contact:**
   ```
   crm_contacts_create(
     emails=[{"value": "<email>"}],
     name="<name>",
     phones=[{"value": "<phone>"}]
   )
   ```

3. **Report result:**
   - Contact ID
   - Name, email, phone

## Example Usage
```
/create-contact user@example.com --name "John Doe" --phone "+380501234567"
/create-contact lead@company.com --name "Jane Smith"
/create-contact prospect@corp.com
```

## Notes
- Checks for existing contact with same email before creating
- Phone should include country code
- Name and phone are optional
