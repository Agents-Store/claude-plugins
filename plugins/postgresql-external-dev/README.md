# postgresql-external-dev

PostgreSQL schema design for external database connections. Compatible SQL patterns for creating and modifying databases that work as external data sources for NocoDB and NocoBase.

## Compatible Platforms

- **NocoDB** — primary system, manages schema directly
- **NocoBase** — connects as external data source, reads schema only

See [compatible-platforms.md](skills/examples/references/compatible-platforms.md) for detailed compatibility info.

## Skills

| Skill | Description |
|-------|-------------|
| `create-tables` | Table creation templates, PK conventions, NocoDB vs NocoBase roles |
| `column-types` | Full type compatibility table (text, numeric, date/time, boolean, JSON, select, special) |
| `modify-schema` | ALTER TABLE operations — add, rename, change type, drop columns and constraints |
| `relations` | One-to-Many, One-to-One, Many-to-Many, Self-referential with FK constraints and indexes |
| `examples` | Complete e-commerce schema walkthrough with all relation types |
| `troubleshoot` | Incompatible types, anti-patterns, verification checklist |

## Agent

**postgresql-schema-designer** — Designs PostgreSQL schemas compatible with low-code platforms. Ensures all tables, relations, types, and indexes follow NocoDB/NocoBase conventions.

## Installation

Install via Agents Store or add manually to your Claude Code plugins.

## Prerequisites

- PostgreSQL database (any version supporting `serial` / `bigserial`)
- NocoDB and/or NocoBase instance for connecting the database
