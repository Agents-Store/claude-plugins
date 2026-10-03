# flask-dev

Flask dev plugin for Agents Store. Application factory patterns, blueprint organization, Jinja2 templates, Flask CLI recipes, and troubleshooting for developers building with Flask.

## Skills

| Skill | Description |
|-------|-------------|
| `setup` | Verify Flask project structure and setup |
| `project-scaffold` | Scaffold a new Flask project: layout, factory, config, `.env`, `.gitignore` |
| `app-patterns` | Application factory, blueprints, config, extensions, CSRF, CRUD views, testing |
| `auth-flask-login` | Flask-Login authentication: login, logout, registration, CSRF, protected routes |
| `api-reference` | Flask core API reference (decorators, request/response, config) |
| `cli-recipes` | Flask CLI commands (`flask run`, `flask shell`, `flask routes`, custom commands) |
| `jinja2-patterns` | Jinja2 template inheritance, macros, filters, forms |
| `troubleshoot` | Common Flask errors and diagnostic steps |

## Agent

**flask-developer** — Flask development specialist for writing routes, organizing blueprints, designing templates, and debugging Flask applications.

## Installation

Install via Agents Store or add manually to your Claude Code plugins.

## Prerequisites

- Python 3.10+
- Flask 3.x
- Flask-SQLAlchemy 3.1 with `"SQLAlchemy<2.1"`: a `MappedAsDataclass` base fails on SQLAlchemy 2.1 ([pallets-eco/flask-sqlalchemy#1420](https://github.com/pallets-eco/flask-sqlalchemy/issues/1420); plain `db.Model` works), so pin `SQLAlchemy<2.1` to be safe and install them together:

```bash
pip install Flask Flask-SQLAlchemy "SQLAlchemy<2.1" Flask-Migrate Flask-Login Flask-WTF
```
