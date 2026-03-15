# syntax=docker/dockerfile:1
#
# provisioning-agent — Multi-stage Dockerfile for the provisioning agent.
# Build context: repository root (docker buildx bake sets context = ".")

# Stage 1: dependency installation
FROM python:3.12-slim AS deps

WORKDIR /build

COPY apps/provisioning-agent/pyproject.toml ./
COPY apps/provisioning-agent/uv.lock* ./

RUN pip install --no-cache-dir uv==0.4.18 && \
    uv pip install --system --no-cache -r pyproject.toml

# Stage 2: runtime image
FROM python:3.12-slim AS runtime

RUN groupadd -r appuser && \
    useradd --no-log-init -r -g appuser -s /sbin/nologin appuser && \
    apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin/uvicorn /usr/local/bin/uvicorn

# Copy application source
COPY apps/provisioning-agent/src /app/src

USER appuser

EXPOSE 8082

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8082

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8082/health')"

ENTRYPOINT ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8082"]
