---
description: Add a subscriber to an email addressbook
allowed-tools: mcp__sendpulse__email_addressbooks_emails_create, mcp__sendpulse__email_addressbooks_list
argument-hint: <email> [--addressbook <id>] [--name <name>]
---

# Add Subscriber

Add a subscriber to an email addressbook (mailing list).

## Arguments
Format: `<email> [--addressbook <id>] [--name <name>]`
- email: Subscriber email address
- --addressbook: Target addressbook ID (optional — lists if omitted)
- --name: Subscriber name (optional)

Parse from "$ARGUMENTS".

## Process

1. **List addressbooks if not specified:**
   ```
   email_addressbooks_list()
   ```
   Ask user to select target list.

2. **Add subscriber:**
   ```
   email_addressbooks_emails_create(
     id=<addressbook-id>,
     emails=[{
       "email": "<email>",
       "variables": {"name": "<name>"}
     }]
   )
   ```

3. **Report result:**
   - Confirmation of addition
   - Addressbook name
   - Subscriber email

## Example Usage
```
/add-subscriber user@example.com --addressbook list_001 --name "John Doe"
/add-subscriber lead@company.com
```

## Notes
- If addressbook not specified, lists available addressbooks
- Name is optional but recommended for personalization
