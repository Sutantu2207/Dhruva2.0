# ==============================================================================
# Dhruva.AI V2 — Production Dockerfile
# Target: Python 3.12-slim, FastAPI, Uvicorn, SQLAlchemy Asyncio
# ==============================================================================

FROM python:3.12-slim

LABEL maintainer="Dhruva.AI Core Engineering <platform@dhruva.ai>" \
      version="2.0.0" \
      description="Dhruva.AI V2 Core Intelligence Backend"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    ENVIRONMENT=production \
    PYTHONPATH="/app:/usr/local/lib/python3.12/site-packages"

WORKDIR /app

# Install system dependencies (build-essential & libpq-dev for C extensions, curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libpq5 \
    build-essential \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications
COPY pyproject.toml requirements.txt ./

# Install pip dependencies with explicit C-extension compilation
RUN pip install --upgrade pip setuptools wheel && \
    pip install "greenlet>=3.0.3" "sqlalchemy[asyncio]>=2.0.30" && \
    pip install -r requirements.txt && \
    pip install .

# Copy application source and migration manifests
COPY alembic.ini ./
COPY alembic ./alembic
COPY src ./src

# Create non-root application user and persistent data volume directory
RUN groupadd -r -g 10001 appgroup && \
    useradd -r -u 10001 -g appgroup -d /app -s /sbin/nologin appuser && \
    mkdir -p /data && \
    chown -R appuser:appgroup /app /data && \
    chmod -R 775 /app /data

USER 10001

# Container Liveness Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

EXPOSE 8000

# Start Uvicorn ASGI server with single worker for zero-overhead fast boot
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --proxy-headers --forwarded-allow-ips '*'"]
