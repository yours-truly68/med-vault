# -----------------------------------------------------------------------------
# Stage 1: Base & Dependencies
# -----------------------------------------------------------------------------
FROM node:22-alpine AS base

WORKDIR /app

# Enable Corepack and copy dependency manifests
RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./

# Activate exact pnpm version specified in package.json packageManager field
RUN corepack prepare --activate

# Install dependencies with frozen lockfile
RUN pnpm install --frozen-lockfile

# -----------------------------------------------------------------------------
# Stage 2: Builder
# -----------------------------------------------------------------------------
FROM base AS builder

WORKDIR /app

COPY . .

ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

RUN pnpm run build

# -----------------------------------------------------------------------------
# Stage 3: Production Runner
# -----------------------------------------------------------------------------
FROM node:22-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Install curl for container healthchecks
RUN apk add --no-cache curl

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy static assets and standalone build output
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

CMD ["node", "server.js"]
