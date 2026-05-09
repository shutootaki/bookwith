# Changelog

## Unreleased — Security hardening (2026-05-09)

セキュリティレビュー（`security-review-2026-05-05` および `security_review`）に基づく一括対応。

### Added

- **Authentication**: Supabase JWT 認証ミドルウェアを `apps/api/src/presentation/api/auth/dependencies.py` に追加。全ルーターで `Depends(get_current_user)` を強制適用。
- **Authorization**: 全リポジトリに `find_by_id_for_user` / `delete_for_user` / `bulk_delete_for_user` を追加。UseCase 層で所有者検証を行い、`Book.assert_owned_by` / `Podcast.assert_owned_by` で二重防御。
- **Rate limiting**: `slowapi` を統合し、`UPLOAD_LIMIT` / `EXPENSIVE_LIMIT` を設定。
- **Body size limit**: ASGI 段で `BodySizeLimitMiddleware` を追加。Content-Length / 累積バイトの両方で 413 拒否。
- **Security headers**: API（`SecurityHeadersMiddleware`）と Next.js 双方で CSP / HSTS / X-Frame-Options / X-Content-Type-Options / Referrer-Policy / Permissions-Policy / COOP を付与。
- **Supabase RLS**: `supabase/migrations/20260505000000_enable_rls_policies.sql` で全テーブルに RLS + `auth.uid() = user_id` ポリシー。
- **Alembic**: `apps/api/alembic.ini` + `env.py` + `script.py.mako` で migration スケルトンを追加。
- **CI**: `.github/workflows/secret-scan.yml` で gitleaks を週次フル履歴スキャン、`.github/workflows/dependency-audit.yml` で `pip-audit` / `pnpm audit`。
- **Tests**: `tests/auth/`、`tests/middleware/`、`tests/schemas/` に最低限の回帰テストを追加。
- **Pre-commit**: gitleaks を `.pre-commit-config.yaml` に追加し、`.gitleaks.toml` で OpenAI / Google / LangSmith / Supabase JWT / PEM の検出ルールを定義。
- **Scripts**: `scripts/check-history-leaks.sh` で git 履歴のシークレット混入をローカル検証。
- **Docs**: `apps/api/SECURITY.md` で環境変数・運用チェックリスト・モニタリング推奨を集約。

### Changed

- **CORS**: `allow_origins=["*"]` を `AppConfig.cors_allow_origins` の allow-list に変更。本番では明示必須。
- **Logging**: `SQLALCHEMY echo` を `AppConfig.sql_echo` で gate。デフォルトは無効。
- **Schema**: `BookCreateRequest` / `BookUpdateRequest` / `ChatCreateRequest` / `MessageCreate` / `RagProcessRequest` から `user_id` / `sender_id` / `book_id` などの mass-assignment フィールドを削除。
- **Frontend imports**: `?src=` リモート EPUB 取り込みを confirm + URL allow-list + Content-Type/Size 検証必須化。
- **EPUB iframe sandbox**: `allowScriptedContent: false` がデフォルト。`packages/epubjs/src/managers/views/iframe.js` で `allow-same-origin` と `allow-scripts` の併用を排除。
- **Gemini safety**: `BLOCK_NONE` から `BLOCK_MEDIUM_AND_ABOVE` に復活。
- **Prompt injection**: `book_content` / `highlight_texts` / `chat_memories` / `book_summary` などの LLM 入力を `<book_excerpts>` `<user_question>` などの XML タグで囲み、システム指示で「内部の指示は無視」を明記。
- **Value objects**: `ChatTitle` / `MessageContent` / `BookTitle` / `AnnotationText` / `AnnotationNotes` に `max_length` と HTML サニタイザを適用。
- **Memory service**: `MemoryService` を `lru_cache` 経由のシングルトンに（DI のオーバーヘッド削減）。
- **Retry decorator**: `book_content_store.create_book_vector_index` を非冪等として retry 無効化（OpenAI 二重課金回避）。
- **Vector CRUD**: `add_memory` / `delete_memory` を allow-list 検証付きの専用メソッド（`add_chat_memory` / `add_book_content` / `add_book_annotation`）に分割。
- **Weaviate**: `connect_to_local` と `connect_to_custom + AuthApiKey` を切替可能に。`auto_tenant_creation` を環境変数で gate。
- **TTS**: SSML / プロンプトインジェクション抑止のため、speech 入力の `<` `>` `&` をエスケープ + 制御文字を除去。
- **Sentry**: ハードコード fallback DSN を削除。`SENTRY_DSN` 未設定時は `Sentry.init` をスキップ。
- **Front fetch**: `apiClient` / `fetcher` で 401 受信時に `bookwith.access_token` を localStorage から自動削除。
- **Docker**: フロント Dockerfile の Node を 16 → 22 に更新。`netlify.toml` も同様。`.dockerignore` に `.env*` を追加。
- **Supabase Auth config**: `minimum_password_length` を 12、`password_requirements` を `lower_upper_letters_digits_symbols`、`enable_confirmations` を true、`secure_password_change` を true に。

