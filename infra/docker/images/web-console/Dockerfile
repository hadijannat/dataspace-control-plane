# syntax=docker/dockerfile:1
#
# web-console — Multi-stage Dockerfile for the Next.js web console.
# Build context: repository root (docker buildx bake sets context = ".")
#
# Stages:
#   deps    — install production dependencies with npm ci
#   builder — build Next.js application (standalone output mode)
#   runtime — minimal runtime image with non-root nextjs user

# Stage 1: install production dependencies
FROM node:20-alpine AS deps

WORKDIR /build

# Copy package files for cache efficiency
COPY apps/web-console/package.json apps/web-console/package-lock.json* ./

# Install production dependencies only
RUN npm ci --omit=dev

# Stage 2: build
FROM node:20-alpine AS builder

WORKDIR /build

COPY --from=deps /build/node_modules ./node_modules
COPY apps/web-console/ ./

# Disable Next.js telemetry during build
ENV NEXT_TELEMETRY_DISABLED=1

# Build the Next.js application in standalone mode
# Requires next.config.js: output: 'standalone'
RUN npm run build

# Stage 3: minimal runtime
FROM node:20-alpine AS runtime

# Create dedicated non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001 -G nodejs

WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

# Copy standalone build output
COPY --from=builder /build/public ./public
COPY --from=builder --chown=nextjs:nodejs /build/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /build/.next/static ./.next/static

USER nextjs

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
  CMD wget -q --spider http://localhost:3000/api/health || exit 1

ENTRYPOINT ["node", "server.js"]
