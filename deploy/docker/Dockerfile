FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY ai_analytics_hub ./ai_analytics_hub
COPY wsgi.py celery_worker.py ./

RUN pip install --upgrade pip && pip install .

COPY . .

EXPOSE 5000
