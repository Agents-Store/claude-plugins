---
name: auth-flask-login
description: >
  Use when the user asks about "Flask-Login", "Flask login and logout", "Flask user
  registration", "Flask authentication", "Flask login_required", "Flask password
  hashing", "Flask session auth", "protect Flask routes", or needs the session-based
  login flow for a Flask 3 application with CSRF protection.
---

# Flask Authentication with Flask-Login

## Overview

Session-based authentication for a Flask 3 app: Flask-Login keeps the signed-in user in the session cookie, Werkzeug hashes the passwords, and Flask-WTF `CSRFProtect` guards the login and registration forms.

Building blocks:

- `LoginManager` created in `extensions.py`, bound with `login_manager.init_app(app)`, with `login_manager.login_view = 'auth.login'` for the redirect of anonymous users.
- A `user_loader` callback that returns the user for an id from the session: `db.session.get(User, int(user_id))`.
- A `User` model that inherits `UserMixin` and stores only a password hash (`generate_password_hash`, scrypt by default in Werkzeug 3), checked with `check_password_hash`.
- Routes `auth.login`, `auth.register`, `auth.logout` in one blueprint, using `login_user(user)`, `logout_user()` and `@login_required`.
- `SECRET_KEY` set and kept stable: it signs the session. Without `CSRFProtect` initialised, `{{ csrf_token() }}` is undefined in the login template.
- `current_user.is_authenticated` in templates and `before_request` hooks; the login endpoint itself must stay public.

Install with the SQLAlchemy pin (see `setup` for why):

```bash
pip install Flask Flask-Login Flask-WTF Flask-SQLAlchemy "SQLAlchemy<2.1"
```

See `app-patterns` for the extension wiring and CSRF setup, `jinja2-patterns` for the login form template, `troubleshoot` for redirect loops and CSRF errors, and the `sqlalchemy-dev` plugin for the `User` model and queries.