### Fixed

- **B-1**: `BookDTO.to_entity` で `None` を `"None"` 文字列化していたバグを修正。
- **B-2**: `gemini_client.summarize_text` の到達不能 `logger.error` を修正。
- **B-3**: `_filter_chapters` の `max_chapter_length` 誤用を `max_chapters` に分離。
- **B-4**: `update_book_usecase` の cfi/percentage 部分更新ロジックを修正。
- **B-5**: `delete_message_usecase.execute_bulk` の戻り値命名不整合を修正。
- **B-6**: `BaseVectorStore` の lazy init をスレッド安全な double-checked locking に変更。
- **B-7**: `vectorize_text_background` / `summarize_and_vectorize_background` をスレッドにオフロード。
- **B-8**: `LibraryContainer` の render 中 `booksMutate()` を `useEffect` に移動。
- **B-9**: `ChatPane.updateAssistantMessage` を非破壊更新に修正。
- **B-10**: `summarization` の chat-scoped lock で重複挿入防止。
- **B-11/B-12**: `AnnotationId` / `BookId` を strict UUID + 小文字正規化。
- **B-13**: `book_repository.save` の `on_conflict_do_update` から `id` / `user_id` / `created_at` を除外。
- **B-14**: `ChatTitle` の空文字を弾く。
- **B-15**: `chat_repository.save` の部分更新で `book_id=None` を上書きしない。
- **B-16**: `decodeURIComponent` の URIError を捕捉し UI 固まり防止。
- **H-07**: annotation 同期の「最初の 1 件しか Weaviate から削除されない」バグを全件 loop に修正。
- **H-11**: `DELETE /messages/bulk` のルート順序を `/{message_id}` より先に宣言。
- **M-01**: cover_image を JPEG/PNG/WebP のマジックナンバー検証で限定（SVG 拒否）。
- **M-05/M-08**: `_filter_chapters` の上限を `max_chapters` で正しく評価。
- **M-18**: `displayFromSelector` の CSS attribute 補間を `CSS.escape` で安全化。

### Subsequent iterations (2026-05-09 拡張対応)

5〜26 イテレーションでの追補:

- **H-1 強化**: `BodySizeLimitMiddleware` で Content-Length / 累積バイト両方の 413 ガードを追加。`POST /messages` / `POST /rag` / `POST /podcasts` に `@expensive_limit()` (20/minute) を明示適用
- **M-02**: `MemoryService` を `lru_cache` のシングルトンに統一
- **H-09**: `retry_decorator` に `idempotent` / `non_retryable_exceptions` を追加し、`book_content_store.create_book_vector_index` を非冪等として retry 無効化
- **M-17**: `window.podcastSeekFunction` を `bookwithPodcastSeek` に名前空間化し、production では露出しない
- **M-15**: `Base.metadata.create_all` を `is_production` + `sqlalchemy_auto_create` で gate。Alembic 雛形を追加
- **AppConfig 強化**: `assert_production_ready`（CR-1/CR-2/H-21 必須項目の起動時 fail-fast）+ `environment` の strict 検証（`production` / `staging` / `development` 以外を拒否）
- **DDD 二重防御**: Book / Chat / Podcast エンティティに `assert_owned_by`、Annotation に `assert_belongs_to_book` を追加し、UseCase クエリと併せて 4 段階認可（Repository / UseCase / Domain / RLS）に
- **Pydantic strict mode**: `BaseRequestSchemaModel`（`extra='forbid'`）に Book / Chat / Message / Podcast / Annotation / Rag のリクエストスキーマを移行
- **OpenAPI**: Bearer scheme を `securitySchemes` で明示し、フロントの型生成時に Authorization 必須が伝わる
- **Sentry**: `tracesSampleRate` を環境変数経由に（dev=1.0 / prod=0.1 デフォルト）
- **Frontend**: `apps/reader/src/lib/auth/token.ts` で Supabase Auth クライアントとの統合足場、`apiClient` / `fetcher` の 401 自動 logout、`?src=` の allow-list 検証

