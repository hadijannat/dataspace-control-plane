# syntax=docker/dockerfile:1
#
# python-runtime.Dockerfile — Shared Python runtime base image.
# Used as a FROM target in application Dockerfiles for the runtime stage.
#
# Pin to digest in release builds by passing PYTHON_DIGEST via Bake variable.
# Example usage in an app Dockerfile:
#   FROM ghcr.io/your-org/dataspace-control-plane/base/python-runtime:3.12 AS runtime
#
# Build with:
#   docker buildx build -f infra/docker/images/base/python-runtime.Dockerfile \
#     --build-arg PYTHON_VERSION=3.12 \
#     --build-arg PYTHON_DIGEST="@sha256:..." \
#     -t ghcr.io/your-org/dataspace-control-plane/python-runtime:3.12 .

ARG PYTHON_VERSION=3.12
ARG PYTHON_DIGEST=""

# Build the image name dynamically to support digest pinning.
# When PYTHON_DIGEST is set, the image reference becomes python:3.12-slim@sha256:...
FROM python:${PYTHON_VERSION}-slim${PYTHON_DIGEST:+@${PYTHON_DIGEST}} AS python-runtime

# Install ca-certificates and create shared non-root user
RUN groupadd -r appuser && \
    useradd --no-log-init -r -g appuser -s /sbin/nologin appuser && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
      ca-certificates \
      curl && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install uv globally so app Dockerfiles can use it without reinstalling
RUN pip install --no-cache-dir uv==0.4.18
