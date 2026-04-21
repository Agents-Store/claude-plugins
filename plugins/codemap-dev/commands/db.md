---
description: Parse models, migrations, or schema and generate an ERD diagram + DB documentation
argument-hint: (no arguments — auto-detects models)
---

# Database Schema ERD

Analyze the database schema and generate an Entity-Relationship Diagram + documentation.

## Instructions

1. Read all three codemap skills:
   - `${CLAUDE_PLUGIN_ROOT}/skills/codemap-diagram/SKILL.md` — for ERD generation rules
   - `${CLAUDE_PLUGIN_ROOT}/skills/codemap-explain/SKILL.md` — for explaining schema design decisions
   - `${CLAUDE_PLUGIN_ROOT}/skills/codemap-review/SKILL.md` — for identifying schema issues (missing indexes, naming inconsistencies, missing constraints)
2. Read ERD-specific guidance from `${CLAUDE_PLUGIN_ROOT}/skills/codemap-diagram/references/diagram-types.md`

### Detect ORM and Models

3. Search for model definitions in order of priority:
   - `models.py` or `models/` directory (SQLAlchemy, Django)
   - `prisma/schema.prisma` (Prisma)
   - `*.entity.ts` files (TypeORM)
   - `migrations/versions/` (Alembic — parse for table definitions)
   - `*.sql` migration files
   - If nothing found → ask user where models are defined

### Parse Schema

4. For each model/table found, extract:
   - Table name
   - All columns with types
   - Primary keys (mark as PK)
   - Foreign keys (mark as FK, note referenced table)
   - Unique constraints
   - Relationships (one-to-many, many-to-many, self-referential)
   - Junction/association tables for M:N relationships

### Review Schema Quality

5. Apply codemap-review methodology to identify schema issues:
   - Missing foreign key constraints
   - Naming inconsistencies (mixed conventions)
   - Missing created_at/updated_at timestamps
   - Missing user_id for data isolation (if multi-tenant)
   - Tables without primary keys

### Generate ERD

6. Build mxGraph XML for ERD:
   - Each table as a box with: table name header, column rows (name + type)
   - PK and FK markers in left column
   - Relationship edges with cardinality labels (1, N, M)
   - Use Data layer color (blue: `#dae8fc` / `#6c8ebf`)
   - Include color legend
   - Apply adequate spacing between tables

7. Save to `docs/codemap/diagrams/erd.drawio`
8. Call `open_drawio_xml` MCP tool for preview

### Generate DB Documentation

9. Write `docs/codemap/DB.md` with:
   - **Tables Overview** — list of all tables with one-line descriptions
   - **Table Details** — for each table: columns, types, constraints, purpose (using codemap-explain methodology)
   - **Relationships** — description of all FK relationships and their meaning
   - **Data Isolation** — note which tables have user_id for multi-tenant data isolation
   - **Schema Quality Notes** — issues found during review (from step 5)
   - **Link to ERD** — reference to the generated diagram file

### Output

10. Show the ERD file path and preview URL
11. Show the DB.md file path
12. Summary: total tables, total relationships, any notable patterns or issues found