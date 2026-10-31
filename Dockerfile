# syntax=docker/dockerfile:1

# --- Ressources front-end : Node ne sert qu'à la construction, jamais à l'exécution.
FROM node:22-alpine AS assets
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY scripts/copy-vendor.mjs ./scripts/
COPY assets ./assets
COPY templates ./templates
COPY apps ./apps
RUN npm run build

# --- Base Python commune
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
# gettext : compilation des fichiers de traduction .po.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gettext \
    && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --uid 1000 daara
WORKDIR /app
COPY requirements ./requirements
RUN pip install -r requirements/base.txt

# --- Développement : le code est monté depuis l'hôte (voir docker-compose.yml).
FROM base AS dev
RUN pip install -r requirements/dev.txt
USER daara
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# --- Production
FROM base AS prod
RUN chown daara:daara /app
COPY --chown=daara:daara . .
COPY --from=assets --chown=daara:daara /app/static/dist ./static/dist
USER daara
RUN DJANGO_SETTINGS_MODULE=config.settings.prod SECRET_KEY=build-only \
    python manage.py compilemessages \
    && DJANGO_SETTINGS_MODULE=config.settings.prod SECRET_KEY=build-only \
    python manage.py collectstatic --noinput
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
