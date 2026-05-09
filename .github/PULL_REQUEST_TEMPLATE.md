<!--
  PR を出す前に [CONTRIBUTING.md](../CONTRIBUTING.md) と [SECURITY.md](../SECURITY.md) を一読してください。
  脆弱性報告は公開 PR ではなく https://github.com/<owner>/<repo>/security/advisories/new から非公開で。
-->

## Summary

<!-- この PR で何を変更し、なぜ必要なのかを 1〜3 文で説明してください -->

## Type of change

- [ ] feat: 新機能
- [ ] fix: バグ修正
- [ ] refactor: 機能変更を伴わない再構成
- [ ] perf: パフォーマンス改善
- [ ] docs: ドキュメントのみ
- [ ] test: テストのみ
- [ ] chore: ビルド / 依存 / ツール
- [ ] security: セキュリティ修正（影響範囲を以下に明記）

## Security checklist

CONTRIBUTING.md のセキュリティ規約と整合していることを確認してください。

### Backend (apps/api)

- [ ] 新規エンドポイントに `Depends(require_user_id)` を付けた、または router 単位で認証必須化されている
- [ ] `user_id` をクライアントから受け取らず、認証 principal から取得している
- [ ] リソース取得は `find_by_id_for_user(id, user_id)` を経由している
- [ ] 取得後に `entity.assert_owned_by(user_id)` で二重防御している
- [ ] 例外メッセージに内部実装文字列を漏らしていない (`HTTPException(500, str(e))` 禁止)
- [ ] 新規 Pydantic スキーマは `BaseRequestSchemaModel`（または `extra='forbid'`）を継承
- [ ] 値オブジェクトを通すべきテキストは `sanitize_plain_text` を経由
- [ ] 外部 fetch / 任意パス IO は allow-list で制限

### Frontend (apps/reader)

- [ ] `EPUB iframe` 周りで `allowScriptedContent` を変えていない（CR-5）
- [ ] `?src=` 系の取り込みは `isAllowedRemoteImportUrl` で検証
- [ ] API 呼出は `apiClient` / `fetcher` を経由（直 fetch を避ける）
- [ ] Sentry / GTM / Supabase の DSN・ID をハードコードしていない
- [ ] `window` への global 露出は dev のみ

### General

- [ ] `.env*` を新規追加していない / 編集していない
- [ ] 新しいシークレットや API キーをコミットしていない
- [ ] `pre-commit run --all-files` が緑（gitleaks 含む）
- [ ] `make test`（バックエンド）と `pnpm -F @flow/reader run ts:check`（フロント）が緑
- [ ] 認可マトリクス（401 / 403 / 200）テストがあるか、回帰検出可能

## Impact / Risk

<!--
  本番へのデプロイ後、何が壊れる可能性があるか。ロールバック方針。
  パフォーマンス / 課金への影響。
-->

## Test plan

<!-- どうやって動作確認したか。手動テスト・新規テストケース・回帰確認 -->

## Related

<!-- Closes #issue-number / Refs SECURITY-REVIEW-XXX -->
