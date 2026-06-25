# ML and AI Analytics Platform

## Project Team
- **Ahmad Niazi** (L1f23bsse0381)
- **Hamza Sahid** (L123bsse0362)

A Flask web application built as a semester project that provides a single interface for running several machine learning and NLP tasks without writing any code.

## What it does

Most ML experiments require setting up Python environments, writing scripts, and managing output files manually. This project solves that by wrapping the most common algorithms in a web form — upload a CSV, set parameters, and click run.

**Modules included:**

- **Apriori Association Rule Mining** — upload a transactional CSV and discover frequent itemsets and association rules using support, confidence, and lift thresholds
- **Deep Learning Classifier** — train a neural network on any tabular CSV dataset, with accuracy, precision, recall, and F1 score reported
- **Question Answering** — provide a paragraph of text and ask a question; a transformer model extracts the answer from the context
- **Text Generation** — enter a prompt and control max tokens and temperature to generate text continuations
- **Named Entity Recognition** — paste any text to extract named entities (people, places, organizations)
- **AI Assistant** — a chat interface for asking questions about data or results; conversations are saved per user

## Database

The application uses **SQLite** stored at `instance/app.db`. The schema is defined in [`schema.sql`](schema.sql) and includes six tables:

| Table | Purpose |
|---|---|
| `users` | Registered platform users with roles (admin, analyst, viewer) |
| `uploads` | Uploaded CSV dataset files |
| `jobs` | Background analytics and inference jobs |
| `audit_events` | Immutable log of login, upload, and admin actions |
| `chat_sessions` | Named conversation threads |
| `chat_messages` | Individual messages within each session |

Tables are created automatically the first time you run `flask init-db`.

## Setup

**Requirements:** Python 3.11+

1. Install the core platform:

   ```bash
   pip install -e .[dev]
   ```

2. Install ML/AI extras (only what you need):

   ```bash
   pip install -e .[analytics]           # Apriori and classifier
   pip install -e .[analytics,training]  # adds TensorFlow for classifier training
   pip install -e .[genai]               # adds transformers for QA, text gen, NER
   ```

3. Copy the example environment file:

   ```bash
   copy .env.example .env
   ```

4. Create the database tables and seed an admin account:

   ```bash
   flask --app wsgi.py init-db
   flask --app wsgi.py seed-admin
   ```

   Default admin credentials are set in `.env` (see `DEFAULT_ADMIN_EMAIL` and `DEFAULT_ADMIN_PASSWORD`).

5. Run the app:

   ```bash
   flask --app wsgi.py run
   ```

6. Open `http://127.0.0.1:5000` in your browser and sign in.

## User management

Admin users can create, update, and deactivate accounts directly from the **Users** page (`/admin/users`). All changes go straight to the SQLite database.

You can also manage users from the command line:

```bash
flask --app wsgi.py create-user        # create a new user interactively
flask --app wsgi.py list-users         # list all users
flask --app wsgi.py reset-user-password  # reset a user's password
```

## Project structure

```
ai_analytics_hub/
  core/          # config, extensions, error handlers, CLI commands
  domain/        # SQLAlchemy models (matches schema.sql)
  services/      # business logic: auth, apriori, classifier, chat, etc.
  api/           # REST API blueprints
  web/           # HTML route handlers
  templates/     # Jinja2 HTML templates
  static/        # CSS and JavaScript
tests/           # pytest test suite
schema.sql       # reference SQL schema snapshot
wsgi.py          # WSGI entry point
```

## Running tests

```bash
pytest
```

## Tech stack

| Component | Technology |
|---|---|
| Web framework | Flask 3 |
| Database ORM | SQLAlchemy 2 + Flask-SQLAlchemy |
| Database | SQLite (development) |
| Authentication | Flask-Login (sessions) + Flask-JWT-Extended (API) |
| ML / analytics | pandas, scikit-learn, mlxtend |
| Deep learning | TensorFlow / Keras |
| NLP | HuggingFace Transformers |
| Background jobs | Celery + Redis |
| Forms & CSRF | Flask-WTF |
