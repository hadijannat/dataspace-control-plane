# syntax=docker/dockerfile:1
#
# node-build.Dockerfile — Shared Node.js build base image.
# Used as a FROM target in web-console Dockerfile for the build stage.
#
# Pin to digest in release builds by passing NODE_DIGEST via Bake variable.
# Example usage:
#   FROM ghcr.io/your-org/dataspace-control-plane/base/node-build:20 AS builder
#
# Build with:
#   docker buildx build -f infra/docker/images/base/node-build.Dockerfile \
#     --build-arg NODE_VERSION=20 \
#     --build-arg NODE_DIGEST="@sha256:..." \
#     -t ghcr.io/your-org/dataspace-control-plane/node-build:20 .

ARG NODE_VERSION=20
ARG NODE_DIGEST=""

FROM node:${NODE_VERSION}-alpine${NODE_DIGEST:+@${NODE_DIGEST}} AS node-build

# Create non-root user for the build stage
RUN addgroup -g 1001 -S nodejs && \
    adduser -S builder -u 1001 -G nodejs

# Install common build tools
RUN apk add --no-cache \
    git \
    python3 \
    make \
    g++

ENV NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production
