# stack-flask-sqlalchemy-dev

Flask + SQLAlchemy stack dev plugin for Agents Store. Integration patterns for app factory wiring, blueprint-model coordination, Flask-Login + SQLAlchemy auth, Jinja2 + query data, and full-feature recipes.

> **Note:** This is a knowledge-only stack plugin. Flask and SQLAlchemy are local Python libraries, not external services — there is no MCP server or `.env.example` because there are no service URLs to configure. The integration value is in the code-level patterns.

## Skills

| Skill | Description |
|-------|-------------|
| `init-project` | Scaffold a complete Flask + SQLAlchemy project from scratch |
| `flask-sqlalchemy-wiring` | Patterns for connecting routes, models, and templates (CRUD, dashboard, selects) |
| `auth-integration` | Flask-Login + SQLAlchemy User model, login/register flow, route protection |
| `full-feature` | Step-by-step recipe for building a complete feature across all layers |

## Agent

**stack-orchestrator** — Cross-layer coordinator for building features that span models, routes, and templates.

## Installation

Install via Agents Store or add manually to your Claude Code plugins.

## Prerequisites

- Python 3.8+
- Flask 3.x + Flask-SQLAlchemy 3.x
- Recommended: flask-dev and sqlalchemy-dev plugins for individual technology knowledge
