# M-14: API 用の多段ビルド Dockerfile（非 root 実行）。
# Python 3.13 + Poetry。

FROM python:3.13-slim AS builder

ENV POETRY_VERSION=1.8.3 \
    POETRY_HOME=/opt/poetry \
    POETRY_VIRTUALENVS_CREATE=false \
    PIP_NO_CACHE_DIR=on \
    PIP_DISABLE_PIP_VERSION_CHECK=on

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl build-essential libpq-dev \
 && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 - --version ${POETRY_VERSION}
ENV PATH="${POETRY_HOME}/bin:${PATH}"

WORKDIR /build

COPY pyproject.toml poetry.lock /build/
RUN poetry install --no-root --without dev

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