### Tests

合計 約 145 件のバックエンドテスト（auth / middleware / schemas / domain / usecase / infrastructure の 6 カテゴリ）を整備：

- 認証: token validation / dependencies / authenticated_user / production_guard / app_config_lists
- ミドルウェア: body_size_limit / security_headers / rate_limit / cors_guard / error_handlers
- スキーマ: book_schema / message_schema / annotation_schema / podcast_schema / error_messages
- ドメイン: text_sanitizer / value_objects / id_normalization / chat_assert_owner / annotation_belongs_to_book / podcast_status
- UseCase: chat_manager_title / book_owner_check / delete_message_bulk / extract_chapters_ssrf / synthesize_audio_sanitize / safe_block
- Infrastructure: retry_decorator / gcs_content_type / vector_crud_allow_list / audio_path_allow_list

### CI / Ops

- `.github/workflows/secret-scan.yml`（gitleaks 週次フル）
- `.github/workflows/dependency-audit.yml`（pip-audit / pnpm audit）
- `.github/dependabot.yml`（Actions / pip / npm の週次依存更新、関連 group まとめ）
- `.github/CODEOWNERS`（auth / middleware / config / RLS / CI / docs / Frontend 認証）
- `.github/ISSUE_TEMPLATE/config.yml`（脆弱性は Security Advisory へ誘導）
- `apps/api/Makefile` に `test` / `migrate` / `migrate.gen` / `secret-scan` / `audit` / `lint.fix`
- `scripts/check-history-leaks.sh`（gitleaks フルスキャン + git log -S grep のスクリプト）

### Documentation

- `SECURITY.md`（リポジトリルート）: Vulnerability reporting / Disclosure policy / 防御層概要 / Branch protection 推奨
- `apps/api/SECURITY.md`: 必須環境変数 / 認証フロー / レート制限 / 脅威モデル / デプロイチェックリスト
- `apps/api/README.md`: クイックスタート / エンドポイント一覧 / ディレクトリ構造
- `apps/reader/README.md`: クイックスタート / Supabase Auth 統合の最小コード例 / セキュリティ補足 / vitest 導入ガイド
- `CONTRIBUTING.md`: PR チェックリスト / セキュリティ規約 / コミット規約
- `apps/api/alembic/README.md`: Alembic 利用ガイド
- `.003_local_temp_docs/security-fixes/ROADMAP.md`: Day 0 / Week 1〜6 / 中長期の運用残作業チェックリスト

### Operations

- `/health`（liveness probe）と `/ready`（readiness probe）を追加（OpenAPI 非露出）
- `RequestIdMiddleware` で `X-Request-ID` を付与し、監査ログ / Sentry トレース連結に利用
- `apps/api/Dockerfile` の `HEALTHCHECK` を `/health` に切替（軽量化）
- `OpenAPI` に `securitySchemes.BearerAuth` を明示し、フロント型再生成時に Authorization 必須が伝わる

### Iteration 58 — ローカル開発の loopback バインド既定化 + `.dockerignore` 強化

- レビュー文書 `security_review/04_infra_supply_chain.md` の **4.4 [Low]** と **3.5 [Info]** に対応。
- **`apps/api/Makefile`** の `make run` を既定で `127.0.0.1` バインドに変更。`HOST ?= 127.0.0.1` 変数で上書き可能。LAN 公開が必要な場合は別ターゲット `make run.lan`（明示警告付き）。これで公衆 Wi-Fi での意図せぬ LAN 公開事故を防ぐ多層防御に。
- **`.dockerignore`** を強化:
  - `**/.env` / `**/.env.*`（`!**/.env.example` は許可）/ `**/.envrc` — 実 API キー混入を防止
  - `.git` / `.github` / `.husky` / `.cursor` / `.claude` / `.deepsec` — image に同梱不要な開発ツール
  - `**/.venv` / `**/__pycache__` / `**/.coverage` / `**/coverage.xml` — Python 内部リソース
  - `**/tests` / `**/*.test.ts` / `.003_local_temp_docs` — テスト・ドキュメント
