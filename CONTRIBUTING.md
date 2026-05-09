# Contributing to BookWith

開発に参加していただきありがとうございます。本ドキュメントは、PR を出す前に必ず一読してください。

## 開発フロー

```bash
# 依存インストール
pnpm install
cd apps/api && make configure && cd -

# pre-commit フック設定（必須）
pre-commit install

# 起動
pnpm dev          # 並列で API + Reader

# テスト
cd apps/api && make test
pnpm -F @flow/reader run ts:check
pnpm -F @flow/reader run lint:eslint
```

### Local テスト確認手順

```bash
# 1) .env を例から作る（実 API キーは Secret Manager から取得）
cp apps/api/src/config/.env.example apps/api/src/config/.env
# 2) 必要に応じて以下を上書き
#    AUTH_DEV_BYPASS=true
#    AUTH_DEV_BYPASS_USER_ID=11111111-1111-1111-1111-111111111111

# 3) Docker で Weaviate / GCS emulator を起動
cd apps/api && make docker.up

# 4) 単体テスト
make test

# 5) lint / format
make lint            # mypy + pre-commit
make lint.fix        # ruff --fix + ruff format

# 6) シークレットスキャン（任意）
make secret-scan

# 7) 依存脆弱性スキャン（任意）
make audit
```

### フロント側の OpenAPI 型再生成

本番では `/openapi.json` を 404 にしているため、ローカル or staging 経由で：

```bash
# API を別ターミナルで起動
cd apps/api && make run

# 別ターミナルでフロントの型再生成
pnpm -F @flow/reader run openapi:ts
```

## セキュリティ規約（必読）

セキュリティレビュー（2026-05-05）に基づき、以下のルールが強制されています：

### バックエンド (apps/api)

1. **認証は `Depends(get_current_user)` で全ルーター強制**: 個別ハンドラで省略しないこと
2. **`user_id` をリクエストから受け取らない**: 認証 principal から取得する
3. **リソース取得は `find_by_id_for_user(id, user_id)` 経由**: `find_by_id` だけの取得は禁止
4. **取得後にエンティティの `assert_owned_by(user_id)` を呼ぶ**: 二重防御
5. **エラーは固定文言**: `HTTPException(500, str(e))` は禁止。`logger.exception` でサーバ側ログのみ
6. **Pydantic スキーマは `BaseRequestSchemaModel` を継承**: `extra='forbid'` でオーバーポストを拒否
7. **値オブジェクトは `sanitize_plain_text` 経由**: HTML タグ・制御文字を除去
8. **Cloud TTS / GCS 等の外部入出力は allow-list**: ファイル MIME / プロトコル / ホストを限定

### フロントエンド (apps/reader)

1. **EPUB iframe は `allowScriptedContent: false`**: epub.js のスクリプト実行は禁止
2. **`?src=` 経由の取り込みは `isAllowedRemoteImportUrl` で検証**: confirm + Content-Type + size cap
3. **Sentry DSN はハードコードしない**: 環境変数経由
4. **API 呼出は `apiClient` / `fetcher` 経由**: Bearer Token を統一管理
5. **`window` への global 露出は dev のみ**: production ビルドで隔離

### 環境変数

- `.env` は **絶対にコミットしない**（`.gitignore` 二重防御済み）
- 本番では `assert_production_ready` で必須項目を検証
- Supabase JWT secret / OpenAI / Gemini / LangSmith キーは Secret Manager 経由

## PR チェックリスト

PR を出す前に以下を確認してください：

- [ ] `pre-commit run --all-files` が通る（gitleaks / ruff / ruff-format / poetry-check）
- [ ] `make test` が通る（バックエンドテスト）
- [ ] `pnpm -F @flow/reader run ts:check` が通る（フロント型チェック）
- [ ] 認可が必要なエンドポイントに `Depends(require_user_id)` が付いている
- [ ] 新規 schema が `BaseRequestSchemaModel` を継承している
- [ ] 新規エンドポイントの認可マトリクス（401 / 403 / 200）テストがある
- [ ] エラーレスポンスに内部実装が漏れていない
- [ ] `.env*` を変更していない / 新たに作っていない

## コミットメッセージ

[Conventional Commits](https://www.conventionalcommits.org/) を推奨：

- `feat(api): add ...`
- `fix(api): handle null in ...`
- `chore(deps): bump ...`
- `docs(security): update ...`
- `test(usecase): cover ...`

## セキュリティ報告

脆弱性を発見した場合は、公開 issue ではなく [SECURITY.md](./SECURITY.md) の手順に従ってください。

## 参考ドキュメント

- [`SECURITY.md`](./SECURITY.md) — 脆弱性報告ポリシー
- [`apps/api/SECURITY.md`](./apps/api/SECURITY.md) — API 側のセキュリティ設計
- [`apps/api/README.md`](./apps/api/README.md) — API のセットアップとエンドポイント一覧
- [`apps/reader/README.md`](./apps/reader/README.md) — フロントのセットアップと Auth 統合例
- [`CHANGELOG.md`](./CHANGELOG.md) — 変更履歴
- [`.003_local_temp_docs/security-fixes/`](./.003_local_temp_docs/security-fixes/) — セキュリティ修正詳細
