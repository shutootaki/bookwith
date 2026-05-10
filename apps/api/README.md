# BookWith API

FastAPI / Python 3.13 ベースのバックエンド。Supabase（Postgres + Auth）、Weaviate、GCS、OpenAI、Gemini、Cloud TTS と統合する。

## クイックスタート

```bash
# 1) 依存インストール（推奨：リポジトリルートから JS + Python を一括）
cd ../.. && pnpm setup
# Python 依存だけ再同期したいなら
pnpm setup:api
# apps/api 単独でやるなら
make configure          # uv sync --frozen と等価

# 2) 環境変数の用意（src/config/.env を編集）
cp src/config/.env.example src/config/.env
# - SUPABASE_JWT_SECRET（本番では必須）
# - OPENAI_API_KEY、GEMINI_API_KEY
# - DATABASE_URL
# - CORS_ALLOW_ORIGINS

# 3) ルートから一括起動を推奨（Docker services + API + Reader を並列）
cd ../.. && pnpm dev:api    # API + Docker のみ起動したい場合
# 全部起動するなら
cd ../.. && pnpm dev

# --- ここから単独操作（apps/api 配下） ---

# Docker（Weaviate + GCS emulator）のみ起動
make docker.up

# API のみ起動
make run

# テスト
make test               # または ルートから `pnpm test`
make typecheck          # mypy 単独 / または ルートから `pnpm typecheck`
make lint               # mypy + pre-commit
make lint.fix           # ruff --fix + ruff format
make clean              # __pycache__ / .mypy_cache 等を削除

# Alembic
make migrate            # 適用
make migrate.gen MSG="describe change"  # 自動生成
```

## 認証

- 認証ミドルウェア: `src/presentation/api/auth/dependencies.py`
- 全ルーターに `Depends(get_current_user)` を強制適用（`src/presentation/api/routes.py`）
- Supabase Auth 発行の HS256 JWT を `Authorization: Bearer <token>` で受け取る
- 開発時は `AUTH_DEV_BYPASS=true` + `AUTH_DEV_BYPASS_USER_ID=<UUID>` で固定ユーザーに固定可能（本番では絶対 false）

詳細は [SECURITY.md](./SECURITY.md) を参照。

## レート制限

- ASGI: `slowapi` ベースのデフォルト `120/minute`（per user / IP）
- 明示制限: `POST /messages` に `expensive_limit()=20/minute` を適用
- 上限到達時は `429 Too Many Requests`

## エンドポイント

| Method | Path | 認証 | 概要 |
|---|---|---|---|
| GET | `/books/me` | 必要 | 認証ユーザーの本一覧 |
| POST | `/books` | 必要 | 本を作成（base64 EPUB） |
| GET | `/books/{book_id}` | 必要 | 本の詳細 |
| GET | `/books/{book_id}/file` | 必要 | GCS 署名 URL（10 分） |
| PUT | `/books/{book_id}` | 必要 | 本の更新 |
| DELETE | `/books/{book_id}` | 必要 | 本の削除 |
| DELETE | `/books/bulk-delete` | 必要 | 一括削除（最大 100 件） |
| GET | `/books/covers` | 必要 | カバー署名 URL 一覧 |
| GET | `/chats/me` | 必要 | 認証ユーザーのチャット一覧 |
| POST | `/chats` | 必要 | チャット作成 |
| GET | `/chats/{chat_id}` | 必要 | チャット詳細 |
| PATCH | `/chats/{chat_id}/title` | 必要 | タイトル更新 |
| DELETE | `/chats/{chat_id}` | 必要 | チャット削除 |
| POST | `/messages` | 必要（厳しめ rate） | LLM ストリーム返信 |
| GET | `/messages/{chat_id}` | 必要 | メッセージ一覧 |
| DELETE | `/messages/bulk` | 必要 | 一括削除（最大 200 件） |
| DELETE | `/messages/{message_id}` | 必要 | 単一削除 |
| PUT | `/books/{book_id}/annotations` | 必要 | 注釈同期 |
| POST | `/podcasts` | 必要 | ポッドキャスト生成開始 |
| GET | `/podcasts/{podcast_id}` | 必要 | ポッドキャスト詳細 |
| GET | `/podcasts/{podcast_id}/status` | 必要 | 生成ステータス |
| POST | `/podcasts/{podcast_id}/retry` | 必要 | 失敗時リトライ |
| GET | `/podcasts/book/{book_id}` | 必要 | 本のポッドキャスト一覧 |
| POST | `/rag` | 必要 | EPUB ベクトルインデックス化 |

## ディレクトリ構造

```
src/
├── main.py                     # FastAPI app + ライフサイクル
├── config/                     # AppConfig / DB
├── domain/                     # エンティティ・値オブジェクト・リポジトリ IF
├── infrastructure/
│   ├── di/                     # FastAPI Depends 用プロバイダ
│   ├── postgres/               # SQLAlchemy リポジトリ実装
│   ├── memory/                 # Weaviate / OpenAI 関連
│   └── external/               # GCS / Gemini / Cloud TTS
├── usecase/                    # アプリケーション層
└── presentation/api/
    ├── auth/                   # CR-1 認証 Depends
    ├── handlers/               # FastAPI ルーター
    ├── middleware/             # body_size_limit / rate_limit / security_headers
    ├── schemas/                # Pydantic リクエスト/レスポンス
    └── error_messages/         # 例外ハンドラ + 固定文言

tests/
├── auth/                       # 認証 Depends
├── middleware/                 # Body size / security headers / rate limit
├── schemas/                    # スキーマバリデーション
└── domain/                     # 値オブジェクト + sanitize

alembic/                        # スキーマ migration
```

## セキュリティチェックリスト

[SECURITY.md](./SECURITY.md) を参照。`pre-commit run --all-files` と `pnpm test`（または `make test`）をデプロイ前に必ず実行する。