- **意図**: `docker build .` の context にルート `/` が指定されたとき、`.env` 系ファイルや `.deepsec/` のセキュリティスナップショットが image に焼かれる事故を防ぐ防御層を確立。

### Iteration 57 — GitHub Actions 最小権限化と CI 失敗握り潰しの解消

- レビュー文書 `security_review/04_infra_supply_chain.md` の **5.4 / 5.5** に対応。
- **`.github/workflows/backend-ci.yml`** / **`.github/workflows/frontend-ci.yml`** に top-level + job-level で `permissions: contents: read` を追加。これにより `GITHUB_TOKEN` の write-all 権限が取れず、cache poisoning やリポジトリ書き込みを伴うサプライチェーン攻撃への防御層を強化。
- **`backend-ci.yml`** の Setup environment file ステップで `cp ... || true` を撤去し `set -euo pipefail` を追加。`.env.example` が消えていれば即 fail させて構成漏れを早期検出（5.4 [Medium] の握り潰し問題を解消）。
- **意図**: GitHub Actions のデフォルト権限はリポジトリ設定依存で意図せず広い権限を持つ可能性がある。各 workflow で `contents: read` を明示することで CIS / SLSA に沿った最小権限原則を実現。

### Iteration 56 — `.deepsec/` オフトラック領域のシークレット残置検出

- レビュー文書 `security_review/04_infra_supply_chain.md` の **1.5 [Medium]** を再精読。`.deepsec/data/bookwith/files/apps/api/src/config/.env.json` に DeepSec のファイルスナップショットとして **実 API キー（OpenAI / Gemini / LangSmith）が平文で残置** されていることを確認。git tracked ではないが PC 紛失・誤コピー時の流出経路。
- **`scripts/check-history-leaks.sh`** を拡張:
  - 既存の `git log -S` 検索に加え、`.deepsec/` 等 **オフトラック領域** も再帰 grep
  - `sk-proj-` / `AIzaSy` / `lsv2_pt_` 等の prefix を検出したらファイルパス付きで警告 + 終了コード 1
  - ローテートと sanitize/削除の操作を運用者に明示
- **`apps/api/SECURITY.md`** のデプロイ前チェックリストに `bash scripts/check-history-leaks.sh` の実行を追加。
- **意図**: 「git 履歴に無いから安全」と誤認しないため、ディスク上のオフトラックファイルも CI/手動運用で検出。これで漏洩経路の包括的なカバレッジに到達。

### Iteration 55 — L-01 (seed.py 本番ガード) の回帰テスト追加

- レビュー文書 `security_review/02_backend_infra.md` の L-01 を再精読。`seed_data()` の本番ガード実装は対応済みだが、回帰検出テストが欠けていたため追加。
- **`apps/api/tests/test_seed_production_guard.py`** を新規追加（3 ケース）:
  - `ENVIRONMENT=production` で `seed_data` 呼び出し → `RuntimeError`
  - production guard が `SessionLocal` 取得より **前** で短絡することを検証（DB に触れずに失敗する保証）
  - `ENVIRONMENT=development` では `seed_data` が正常通過（開発フローを壊さない）
- **意図**: `seed_data` の production guard が将来のリファクタで外れた場合（例: `is_production` チェックが削除される、または DB session が先に取得される実装変更）に即時検出。「DB に触らずに RuntimeError を投げる」という挙動を契約として固定。

### Iteration 54 — `Theme.tsx` の `dangerouslySetInnerHTML` への入力厳格化

