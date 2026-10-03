---
name: project-scaffold
description: >
  Use when the user asks to "create a new Flask project", "scaffold a Flask app",
  "start a Flask project", "Flask project structure", "Flask project layout",
  "init Flask project", "Flask with SQLAlchemy and migrations from scratch", or needs
  the initial layout, application factory, config, .env and .gitignore for a new
  Flask 3 application.
---

# Flask Project Scaffold

## Overview

Starting a new Flask 3 project: the directory layout, the application factory, config classes selected by an `APP_ENV` variable, extensions created in `extensions.py` (Flask-SQLAlchemy, Flask-Migrate, Flask-Login, `CSRFProtect`), the `.flaskenv` / `.env` / `.gitignore` files, an install line with the SQLAlchemy pin, and the first migration.

Layout (flat, application name `myapp`):

```
myapp/
├── app.py              # create_app() factory
├── config.py           # Development / Production / Testing config classes
├── extensions.py       # db, migrate, login_manager, csrf (no app imported)
├── models.py           # SQLAlchemy models
├── routes/             # one blueprint per feature area
├── templates/          # base.html and per-feature templates
├── static/
├── tests/
├── requirements.txt
├── .flaskenv           # FLASK_APP, APP_ENV, FLASK_DEBUG (public, committed)
├── .env                # SECRET_KEY, DATABASE_URL (private, gitignored)
└── .gitignore          # .env, instance/, .venv/, __pycache__/
```

Install and first run (Python 3.10+). A `MappedAsDataclass` base fails on SQLAlchemy 2.1 ([pallets-eco/flask-sqlalchemy#1420](https://github.com/pallets-eco/flask-sqlalchemy/issues/1420); plain `db.Model` works), so pin `SQLAlchemy<2.1` to be safe until Flask-SQLAlchemy supports 2.1. Run this after the files above exist and `.env` holds a `SECRET_KEY`:

```bash
# run from the project root, after the files above exist and .env holds SECRET_KEY
python3 -m venv .venv && . .venv/bin/activate
pip install Flask Flask-SQLAlchemy "SQLAlchemy<2.1" Flask-Migrate Flask-Login Flask-WTF python-dotenv
flask db init
flask db migrate -m "Initial schema"
flask db upgrade
flask run
```

Rules the scaffold follows:

- No `db.create_all()` in the factory; the schema comes from `flask db upgrade`.
- `SECRET_KEY` has no fallback value: the factory raises when it is missing.
- Debug mode comes from `--debug` / `FLASK_DEBUG`, never from a config class.
- Queries use `db.session.execute(db.select(...))`, not `Model.query`.

This skill is an outline for now: it gives the layout, the commands and the rules, and points to the skills that hold the details.

See `app-patterns` for the factory, config classes and extension wiring in full, `auth-flask-login` for the login flow, `setup` to verify an existing project, and the `sqlalchemy-dev` plugin for models and migrations.
