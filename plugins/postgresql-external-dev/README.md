# postgresql-external-dev

PostgreSQL schema design for external database connections. Compatible SQL patterns for creating and modifying databases that work as external data sources for NocoDB and NocoBase.

## Compatible Platforms

- **NocoDB** — connects PostgreSQL as an external data source; can create and alter tables itself only when *Allow Schema Edit* is enabled (off by default), otherwise you change the schema with SQL and run **Meta Sync**
- **NocoBase** — connects as an external data source and reads the schema only. The PostgreSQL connector (`@nocobase/plugin-data-source-external-postgres`) **requires a commercial license** — Standard edition or above, not available in Community. After a schema change, **refresh** the data source

See [compatible-platforms.md](skills/examples/references/compatible-platforms.md) for detailed compatibility info.

## Safe Defaults, Wider Support

The skills generate conservative defaults that behave the same on both platforms: `serial`/`bigserial` PK named `id`, `json`, `text` for select fields, `timestamp`. Upstream docs and source accept more — `jsonb`, `uuid` keys, `ARRAY`, native `ENUM`, geometric types — with per-platform caveats. The `column-types` and `troubleshoot` skills list them; check on your target versions before using one.

## Skills

| Skill | Description |
|-------|-------------|
| `create-tables` | Table creation templates, PK conventions, NocoDB vs NocoBase roles, tables without a primary key |
| `column-types` | Type compatibility table (text, numeric, date/time, boolean, JSON, select, special) and per-platform support for `jsonb`, `uuid`, `ARRAY`, `ENUM`, geometric types |
| `modify-schema` | ALTER TABLE operations — add, rename, change type, drop columns and constraints — plus Meta Sync / refresh afterwards |
| `relations` | One-to-Many, One-to-One, Many-to-Many, Self-referential with FK constraints and indexes |
| `examples` | Complete e-commerce schema walkthrough with all relation types |
| `troubleshoot` | Type caveats by platform, anti-patterns, verification checklist |

## Agent

**postgresql-schema-designer** — Designs PostgreSQL schemas compatible with low-code platforms. Ensures all tables, relations, types, and indexes follow NocoDB/NocoBase conventions.

## Installation

Install via Agents Store or add manually to your Claude Code plugins.

## Prerequisites

- PostgreSQL 14 to 18 (supported upstream; NocoDB recommends 14 or later). Version 13 and older are end of life. NocoBase's external connector documents 9.5 as its minimum
- NocoDB and/or NocoBase instance for connecting the database
- For NocoBase: a commercial license that includes the external PostgreSQL data source plugin
