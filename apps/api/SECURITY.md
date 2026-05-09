# API Security Configuration

このドキュメントは BookWith API（FastAPI）でセキュリティレビュー対応の結果として導入された
環境変数・ミドルウェア・運用上の注意点をまとめたものです。

## 脅威モデル

### 保護対象

- **書籍コンテンツ**: ユーザーがアップロードした EPUB と派生メタデータ（著作権物を含むため、他ユーザーへの漏洩は重大）
- **チャット履歴**: ユーザーと AI のやり取り全文（個人情報や思考過程を含み得る）
- **ハイライト・注釈**: ユーザーが本に付けたメモ（個人の思想・健康情報等が含まれ得る）
- **ポッドキャスト・音声**: ユーザー固有の派生コンテンツ
- **API キー**: OpenAI / Gemini / LangSmith / Cloud TTS（被害が金銭で出る）

### 想定する攻撃者の能力

- インターネット上の任意のクライアント（未認証含む）
- Supabase Auth で正規にアカウントを作成できる悪意あるユーザー（user_A の token で user_B のリソースを狙う）
- 攻撃者作成の悪意ある EPUB をユーザーに踏ませることができる第三者（XXE / XSS / プロンプトインジェクション素材を仕込める）
- 公開された GitHub リポジトリの履歴を全件解析できる

### 保護されないもの

- バックエンド・フロント両方のサーバー本体への root レベル侵入（インフラ層の問題）
- Supabase / GCS / Weaviate プロバイダ自体の脆弱性
- ユーザーの認証情報をフィッシングで盗まれた場合の被害（多要素認証は別マイルストーン）

### 主要な防御層

1. **認証**: Supabase JWT（HS256）+ FastAPI `Depends(get_current_user)` を全ルーター強制
2. **認可**: Repository / UseCase の二重 owner 検証 + ドメインエンティティの `assert_owned_by`
3. **入力**: Pydantic `max_length` + 値オブジェクトの HTML サニタイズ + EPUB ZIP マジック検証
4. **レート制限**: slowapi `EXPENSIVE_LIMIT` / `UPLOAD_LIMIT` + ボディサイズ ASGI ハードキャップ
5. **データ層**: Supabase RLS（`auth.uid() = user_id`）+ Weaviate per-tenant 分離 + auto_tenant_creation OFF
6. **アウトバウンド**: EPUB 外部 fetch を allow-list 必須 + プライベート IP 拒否 + 30s タイムアウト
7. **観測**: SecurityHeadersMiddleware + Sentry（DSN 環境変数経由）+ gitleaks の週次フルスキャン



## 必須環境変数（本番）

| 変数 | 説明 | 例 |
|---|---|---|
| `ENVIRONMENT` | `production` / `staging` / `development` | `production` |
| `AUTH_DEV_BYPASS` | 認証バイパスフラグ。本番では必ず `false` | `false` |
| `SUPABASE_JWT_SECRET` | Supabase Auth の HS256 署名検証鍵 | `supabase status` で取得 |
| `SUPABASE_JWT_AUDIENCE` | Supabase JWT の audience | `authenticated` |
| `SUPABASE_JWT_ALGORITHMS` | 許可アルゴリズム | `HS256` |
| `SUPABASE_JWT_ISSUER` | issuer pinning（設定時のみ `iss` を厳密検証） | `https://abc123.supabase.co/auth/v1` |
| `SUPABASE_JWT_LEEWAY_SECONDS` | クロックスキュー許容秒数（0〜300） | `10` |
| `CORS_ALLOW_ORIGINS` | CORS allow-list（カンマ区切り） | `https://app.bookwith.example` |
| `SQL_ECHO` | SQLAlchemy echo（本番は false） | `false` |
| `WEAVIATE_URL` | Weaviate クラウドの URL | `https://your-cluster.weaviate.network` |
| `WEAVIATE_API_KEY` | Weaviate Auth API キー | （Weaviate Cloud で発行） |
| `WEAVIATE_AUTO_TENANT_CREATION` | テナント自動作成を許可するか | `false` |
| `EPUB_FETCH_ALLOWED_HOSTS` | 外部 EPUB fetch 許可ホスト | （空 = 完全禁止） |
| `AUDIO_BGM_DIRS` | 音声 BGM 参照可能ディレクトリ | `/app/assets/bgm` |
| `AUDIO_OUTPUT_DIRS` | 音声出力許可ディレクトリ | `/app/audio` |
| `MAX_UPLOAD_BYTES` | アップロード上限（バイト） | `26214400` |
| `MAX_CHAPTERS` | ポッドキャスト用チャプター上限 | `15` |
| `GCS_SIGNED_URL_EXPIRES_SECONDS` | GCS 署名 URL の有効期限 | `600` |
| `SSE_STREAM_TIMEOUT_SECONDS` | SSE ストリーム全体のタイムアウト（B-2 対策、10〜600 秒） | `180` |

