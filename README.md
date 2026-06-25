# 🤖 AI Analytics Hub

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.x-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white)
![MIT License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

---

A production-ready AI analytics platform built with Flask, TensorFlow, Transformers, Celery, Redis, PostgreSQL, and Docker.

## 👨‍💻 Author

**Muhammad Ahmad Khan Niazi**

BS Software Engineering  
University of Central Punjab (UCP)

GitHub:
https://github.com/ahmadniazi0381-dev


A Flask web application built as a project that provides a single interface for running several machine learning and NLP tasks without writing any code.

## 🚀 Quick Links

- Features
- Installation
- Documentation
- Architecture
- Screenshots
- License

## 📚 Table of Contents

- Features
- Technology Stack
- Architecture
- Folder Structure
- Installation
- Configuration
- Docker Deployment
- API Endpoints
- Screenshots
- Documentation
- Roadmap
- License

## ✨ Features

- Association Rule Mining (Apriori)
- Deep Learning Classifier
- AI Question Answering
- AI Text Generation
- Named Entity Recognition
- Authentication & Authorization
- Celery Background Workers
- PostgreSQL Database
- Redis Caching
- Docker Deployment
- REST API
- Professional Dashboard


## 🛠 Technology Stack

| Category | Technology |
|----------|------------|
| Backend | Flask |
| Language | Python |
| Database | PostgreSQL |
| Cache | Redis |
| Queue | Celery |
| Machine Learning | TensorFlow |
| NLP | Hugging Face Transformers |
| Data Processing | Pandas |
| ORM | SQLAlchemy |
| Deployment | Docker |
| Reverse Proxy | Nginx |

## 🏗 Architecture

The platform follows a Modular Flask Monolith architecture with background workers.

Components

• Flask
• Celery
• Redis
• PostgreSQL
• TensorFlow
• Transformers

See:

docs/PRODUCTION_BLUEPRINT.md

## 📖 Documentation

- Production Blueprint
- Implementation Roadmap
- Architecture Decision Record

## 📂 Project Structure

```text
AI-Analytics-Hub-ML
│
├── ai_analytics_hub/
├── deploy/
├── docs/
├── migrations/
├── tests/
├── README.md
├── docker-compose.yml
├── pyproject.toml
└── wsgi.py
```## 🚀 Installation

```bash
git clone https://github.com/ahmadniazi0381-dev/AI-Analytics-Hub-ML.git

cd AI-Analytics-Hub-ML

python -m venv .venv

source .venv/bin/activate
```

Windows

```powershell
.venv\Scripts\activate
```

Install packages

```bash
pip install -e .
```

Run

```bash
flask run
```

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
