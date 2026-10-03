# stack-flask-sqlalchemy

Flask + SQLAlchemy architecture plugin for Agents Store. It describes how the application factory, the Flask-SQLAlchemy session, Alembic migrations and Jinja2 templates fit together: where `db` is created, what the app context owns, where the transaction ends, what `expire_on_commit` does to a request, and how a template stays free of queries. It names its parts in `dependencies`; what one tool does and how to drive it is taught by that tool's own plugin.

> **Note:** Flask and SQLAlchemy are local Python libraries, not external services: there is no MCP server and no `.env.example` because there are no service URLs to configure. The value is in the boundaries.

## Architecture

| Layer | Library | Role |
|-------|---------|------|
| Interface | Flask, Jinja2, Flask-Login, Flask-WTF | Routes, templates, sessions, CSRF |
| Data | SQLAlchemy 2.0, Flask-SQLAlchemy, Flask-Migrate (Alembic) | Models, queries, schema through migrations |

The boundaries between them are what this plugin owns:

| Boundary | Rule |
|----------|------|
| Where `db` lives | `extensions.py`, created without an app; the factory imports the models |
| App context | One session per app context; scripts, threads and tasks open their own and pass ids, not instances |
| Transaction | One `commit()` per unit of work, in the route; `rollback()` after an `IntegrityError` |
| Expiry | `expire_on_commit` stays on; Post/Redirect/Get; ids across contexts |
| Route to template | `lazy='raise'` on the model, `selectinload` / `joinedload` in the route, a statement-count test |
| Schema | Migrations only; no `create_all()` outside test fixtures |

## Dependencies

Declared in `plugin.json` and installed together with the stack. They hold the tool-level knowledge:

| Plugin | Teaches |
|--------|---------|
| `flask-dev` | `project-scaffold` (the files of a new project), `auth-flask-login` (login, registration, logout, CSRF), `app-patterns` (factory, blueprints, config, CRUD views, testing), Jinja2, the Flask CLI |
| `sqlalchemy-dev` | Models (`model-patterns`, including the Flask-Login `User` model), queries and owner-scoped queries (`query-patterns`), Alembic and Flask-Migrate (`cli-recipes`), SQLAlchemy 2.1 |

## Prerequisites

- Python 3.10 or newer
- Flask 3.1 or newer
- Flask-SQLAlchemy 3.1 with `"SQLAlchemy<2.1"`: a plain install resolves SQLAlchemy 2.1, and a `MappedAsDataclass` base fails on it ([pallets-eco/flask-sqlalchemy#1420](https://github.com/pallets-eco/flask-sqlalchemy/issues/1420); plain `db.Model` works), so pin `SQLAlchemy<2.1` to be safe until Flask-SQLAlchemy supports 2.1:

```bash
pip install Flask Flask-SQLAlchemy "SQLAlchemy<2.1" Flask-Migrate Flask-Login Flask-WTF python-dotenv
```

## Installation

```bash
claude plugin install stack-flask-sqlalchemy@agents-store-claude-plugins
```

`flask-dev` and `sqlalchemy-dev` come with it.

## Skills

| Skill | Description |
|-------|-------------|
| `layers-and-boundaries` | Where `db` lives, the app context, the transaction boundary, `expire_on_commit`, N+1 at the route-to-template edge, what test fixtures hide |
| `full-feature` | Step-by-step recipe for building a feature across model, migration, routes and templates |

New project: `flask-dev` → `project-scaffold`. Login: `flask-dev` → `auth-flask-login`. CRUD views: `flask-dev` → `app-patterns`. Models and queries: `sqlalchemy-dev`.

## Agent

**stack-orchestrator** — Cross-layer coordinator for building features that span models, migrations, routes and templates, and for debugging problems at the boundaries.
