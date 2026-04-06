# Building a CRM with NocoBase API

End-to-end walkthrough for creating a Customer Relationship Management data model using the NocoBase HTTP API. This scenario creates companies, contacts, and deals collections with full relationships, sample data, and association queries.

## Prerequisites

- A running NocoBase V2 instance with API access
- The **setup** skill verification steps completed successfully
- Admin-level API key with collection create/write permissions

## Step 1 -- Create the "companies" Collection

Create the companies collection with core business fields.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections:create" \
  -d '{
    "name": "companies",
    "title": "Companies",
    "fields": [
      {
        "name": "name",
        "type": "string",
        "interface": "input",
        "uiSchema": {
          "title": "Company Name",
          "type": "string",
          "x-component": "Input",
          "required": true
        }
      },
      {
        "name": "industry",
        "type": "string",
        "interface": "select",
        "uiSchema": {
          "title": "Industry",
          "type": "string",
          "x-component": "Select",
          "enum": [
            { "value": "technology", "label": "Technology" },
            { "value": "finance", "label": "Finance" },
            { "value": "healthcare", "label": "Healthcare" },
            { "value": "manufacturing", "label": "Manufacturing" },
            { "value": "retail", "label": "Retail" },
            { "value": "other", "label": "Other" }
          ]
        }
      },
      {
        "name": "website",
        "type": "string",
        "interface": "url",
        "uiSchema": {
          "title": "Website",
          "type": "string",
          "x-component": "Input.URL"
        }
      },
      {
        "name": "size",
        "type": "string",
        "interface": "select",
        "uiSchema": {
          "title": "Company Size",
          "type": "string",
          "x-component": "Select",
          "enum": [
            { "value": "1-10", "label": "1-10 employees" },
            { "value": "11-50", "label": "11-50 employees" },
            { "value": "51-200", "label": "51-200 employees" },
            { "value": "201-1000", "label": "201-1000 employees" },
            { "value": "1000+", "label": "1000+ employees" }
          ]
        }
      },
      {
        "name": "notes",
        "type": "text",
        "interface": "textarea",
        "uiSchema": {
          "title": "Notes",
          "type": "string",
          "x-component": "Input.TextArea"
        }
      }
    ]
  }'
```

**Expected response:** A JSON object with the created collection metadata, including the auto-generated `id` and all field definitions.

## Step 2 -- Create the "contacts" Collection

Create the contacts collection with personal and professional fields.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections:create" \
  -d '{
    "name": "contacts",
    "title": "Contacts",
    "fields": [
      {
        "name": "firstName",
        "type": "string",
        "interface": "input",
        "uiSchema": {
          "title": "First Name",
          "type": "string",
          "x-component": "Input",
          "required": true
        }
      },
      {
        "name": "lastName",
        "type": "string",
        "interface": "input",
        "uiSchema": {
          "title": "Last Name",
          "type": "string",
          "x-component": "Input",
          "required": true
        }
      },
      {
        "name": "email",
        "type": "string",
        "interface": "email",
        "uiSchema": {
          "title": "Email",
          "type": "string",
          "x-component": "Input",
          "x-component-props": { "type": "email" },
          "required": true
        }
      },
      {
        "name": "phone",
        "type": "string",
        "interface": "phone",
        "uiSchema": {
          "title": "Phone",
          "type": "string",
          "x-component": "Input",
          "x-component-props": { "type": "tel" }
        }
      },
      {
        "name": "jobTitle",
        "type": "string",
        "interface": "input",
        "uiSchema": {
          "title": "Job Title",
          "type": "string",
          "x-component": "Input"
        }
      },
      {
        "name": "status",
        "type": "string",
        "interface": "radioGroup",
        "uiSchema": {
          "title": "Status",
          "type": "string",
          "x-component": "Radio.Group",
          "enum": [
            { "value": "lead", "label": "Lead" },
            { "value": "active", "label": "Active" },
            { "value": "inactive", "label": "Inactive" }
          ],
          "default": "lead"
        }
      }
    ]
  }'
```

## Step 3 -- Create the "deals" Collection

