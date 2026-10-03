# sqlalchemy-dev

SQLAlchemy dev plugin for Agents Store. Typed SQLAlchemy 2.0 style throughout (`DeclarativeBase`, `Mapped`, `mapped_column`, `select()`), with a SQLAlchemy 2.1 section: model definition patterns, relationship mapping, query optimization, Alembic migrations, and troubleshooting for developers building with SQLAlchemy 2.0 and 2.1.

## Skills

| Skill | Description |
|-------|-------------|
| `setup` | Verify SQLAlchemy configuration, version pin, driver and database connection |
| `model-patterns` | Model definitions, relationships, column types, constraints, mixins |
| `query-patterns` | Queries, filtering, joins, aggregations, eager loading, pagination, bulk operations |
| `api-reference` | Core SQLAlchemy API (column types, session methods, relationship options), plus references: advanced API, SQLAlchemy 2.1, Legacy 1.x style |
| `cli-recipes` | Alembic / Flask-Migrate migration commands |
| `troubleshoot` | Common SQLAlchemy errors and diagnostic steps |

## Agent

**sqlalchemy-developer** — SQLAlchemy development specialist for defining models, writing queries, managing migrations, and debugging database issues.

## Installation

Install via Agents Store or add manually to your Claude Code plugins.

## Prerequisites

- Python 3.11+ for SQLAlchemy 2.1 (SQLAlchemy 2.0.x runs on Python 3.7+; Alembic 1.20 needs 3.10+)
- SQLAlchemy 2.1, or SQLAlchemy 2.0.x
- Flask-SQLAlchemy 3.1 with `"SQLAlchemy<2.1"`: a `MappedAsDataclass` base fails on SQLAlchemy 2.1 ([pallets-eco/flask-sqlalchemy#1420](https://github.com/pallets-eco/flask-sqlalchemy/issues/1420); plain `db.Model` works), so pin `SQLAlchemy<2.1` to be safe until Flask-SQLAlchemy supports 2.1:

```bash
pip install Flask-SQLAlchemy "SQLAlchemy<2.1" Flask-Migrate
```

Plain SQLAlchemy projects install 2.1 directly. For PostgreSQL name the driver in the URL (`postgresql+psycopg://`) and install `"psycopg[binary]"`; for asyncio install `"sqlalchemy[asyncio]"`.

The examples use the 2.0 typed style and Python 3.10+ syntax. Code written in the SQLAlchemy 1.x style (`Column`, `backref`, `Model.query`) is covered only as a translation aid in the Legacy 1.x style reference.
