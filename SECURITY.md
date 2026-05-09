# Security Policy

## Reporting a Vulnerability

BookWith に脆弱性を見つけた場合は、**公開 issue ではなく** 以下のいずれかでご連絡ください：

- **GitHub Security Advisory**: [このリポジトリの "Report a vulnerability"](../../security/advisories/new) から非公開で報告
- **Email**: `security@bookwith.example`（運用ドメイン確定後に更新）

報告に含めていただきたい情報：

1. 影響を受けるエンドポイント / コンポーネント / バージョン
2. 再現手順（最小限の PoC）
3. 想定される影響（情報漏洩 / 改竄 / 課金被害 / DoS 等）
4. 推奨される修正案（任意）

機微なシークレット（実 API キー、JWT 等）が漏洩している場合は、報告本文に貼らず、暗号化チャネル（GitHub Security Advisory の private comment）を使ってください。

## Disclosure Policy

- 受領後 **48 時間以内** に一次返信
- 修正が確定したら **15 営業日以内** にパッチをリリース
- リリース後 **7 日間** で報告者と相互に内容確認し、Advisory を公開
- CVE が必要な場合は GitHub 経由で発番

## Supported Versions

- `main` ブランチで対応する。リリースされたタグの旧版へのバックポートは個別判断。

## In-Scope

- `apps/api`（FastAPI バックエンド）
- `apps/reader`（Next.js フロントエンド）
- `packages/epubjs`（フォーク版 epub.js）
- `supabase/migrations`、`docker-compose.yml`、`.github/workflows`
- 認証・認可・入力検証・レート制限・依存ライブラリ脆弱性

## Out-of-Scope

- DoS by raw network flooding（CDN / プロキシ層の問題）
- Self-XSS のみで他ユーザーに影響しないもの
- 物理アクセスや SaaS プロバイダ（Supabase / GCS / Weaviate）自体の脆弱性
- 過去のフォーク元（pacexy/flow）の Sentry プロジェクトへの誤送信（既に修正済み）

## Security Architecture

詳細は [`apps/api/SECURITY.md`](./apps/api/SECURITY.md) を参照。

主要な防御層：

1. Supabase JWT 認証（HS256）+ 全ルーター強制
2. 認可 4 段階（Repository クエリ / UseCase 検証 / Domain `assert_owned_by` / Supabase RLS）
3. 入力検証（Pydantic `extra='forbid'` + 値オブジェクトサニタイズ + ファイルマジック検証）
4. レート制限（middleware default 120/min + 高コスト経路 20/min + ボディサイズ ASGI ハードキャップ）
5. SecurityHeaders（CSP / HSTS / X-Frame-Options / Permissions-Policy）
6. アウトバウンド制御（EPUB allow-list + プライベート IP 拒否 + Audio path allow-list）
7. 観測（gitleaks 週次フル + dependency audit + Sentry）

## Branch Protection（推奨設定）

`main` ブランチでは以下を有効化することを推奨します（GitHub: Settings → Branches → Branch protection rules）：

- **Require a pull request before merging**
  - **Require approvals**: 最低 1 人
  - **Require review from Code Owners**: 有効（`.github/CODEOWNERS` を参照）
  - **Dismiss stale pull request approvals when new commits are pushed**: 有効
- **Require status checks to pass before merging**: 以下を必須にする
  - `Backend CI` (`backend-ci.yml`)
  - `Frontend CI` (`frontend-ci.yml`)
  - `Secret scan / gitleaks` (`secret-scan.yml`)
  - `Dependency audit / pip-audit` (`dependency-audit.yml`)
  - `Dependency audit / pnpm audit`
- **Require branches to be up to date before merging**: 有効
- **Require signed commits**: 有効（GPG / Sigstore）
- **Require linear history**: 有効
- **Restrict who can push to matching branches**: 管理者のみ
- **Allow force pushes**: 無効
- **Allow deletions**: 無効

これらの保護に加え、CODEOWNERS が指定するファイル（auth / middleware / RLS / CI / Frontend 認証）への変更には Owner のレビューが自動で必須化されます。

## Recent Hardening

- 2026-05-09: 包括的なセキュリティレビュー対応 — 詳細は [`CHANGELOG.md`](./CHANGELOG.md) を参照