## アーキテクチャの要点

### 認証フロー（CR-1）

1. クライアントは Supabase Auth で取得した JWT を `Authorization: Bearer <token>` で送信。
2. `src/presentation/api/auth/dependencies.py:get_current_user` が JWT を検証。
3. 全ルーターは `setup_routes` で `Depends(get_current_user)` を強制適用。
4. ハンドラは `Depends(require_user_id)` で user_id（UUID）を取得。

### 認可（CR-3）

- リポジトリには `find_by_id_for_user` / `delete_for_user` / `bulk_delete_for_user` を追加。
- ユースケースは `find_by_id_for_user` でリソースを取得し、所有者でなければ 403。
- メッセージは chat_id を経由した join で所有者検証。

### レート制限（H-1）

- `slowapi` を統合。`src/presentation/api/middleware/rate_limit.py`。
- key は認証 user_id 優先。未認証は IP fallback。
- `EXPENSIVE_LIMIT="20/minute"`、`UPLOAD_LIMIT="10/minute"`、デフォルト `120/minute`。

### EPUB 処理の堅牢化（CR-6）

- `defusedxml` を依存追加。`book_content_store.py` で参照。
- `extract_chapters_usecase.py` の HTTP fetch にタイムアウト・サイズ・プライベート IP/リダイレクト禁止。
- 外部 fetch は `EPUB_FETCH_ALLOWED_HOSTS` 必須（空なら完全禁止）。

### Supabase RLS（H-21）

- `supabase/migrations/20260505000000_enable_rls_policies.sql` で全テーブルに RLS を有効化。
- `auth.uid() = user_id` を必須条件にしている（messages / annotations は join 経由）。
- FastAPI が SERVICE_ROLE_KEY で接続する場合は RLS をバイパスするため、API 側の所有者検証も必須。

## デプロイ前チェックリスト

- [ ] Supabase 側で auth.uid() ベースの RLS が有効か確認
- [ ] `apps/api/src/config/.env` から OpenAI / Gemini / LangSmith のキーを削除し、Secret Manager 等で注入
- [ ] `pre-commit install` 後、`pre-commit run --all-files` で gitleaks がクリーンか確認
- [ ] `poetry run alembic upgrade head` を CI で必須化
- [ ] `poetry run pytest tests/` で認可テストが通るか確認
- [ ] フロントは `pnpm openapi:ts` でスキーマ再生成
- [ ] フロント本番ビルドが Sentry DSN 設定済みか確認
- [ ] CDN / Reverse proxy 側でも HTTPS / HSTS / CSP が機能しているか確認
- [ ] `MAX_UPLOAD_BYTES` が 100 MiB 以下に設定されているか（`assert_production_ready` で hard cap 検証あり）
- [ ] `SUPABASE_JWT_ISSUER` を Supabase の発行 URL に設定（issuer pinning による多層防御）
- [ ] `bash scripts/check-history-leaks.sh` を実行し、git 履歴 + `.deepsec/` 等オフトラック領域にも実 API キーが残っていないか確認

## モニタリング推奨

- レート制限ヒット時の 429 ログ
- 認証失敗（401）の急増
- ポッドキャスト生成の status=PENDING 滞留
- Weaviate のテナント数増加（自動作成 OFF なので増えない想定）
- GCS の object 数とサイズ

## 既知の運用課題（残作業）

- フロント依存のメジャーアップデート（Sentry v7→v8/9、`next-pwa` 移行、`formidable` 更新）
- Alembic 初期 migration のスクリプト生成（`alembic revision --autogenerate -m "initial"`）
- Supabase Auth 統合の本格化（client SDK の組み込み、token refresh、ログイン画面）
- 認可マトリクスの本格テスト（user_A の token で user_B のリソースが 403 になること）