- レビュー文書 `05_safe.md` の「現状で安全と確認できた」項目を再精読し、`Theme.tsx:84` で `generateCss(theme)` を `dangerouslySetInnerHTML` に流す経路の入力源を再検証。
- レビュー時の判断は「material-color-utilities が数値出力するため安全」だが、**`sourceColor` の経路は localStorage 経由でユーザー設定値**。CR-5 (EPUB iframe XSS) が将来再導入されたとき、攻撃者が `parent.localStorage` を改竄することで `sourceColor` に任意文字列を入れ、`generateCss` 経由の CSS 注入経路になり得る（多層防御の観点で footgun）。
- **`apps/reader/src/hooks/theme/useSourceColor.ts`** を強化:
  - `HEX_COLOR_RE = /^#[0-9a-fA-F]{6}$/` で厳密検証
  - `isValidSourceColor` を export し、`setSourceColor` の入力検証 + 読み取り時の検証を二重化
  - 不正値はデフォルト `#0ea5e9` にフォールバック
- **意図**: CR-5 の防御層が破られた場合の **n+1 段目の防御**。`05_safe.md` の注記「将来パレットキーをユーザー制御可能にすると CSS 注入の footgun」を実装側で先回りして閉塞。

### Iteration 53 — SECURITY.md と AppConfig の整合性検証テスト

- **`apps/api/tests/test_security_doc_consistency.py`** を新規追加。`apps/api/SECURITY.md` の環境変数表が AppConfig の本番関連 Field を網羅していることを CI で検証する。
- **3 ケース**:
  - `SECURITY.md` ファイル存在確認
  - 19 個の必須 env var（`ENVIRONMENT` / `SUPABASE_JWT_*` / `CORS_ALLOW_ORIGINS` / `WEAVIATE_*` / `MAX_*` / `SSE_STREAM_TIMEOUT_SECONDS` 等）がすべてドキュメント化されていること
  - AppConfig に新規追加された Field が `SECURITY.md` または「意図的に非公開」リストに登録されていること（漏れを CI で検出）
- **意図**: 「実装に新しいセキュリティ env var を追加したが SECURITY.md を更新し忘れる」という documentation drift を即時に検出。新人運用者が運用時に必要な情報を見落とさない仕組み。

### Iteration 52 — `MAX_UPLOAD_BYTES` の本番ハードキャップ + デプロイチェックリスト強化

- **`AppConfig.assert_production_ready`** に `MAX_UPLOAD_BYTES > 100 MiB` で `RuntimeError` の検証を追加。本番環境で誤って `MAX_UPLOAD_BYTES=1GB` のような極端な値が設定されたときのメモリ枯渇 DoS を fail-fast で防止。
- **`apps/api/tests/auth/test_app_config_production_guard.py`** に 2 ケース追加:
  - 1 GiB の `MAX_UPLOAD_BYTES` が本番で reject されること
  - 100 MiB ぴったりは許容されること（境界値テスト）
- **`apps/api/SECURITY.md`** のデプロイ前チェックリストに `MAX_UPLOAD_BYTES <= 100 MiB` と `SUPABASE_JWT_ISSUER` を追加（運用での見落としを防止）。
- **意図**: H-1 (rate limit + body size) と addendum B-1 (size limit) の追加防御層。設定値レベルでの本番ハードガード。

### Iteration 51 — Addendum B-1 (aiohttp timeout/size/redirect) の定数回帰検出

- レビュー文書 `security_review/00_addendum.md` の addendum B-1〜B-7 を全項目精読・実装突合。実装はすべて対応済みだが、**addendum B-1 の重要定数値が将来的に弱体化する事故** を検出するテストが欠けていたため追加。
- **`apps/api/tests/usecase/test_extract_chapters_ssrf.py`** に 4 ケース追加:
  - `_FETCH_TIMEOUT` の connect/total が None でなく、totalが 300 秒以下
  - `_FETCH_MAX_BYTES` が正で 100 MiB 以下
  - `_ALLOWED_SCHEMES == {"http", "https"}` を厳密ロック
  - `_download_remote_epub` が `session.get` に `allow_redirects=False` を必ず渡している（メタデータエンドポイントへの redirect 経由 SSRF を防止）
- **意図**: SSRF 防御の設定値が「弱体化リファクタ（timeout なし / size ∞ / allow_redirects=True 等）」で再導入される事故を即時検出する装置。

### Iteration 50 — B-3 (max_chapters 誤用) の回帰テスト追加

