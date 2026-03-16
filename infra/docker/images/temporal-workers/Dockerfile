# syntax=docker/dockerfile:1
#
# temporal-workers — Multi-stage Dockerfile for the Temporal workflow worker.
# Build context: repository root (docker buildx bake sets context = ".")
#
# Workers do not serve HTTP. No port is exposed.
# Health is checked via process liveness (pid 1 alive).

ARG PYTHON_BASE_IMAGE=python:3.12-slim

# Stage 1: dependency installation
FROM ${PYTHON_BASE_IMAGE} AS deps

WORKDIR /build

COPY apps/temporal-workers/pyproject.toml ./
COPY apps/temporal-workers/uv.lock* ./

RUN pip install --no-cache-dir uv==0.4.18 && \
    uv pip install --system --no-cache -r pyproject.toml

# Stage 2: runtime image
FROM ${PYTHON_BASE_IMAGE} AS runtime

RUN groupadd -r appuser && \
    useradd --no-log-init -r -g appuser -s /sbin/nologin appuser && \
    apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application source
COPY apps/temporal-workers/src /app/src

USER appuser

# Workers do not serve HTTP — no EXPOSE directive.
# Metrics may be served on port 8081 if the SDK prometheus integration is enabled;
# the Helm chart headless service targets this port for scraping.

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Health check via process existence — workers don't have an HTTP health endpoint.
# Kubernetes exec probe checks that pid 1 is alive.
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD python -c "import os; os.kill(1, 0)"

ENTRYPOINT ["python", "-m", "src.main"]
