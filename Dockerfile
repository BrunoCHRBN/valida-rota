# syntax=docker/dockerfile:1

# ---- Estágio 1: bundle do frontend ----
FROM node:22-slim AS bundle
WORKDIR /src
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Estágio 2: runtime único (API + interface) ----
FROM python:3.14-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VALIDA_ROTA_DB=/data/valida_rota.db \
    VALIDA_ROTA_DIST=/app/frontend/dist

WORKDIR /app
COPY backend/pyproject.toml ./
COPY backend/app ./app
RUN pip install --no-cache-dir .

COPY --from=bundle /src/dist ./frontend/dist

RUN useradd --create-home --uid 10001 valida \
    && mkdir -p /data \
    && chown -R valida:valida /data /app
USER valida

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import os,sys,urllib.request; p=os.environ.get('PORT','8000'); sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:%s/api/health' % p, timeout=2).status == 200 else 1)"

# `PORT` é injetada por PaaS (Render usa 10000 por padrão); localmente cai em 8000.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
