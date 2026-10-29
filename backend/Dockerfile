# ==============================================================================
# Dhruva.AI V2 — Multi-Stage Production Dockerfile (Render / Multi-Cloud)
# Target: Python 3.12, Uvicorn, Non-Root Execution (UID 10001), Minimal Footprint
# ==============================================================================

# ------------------------------------------------------------------------------
# STAGE 1: Dependency Builder
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install system build dependencies required for C-extensions (psycopg, argon2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml to install project dependencies
COPY pyproject.toml .

# Upgrade pip and install wheel packages into /install prefix
RUN pip install --upgrade pip setuptools wheel && \
    pip install --prefix=/install .

# ------------------------------------------------------------------------------
# STAGE 2: Hardened Production Runtime
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS runner

LABEL maintainer="Dhruva.AI Core Engineering <platform@dhruva.ai>" \
      version="2.0.0" \
      description="Dhruva.AI V2 Multi-Tenant Core Intelligence Backend"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    ENVIRONMENT=production

WORKDIR /app

# Install minimal runtime shared libraries (libpq for PostgreSQL, curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create secure non-root user and group (Principle of Least Privilege)
RUN groupadd -r -g 10001 appgroup && \
    useradd -r -u 10001 -g appgroup -d /app -s /sbin/nologin appuser

# Copy installed Python packages from builder stage
COPY --from=builder /install /usr/local

# Copy application code and database migration manifests
COPY alembic.ini ./
COPY alembic ./alembic
COPY src ./src

# Set secure permissions ensuring non-root user owns the application directory
RUN chown -R appuser:appgroup /app && \
    chmod -R 755 /app

# Drop root privileges
USER 10001

# Container Liveness Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

EXPOSE 8000

# Start Uvicorn ASGI server with forwarder proxy headers support
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2 --proxy-headers --forwarded-allow-ips '*'"]
