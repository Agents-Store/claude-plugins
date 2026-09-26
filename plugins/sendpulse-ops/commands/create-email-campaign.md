---
description: Create and send an email campaign
allowed-tools: mcp__sendpulse__email_campaigns_create, mcp__sendpulse__email_addressbooks_list, mcp__sendpulse__email_templates_list, mcp__sendpulse__email_senders_list, mcp__sendpulse__email_balance_show, mcp__sendpulse__email_addressbooks_cost
argument-hint: <subject> [--addressbook <id>] [--sender <email>] [--template <id>]
---

# Create Email Campaign

Create and send an email campaign with pre-flight checks.

## Arguments
Format: `<subject> [--addressbook <id>] [--sender <email>] [--template <id>]`
- subject: Email subject line
- --addressbook: Target addressbook ID (optional — lists if omitted)
- --sender: Sender email address (optional — lists if omitted)
- --template: Template ID (optional — lists if omitted)

Parse from "$ARGUMENTS".

## Process

1. **Check balance:**
   ```
   email_balance_show()
   ```
   Verify sufficient credits.

2. **List addressbooks if not specified:**
   ```
   email_addressbooks_list()
   ```
   Ask user to select target list.

3. **Check sending cost:**
   ```
   email_addressbooks_cost(id=<addressbook-id>)
   ```
   Confirm cost fits within balance.

4. **List senders if not specified:**
   ```
   email_senders_list()
   ```
   Ask user to select verified sender.

5. **List templates if not specified:**
   ```
   email_templates_list()
   ```
   Ask user to select template.

6. **Create campaign:**
   ```
   email_campaigns_create(
     name=<subject>,
     subject=<subject>,
     sender_email=<sender>,
     addressbook_id=<addressbook-id>,
     template_id=<template-id>
   )
   ```

7. **Report result:**
   - Campaign ID
   - Target audience size
   - Estimated cost
   - Sender and template used

## Example Usage
```
/create-email-campaign "March Newsletter" --addressbook list_001 --sender news@acme.com --template tmpl_monthly
/create-email-campaign "Product Launch Announcement"
```

## Notes
- Always checks balance before creating
- Shows cost estimate before sending
- If sender is not verified, warns the user
- Campaign is sent immediately unless send_date is specified
