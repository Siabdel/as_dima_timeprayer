# syntax=docker/dockerfile:1
# =============================================================================
# Backend Django — image multi-stage
#   * target "dev"  : docker compose (runserver, hot-reload, outils de test)
#   * target "prod" : gunicorn + dépendances de production uniquement
# =============================================================================

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dépendances système : compilation éventuelle des paquets (psycopg, cryptography…)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Utilisateur applicatif non root
RUN addgroup --system app && adduser --system --ingroup app app

# Dépendances Python (couche mise en cache tant que requirements/ ne change pas)
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/dev.txt

# ----------------------------------------------------------------- dev -------
FROM base AS dev
COPY --chown=app:app . .
USER app
EXPOSE 8000

# ----------------------------------------------------------------- prod ------
FROM base AS prod
RUN pip install --no-cache-dir -r requirements/prod.txt
COPY --chown=app:app . .
USER app
EXPOSE 8000
