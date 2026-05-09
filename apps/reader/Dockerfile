# https://github.com/vercel/turborepo/blob/a2a04ed4eba28602c7cdb36377c75a2f7007e90d/examples/with-docker/apps/web/Dockerfile

# M-13: node:16-alpine は EOL のため、全ステージで node:22-alpine を使用する。
FROM node:22-alpine AS builder
RUN apk add --no-cache libc6-compat
RUN apk update
WORKDIR /app
RUN yarn global add turbo
COPY . .
RUN turbo prune --scope=@flow/reader --docker

FROM node:22-alpine AS installer
RUN apk add --no-cache libc6-compat
RUN apk update
WORKDIR /app

COPY .gitignore .gitignore
COPY --from=builder /app/out/json/ .
COPY --from=builder /app/out/pnpm-*.yaml .
RUN corepack enable
RUN pnpm i --frozen-lockfile

COPY --from=builder /app/out/full/ .
COPY turbo.json turbo.json
COPY tsconfig.*json .

RUN DOCKER=1 pnpm -F reader build

FROM node:22-alpine AS runner
WORKDIR /app

# Don't run production as root
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs
USER nextjs

COPY --from=installer --chown=nextjs:nodejs /app/apps/reader/next.config.js .
COPY --from=installer --chown=nextjs:nodejs /app/apps/reader/package.json .

# Automatically leverage output traces to reduce image size
COPY --from=installer --chown=nextjs:nodejs /app/apps/reader/.next/standalone ./
COPY --from=installer --chown=nextjs:nodejs /app/apps/reader/.next/static ./apps/reader/.next/static

CMD node apps/reader/server.js
