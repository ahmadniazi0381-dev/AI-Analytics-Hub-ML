# Migrations

Initialize Alembic after the first local setup:

```bash
flask --app wsgi.py db init
flask --app wsgi.py db migrate -m "Initial schema"
flask --app wsgi.py db upgrade
```