Create the deals collection to track sales opportunities.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections:create" \
  -d '{
    "name": "deals",
    "title": "Deals",
    "fields": [
      {
        "name": "title",
        "type": "string",
        "interface": "input",
        "uiSchema": {
          "title": "Deal Title",
          "type": "string",
          "x-component": "Input",
          "required": true
        }
      },
      {
        "name": "value",
        "type": "decimal",
        "interface": "number",
        "uiSchema": {
          "title": "Deal Value",
          "type": "number",
          "x-component": "InputNumber",
          "x-component-props": { "precision": 2, "min": 0 }
        }
      },
      {
        "name": "stage",
        "type": "string",
        "interface": "radioGroup",
        "uiSchema": {
          "title": "Stage",
          "type": "string",
          "x-component": "Radio.Group",
          "enum": [
            { "value": "prospecting", "label": "Prospecting" },
            { "value": "qualification", "label": "Qualification" },
            { "value": "proposal", "label": "Proposal" },
            { "value": "negotiation", "label": "Negotiation" },
            { "value": "closed_won", "label": "Closed Won" },
            { "value": "closed_lost", "label": "Closed Lost" }
          ],
          "default": "prospecting"
        }
      },
      {
        "name": "expectedCloseDate",
        "type": "date",
        "interface": "datetime",
        "uiSchema": {
          "title": "Expected Close Date",
          "type": "string",
          "x-component": "DatePicker",
          "x-component-props": { "dateFormat": "YYYY-MM-DD" }
        }
      },
      {
        "name": "description",
        "type": "text",
        "interface": "textarea",
        "uiSchema": {
          "title": "Description",
          "type": "string",
          "x-component": "Input.TextArea"
        }
      }
    ]
  }'
```

## Step 4 -- Set Up Relationships

### 4a. Contact belongsTo Company

Each contact belongs to one company. This creates a `companyId` foreign key on the contacts collection.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections/contacts/fields:create" \
  -d '{
    "name": "company",
    "type": "belongsTo",
    "interface": "m2o",
    "target": "companies",
    "foreignKey": "companyId",
    "targetKey": "id",
    "uiSchema": {
      "title": "Company",
      "x-component": "AssociationField",
      "x-component-props": { "fieldNames": { "label": "name", "value": "id" } }
    }
  }'
```

### 4b. Company hasMany Contacts

The reverse relationship -- a company has many contacts.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections/companies/fields:create" \
  -d '{
    "name": "contacts",
    "type": "hasMany",
    "interface": "o2m",
    "target": "contacts",
    "foreignKey": "companyId",
    "sourceKey": "id",
    "uiSchema": {
      "title": "Contacts",
      "x-component": "AssociationField",
      "x-component-props": { "fieldNames": { "label": "email", "value": "id" } }
    }
  }'
```

### 4c. Deal belongsTo Contact

Each deal is linked to a contact.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections/deals/fields:create" \
  -d '{
    "name": "contact",
    "type": "belongsTo",
    "interface": "m2o",
    "target": "contacts",
    "foreignKey": "contactId",
    "targetKey": "id",
    "uiSchema": {
      "title": "Contact",
      "x-component": "AssociationField",
      "x-component-props": { "fieldNames": { "label": "email", "value": "id" } }
    }
  }'
```

### 4d. Deal belongsTo Company

Each deal is also linked to a company.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections/deals/fields:create" \
  -d '{
    "name": "company",
    "type": "belongsTo",
    "interface": "m2o",
    "target": "companies",
    "foreignKey": "dealCompanyId",
    "targetKey": "id",
    "uiSchema": {
      "title": "Company",
      "x-component": "AssociationField",
      "x-component-props": { "fieldNames": { "label": "name", "value": "id" } }
    }
  }'
```

### 4e. Contact hasMany Deals

The reverse relationship -- a contact has many deals.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections/contacts/fields:create" \
  -d '{
    "name": "deals",
    "type": "hasMany",
    "interface": "o2m",
    "target": "deals",
    "foreignKey": "contactId",
    "sourceKey": "id",
    "uiSchema": {
      "title": "Deals",
      "x-component": "AssociationField",
      "x-component-props": { "fieldNames": { "label": "title", "value": "id" } }
    }
  }'
```

### 4f. Company hasMany Deals

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collections/companies/fields:create" \
  -d '{
    "name": "deals",
    "type": "hasMany",
    "interface": "o2m",
    "target": "deals",
    "foreignKey": "dealCompanyId",
    "sourceKey": "id",
    "uiSchema": {
      "title": "Deals",
      "x-component": "AssociationField",
      "x-component-props": { "fieldNames": { "label": "title", "value": "id" } }
    }
  }'
```

## Step 5 -- Create a Collection Category

Organize the CRM collections under a category for cleaner navigation.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/collectionCategories:create" \
  -d '{
    "name": "CRM",
    "color": "#1890ff"
  }'
```

Note the returned category `id`. You can then assign collections to this category by updating them. The exact mechanism depends on your NocoBase version -- some versions support a `category` field on the collection, while others use a separate association.