- レビュー文書 `04_bugs.md` の B-1〜B-16 を全項目精読・実装突合。`B-3 (max_chapter_length と max_chapters の混同)` は実装修正済みだが回帰検出テストが欠けていたため追加。
- **`apps/api/tests/usecase/test_filter_chapters.py`** を新規追加（5 ケース）:
  - 上限以下の入力は全件返す
  - 上限超過時は `max_chapters` 件に間引く
  - **誤って `max_chapter_length` (10000) を比較に使った場合** 20 件入力で間引きが発火しないことを明示的に弾く（B-3 の本質的なリグレッション検出）
  - カスタム max_chapters 値の尊重
  - 境界条件（入力数 == max_chapters）
- **意図**: `_filter_chapters` の責務は「Gemini への過剰投入を防ぐ間引き」。max_chapters と max_chapter_length を将来のリファクタで再混同する事故が起きた瞬間に検出する装置を追加。

### Iteration 49 — CR-1 認証ガードの網羅マトリクス

- レビュー文書 `01_critical.md` の CR-1〜CR-7 を全項目精読・突合。CR-3 の影響範囲（`POST /podcasts` / `POST /rag` / `PUT /books/{id}/annotations` / `DELETE /books/{id}` / `DELETE /books/bulk-delete`）に **未認証 401 テストが欠けていた** ため追加。
- **`apps/api/tests/auth/test_authorization_matrix.py`** に 6 ケース追加:
  - `POST /podcasts` 未認証 → 401（高額課金エンドポイント保護）
  - `GET /podcasts/{id}` 未認証 → 401
  - `POST /rag` 未認証 → 401（Embedding 大量呼出保護）
  - `PUT /books/{id}/annotations` 未認証 → 401（Mass Assignment 経路の遮断）
  - `DELETE /books/{id}` 未認証 → 401
  - `DELETE /books/bulk-delete` 未認証 → 401
- これで「全 router に `Depends(get_current_user)` が掛かっている」ことを横断マトリクスで保証。新規 router を追加した時に認証掛け忘れがあれば回帰テストで即検出できる。

### Iteration 48 — H-16 (Message chat-owner authorization) regression coverage

- レビュー文書 02_high.md の H-1 〜 H-21 を全項目精読・突合。実装抜けは無いことを確認しつつ、**回帰検出テストが欠けていた H-16** に専用テストを追加。
- **`apps/api/tests/infrastructure/test_message_repository_chat_owner.py`** を新規追加（3 ケース）:
  - `find_by_chat_id_for_user` が `ChatDTO` を join し、`user_id` を WHERE 句に含めること
  - `find_latest_by_chat_id_for_user` が同じ owner filter + `limit` を適用すること
  - legacy `find_by_chat_id` は意図的に owner filter を持たない（公開エンドポイントへの誤接続を防ぐ ガード テスト）
- **意図**: H-16 は「他人の `chat_id` を指定すれば被害者の最新会話履歴がコンテキスト混入し AI 応答経由で漏出する」という致命的 IDOR 経路。実装は対応済みだが、リファクタで `find_by_chat_id` の方を誤接続する事故を回帰検出する装置を追加。

### Iteration 47 — JWT issuer pinning + clock skew leeway

- **`AppConfig.supabase_jwt_issuer`** を追加（任意）。設定時は `_decode_jwt` で `iss` クレームを厳密一致検証し、別 Supabase プロジェクトで発行された JWT を弾く。
- **`AppConfig.supabase_jwt_leeway_seconds`** を追加（既定 10 秒、0〜300 秒で clamp）。クロックスキュー許容を設定可能化（PyJWT のデフォルトは 0 秒で本番運用にやや厳しいため）。
- **`apps/api/tests/auth/test_jwt_issuer_pinning.py`** を新規追加（5 ケース）:
  - 一致 issuer → 200
  - 別 issuer の JWT → 401（pinning が効くこと）
  - issuer 未設定なら従来通り通過（後方互換）
  - leeway 内のクロックスキュー → 200
  - leeway 超過の期限切れ → 401
- **`apps/api/SECURITY.md`** の環境変数表に `SUPABASE_JWT_ISSUER` / `SUPABASE_JWT_LEEWAY_SECONDS` を追加。

### Iteration 46 — LOW 残課題（外部ホスト依存と `index_tenant_mapping.json` の整理）

