# Imagem de rascunho da prova de layout da feature 006 (não faz parte do produto).
FROM python:3.12-slim-bookworm
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       libreoffice-writer-nogui libreoffice-calc-nogui \
       fonts-crosextra-carlito fontconfig poppler-utils \
       libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir docxtpl weasyprint pyhanko pypdf
WORKDIR /work