## Step 6 -- Create Sample Records

### 6a. Create Companies

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/companies:create" \
  -d '{
    "name": "TechVision Inc.",
    "industry": "technology",
    "website": "https://techvision.example.com",
    "size": "51-200",
    "notes": "Enterprise software company, strong potential for platform deal"
  }'
```

Note the returned `id` (e.g., `1`) for use in subsequent records.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/companies:create" \
  -d '{
    "name": "Global Finance Corp",
    "industry": "finance",
    "website": "https://globalfinance.example.com",
    "size": "1000+",
    "notes": "Large financial institution, compliance-heavy procurement process"
  }'
```

### 6b. Create Contacts

Use the company IDs from the previous step in the `companyId` field.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/contacts:create" \
  -d '{
    "firstName": "Sarah",
    "lastName": "Chen",
    "email": "sarah.chen@techvision.example.com",
    "phone": "+1-555-0101",
    "jobTitle": "CTO",
    "status": "active",
    "companyId": 1
  }'
```

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/contacts:create" \
  -d '{
    "firstName": "James",
    "lastName": "Wilson",
    "email": "j.wilson@globalfinance.example.com",
    "phone": "+1-555-0202",
    "jobTitle": "VP of Procurement",
    "status": "lead",
    "companyId": 2
  }'
```

### 6c. Create Deals

Use the contact and company IDs from previous steps.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/deals:create" \
  -d '{
    "title": "TechVision Platform License",
    "value": 75000.00,
    "stage": "proposal",
    "expectedCloseDate": "2026-06-30",
    "description": "Annual platform license for 100 seats",
    "contactId": 1,
    "dealCompanyId": 1
  }'
```

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/deals:create" \
  -d '{
    "title": "Global Finance Security Audit",
    "value": 150000.00,
    "stage": "qualification",
    "expectedCloseDate": "2026-09-15",
    "description": "Comprehensive security audit and compliance review",
    "contactId": 2,
    "dealCompanyId": 2
  }'
```

## Step 7 -- Query Records with Associations

### List Contacts with Their Company

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/contacts:list?appends=[company]&page=1&pageSize=20"
```

**Expected response:**

```json
{
  "data": [
    {
      "id": 1,
      "firstName": "Sarah",
      "lastName": "Chen",
      "email": "sarah.chen@techvision.example.com",
      "company": {
        "id": 1,
        "name": "TechVision Inc.",
        "industry": "technology"
      }
    }
  ],
  "meta": { "count": 2, "page": 1, "pageSize": 20, "totalPage": 1 }
}
```

### List Deals with Contact and Company

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/deals:list?appends=[contact,company]&sort=[-value]&page=1&pageSize=20"
```

### Get a Company with All Its Contacts and Deals

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/companies:get?filterByTk=1&appends=[contacts,deals]"
```

**Expected response:**

```json
{
  "data": {
    "id": 1,
    "name": "TechVision Inc.",
    "industry": "technology",
    "website": "https://techvision.example.com",
    "contacts": [
      {
        "id": 1,
        "firstName": "Sarah",
        "lastName": "Chen",
        "email": "sarah.chen@techvision.example.com"
      }
    ],
    "deals": [
      {
        "id": 1,
        "title": "TechVision Platform License",
        "value": 75000.00,
        "stage": "proposal"
      }
    ]
  }
}
```

### Filter Deals by Stage

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/deals:list?filter={\"stage\":{\"$in\":[\"proposal\",\"negotiation\"]}}&appends=[contact,company]&sort=[-value]&page=1&pageSize=50"
```

### Filter Contacts by Company Industry

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/contacts:list?filter={\"company.industry\":{\"$eq\":\"technology\"}}&appends=[company]&page=1&pageSize=50"
```

## Summary

This scenario created:

- **3 collections**: companies, contacts, deals
- **6 relationships**: 3 belongsTo (contacts->companies, deals->contacts, deals->companies) and 3 hasMany (reverse)
- **1 collection category**: CRM
- **Sample records**: 2 companies, 2 contacts, 2 deals

The data model supports typical CRM queries: finding all contacts at a company, listing deals in a pipeline stage, viewing a company's total deal value, and navigating from deal to contact to company.

## Cleanup

To remove all test data and collections:

```bash
# Delete in reverse dependency order
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/collections:destroy?filterByTk=deals"

curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/collections:destroy?filterByTk=contacts"

curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/collections:destroy?filterByTk=companies"
```

**Warning:** Destroying a collection permanently deletes the underlying database table and all records. This is irreversible.