- **`apps/reader/src/components/library/ImportManager.tsx`** — 第三者ホスト `epubtest.org` から直接サンプル EPUB をダウンロードする UI を削除。レビュー文書 LOW 指摘「外部ホスト改竄時に CR-5 と合わせた 1-click XSS の入口」を解消。
- **`apps/reader/src/components/library/LibraryContainer.tsx`** — `ImportManager` の不要 props を整理（`updateProgress` / `setLoading` / `handleImportOperation` / `hasBooks` / `onImportComplete`）。
- **`apps/reader/src/lib/apiHandler/importHandlers.ts`** — `REMOTE_IMPORT_ALLOWED_HOSTS` から `epubtest.org` を削除。残るのは `standardebooks.org` / `archive.org` / 自前 `cdn.bookwith.app` のみ。
- **`apps/api/index_tenant_mapping.json`** を削除（コミット済みのランタイム状態ファイルを整理）。`.gitignore` に追加して再コミット防止。

### Iteration 45 — M-1 (Podcast retry TOCTOU) regression coverage

- **`apps/api/tests/infrastructure/test_podcast_optimistic_lock.py`** を新規追加。M-1（並行リトライによる二重課金）対策の `update_status_with_optimistic_lock` を 7 ケースで網羅:
  - 期待ステータス一致時の `True` 返却 + `commit()` 呼び出し
  - ステータス不一致時の `False` 返却 + `rollback()` 呼び出し（並行リトライ衝突）
  - `audio_url` 指定時の正常通過
  - 主要 4 状態遷移（FAILED→PENDING / PROCESSING→COMPLETED / PROCESSING→FAILED / PENDING→PROCESSING）の検証
- **目的**: 楽観的ロックの動作はすでに実装済みだが回帰検出テストが欠けていたため、レビュー文書 M-1 への対応を完全な状態に。

### Iteration 44 — Cache-Control for authenticated responses

- **`SecurityHeadersMiddleware`** が認証必須レスポンスに `Cache-Control: no-store` と `Pragma: no-cache` を付与。共有プロキシ・CDN・ブラウザキャッシュ経由のクロスユーザ漏洩を防止。
- **除外パス**: `/health`, `/ready`, `/docs`, `/redoc`, `/openapi.json`, `/metrics` は冪等な公開メタなのでキャッシュ抑止しない。
- **既存ハンドラ尊重**: 個別ハンドラが `Cache-Control` を明示している場合はそれを尊重（上書きしない）。
- **テスト**: `apps/api/tests/middleware/test_security_headers.py` に 3 ケース追加（認証パスへの no-store / 除外パス / 既存ヘッダー尊重）。

### Iteration 43 — B-2 (SSE DoS) full mitigation

- **`SSE_STREAM_TIMEOUT_SECONDS`** を `AppConfig` に追加（デフォルト 180 秒、10〜600 秒で clamp）。
- **`CreateMessageUseCaseImpl`** の `execute()` を `asyncio.timeout(stream_timeout_seconds)` でラップ。LLM ハング時はタイムアウトでストリームを強制終了し、ユーザーへ可視のマーカー (`[stream timed out — partial response saved]`) を送出する。
- **部分応答保存**: タイムアウト時もクライアント切断時も `finally` ブロックで生成済み chunk を `save_ai_message` で永続化。
- **DI**: `injection.py` の `get_create_message_usecase` で `AppConfig.get_config().sse_stream_timeout_seconds` を注入。
- **テスト**: `apps/api/tests/usecase/test_create_message_stream_timeout.py` で（1）正常完了、（2）タイムアウト時のマーカー + 部分保存、（3）一切 chunk を受けないタイムアウト時の保存スキップを検証。
- これにより `COMPLETION_REPORT.md` の Known limitation #1 が解消され、Addendum B-2 が完全対応となる。

### Operational tasks (out of code scope)

- 漏洩 API キー（OpenAI / Gemini / LangSmith）の即時ローテート
- `pre-commit install && pre-commit run --all-files` で gitleaks をクリーンに通過
- `poetry install` で新規依存（slowapi / PyJWT / defusedxml / lxml / alembic / pytest / httpx）を反映
- `alembic revision --autogenerate -m "initial"` で初期 migration を生成
- フロント依存メジャーアップデート（Sentry v7→v8/9、`next-pwa` 移行、`formidable` 更新）
- Supabase Auth 統合の本格化（`@supabase/supabase-js` 追加、フロントのログインフロー実装）
