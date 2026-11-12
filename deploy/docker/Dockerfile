# syntax=docker/dockerfile:1.7
# Imagem do SGP-P&D. Alvos: runtime (homologação e produção) e dev (testes e desenvolvimento).
ARG PYTHON_IMAGE=python:3.12-slim-bookworm

FROM ghcr.io/astral-sh/uv:0.11.17 AS uv

FROM ${PYTHON_IMAGE} AS builder
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON_DOWNLOADS=never
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libldap-dev libsasl2-dev \
    && rm -rf /var/lib/apt/lists/*
COPY --from=uv /uv /uvx /usr/local/bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

FROM builder AS builder-dev
RUN uv sync --frozen --no-install-project

FROM ${PYTHON_IMAGE} AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:${PATH}" \
    DJANGO_SETTINGS_MODULE=config.settings
RUN apt-get update \
    && apt-get install -y --no-install-recommends libldap-2.5-0 libsasl2-2 tzdata \
       libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 fontconfig \
       fonts-crosextra-carlito fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --uid 1000 --create-home --home-dir /home/sgp sgp
# Cópia de segurança (feature 014): pg_dump/pg_restore da mesma versão do servidor (17),
# do repositório oficial do PostgreSQL (o Debian bookworm traz só o cliente 15).
RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-common ca-certificates \
    && /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh -y \
    && apt-get install -y --no-install-recommends postgresql-client-17 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app

FROM base AS runtime
# Commit da versão implantada (evidência da validação, feature 014): --build-arg SGP_COMMIT=...
ARG SGP_COMMIT=""
ENV SGP_COMMIT=${SGP_COMMIT}
COPY --from=builder /opt/venv /opt/venv
COPY --chown=sgp:sgp . /app
RUN chmod +x /app/deploy/docker/entrypoint.sh \
    && DJANGO_SECRET_KEY=somente-para-collectstatic python manage.py collectstatic --noinput \
    && mkdir -p /app/var/media /app/var/backups && chown -R sgp:sgp /app/var /app/staticfiles
USER sgp
EXPOSE 8000
ENTRYPOINT ["/app/deploy/docker/entrypoint.sh"]
CMD ["web"]

FROM base AS dev
COPY --from=builder-dev /opt/venv /opt/venv
COPY --chown=sgp:sgp . /app
RUN chmod +x /app/deploy/docker/entrypoint.sh && mkdir -p /app/var/media /app/var/backups \
    && chown -R sgp:sgp /app/var
USER sgp
EXPOSE 8000
ENTRYPOINT ["/app/deploy/docker/entrypoint.sh"]
CMD ["web-dev"]
