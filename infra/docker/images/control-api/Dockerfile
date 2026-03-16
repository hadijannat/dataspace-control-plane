# syntax=docker/dockerfile:1
#
# control-api — Multi-stage Dockerfile for the FastAPI control-api service.
# Build context: repository root (docker buildx bake sets context = ".")
#
# Stages:
#   deps    — install Python dependencies with uv
#   runtime — minimal runtime image with non-root user

# Stage 1: dependency installation
FROM python:3.12-slim AS deps

WORKDIR /build

# Install uv for fast dependency resolution
COPY apps/control-api/pyproject.toml ./
# Copy lock file if present (uv.lock or requirements.lock)
COPY apps/control-api/uv.lock* ./

RUN pip install --no-cache-dir uv==0.4.18 && \
    uv pip install --system --no-cache -r pyproject.toml

# Stage 2: runtime image
FROM python:3.12-slim AS runtime

# Create non-root user and group
RUN groupadd -r appuser && \
    useradd --no-log-init -r -g appuser -s /sbin/nologin appuser && \
    apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from deps stage
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin/uvicorn /usr/local/bin/uvicorn

# Copy application source
COPY apps/control-api/app /app/app

# Drop privileges
USER appuser

EXPOSE 8080

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

ENTRYPOINT ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
