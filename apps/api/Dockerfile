# M-14: API 用の多段ビルド Dockerfile（非 root 実行）。
# Python 3.13 + uv。

FROM python:3.13-slim AS builder

# uv の公式 distroless イメージから CLI バイナリを取得（pip 不要・SHA pin 容易）。
COPY --from=ghcr.io/astral-sh/uv:0.6.0 /uv /uvx /usr/local/bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/usr/local

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential libpq-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# ロックされた本番依存だけをシステム Python に同期する（dev/プロジェクト本体は除外）。
COPY pyproject.toml uv.lock /build/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY src /build/src

# ----------------------------------------
FROM python:3.13-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# 非 root ユーザー
RUN groupadd --system --gid 1001 app \
 && useradd --system --gid app --uid 1001 app

# 本番でも postgres / pydub などが要求するランタイム依存だけ持つ。
RUN apt-get update \
 && apt-get install -y --no-install-recommends libpq5 ffmpeg curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Builder で入れた site-packages をコピー。
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Application code
COPY --chown=app:app src /app/src

USER app

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/health >/dev/null || exit 1

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
