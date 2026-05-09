# BookWith Reader (Frontend)

Next.js 15 + TypeScript + Valtio。AI 対話付きの ePub リーダー。

## クイックスタート

```bash
# 依存インストール（リポジトリルートで）
pnpm install

# 環境変数の用意（.env.local など）
# - NEXT_PUBLIC_API_BASE_URL: バックエンド API（例: http://localhost:8000）
# - NEXT_PUBLIC_SUPABASE_URL: Supabase プロジェクト URL
# - NEXT_PUBLIC_SUPABASE_ANON_KEY: anon キー
# - NEXT_PUBLIC_GTM_ID（任意）: GTM-XXXXX 形式のみ受け付ける

# 開発サーバー
pnpm dev

# 型チェック
pnpm -F @flow/reader run ts:check

# Lint
pnpm -F @flow/reader run lint:eslint
pnpm -F @flow/reader run lint:prettier
```

## 認証 (CR-1) との連携

`src/lib/auth/token.ts` が `apiClient` / `fetcher` から共有されるトークンストアを提供する。
Supabase Auth クライアント本体を組み込む際は、`pages/_app.tsx` で以下を行う：

```ts
import { createClient } from '@supabase/supabase-js'
import { persistAuthSession, clearAuthTokens } from '../lib/auth/token'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
)

// MyApp 内
useEffect(() => {
  // 起動時に既存セッションを apiClient に伝える
  supabase.auth
    .getSession()
    .then(({ data }) => persistAuthSession(data.session))

  // 状態変化（ログイン / ログアウト / refresh）を購読
  const { data: sub } = supabase.auth.onAuthStateChange((event, session) => {
    if (event === 'SIGNED_OUT') clearAuthTokens()
    else persistAuthSession(session)
  })
  return () => sub.subscription.unsubscribe()
}, [])
```

これだけで、`apiClient` / `fetcher` / 直接 fetch してる経路（`reader.ts` 等）に
Bearer Token が伝播する。

## セキュリティに関する補足

- **EPUB iframe sandbox**: `allowScriptedContent: false`（CR-5）で同一オリジン下のスクリプト実行を禁止。
- **?src= リモートインポート**: `isAllowedRemoteImportUrl` の allow-list で確認 + サイズ / Content-Type 検証（CR-7）。
- **Sentry DSN**: `SENTRY_DSN` / `NEXT_PUBLIC_SENTRY_DSN` 未設定の場合は `Sentry.init` をスキップ（H-19）。
- **CSP/HSTS/X-Frame-Options 等**: `next.config.js` の `headers()` で全ページに付与（H-20）。

詳細は [`apps/api/SECURITY.md`](../api/SECURITY.md) を参照。

## テスト基盤（未導入）

フロントには現状自動テストフレームワークが入っていない。CR-7 / CR-1 周りの
ロジック（`isAllowedRemoteImportUrl` / `lib/auth/token.ts`）を回帰検出するため、
**vitest** の導入を推奨：

```bash
pnpm -F @flow/reader add -D vitest @vitest/ui jsdom @testing-library/react
```

`apps/reader/vitest.config.ts`:

```ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
  },
})
```

`package.json` に追加:

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest"
  }
}
```

優先度の高いテスト候補:

- `src/lib/apiHandler/importHandlers.test.ts` — `isAllowedRemoteImportUrl` の allow-list / 各種スキーム拒否
- `src/lib/auth/token.test.ts` — `persistAuthSession` の挙動 / `clearAuthTokens`
- `src/lib/apiHandler/apiClient.test.ts` — Bearer 付与 / 401 自動 logout

導入後は `frontend-ci.yml` に `pnpm -F @flow/reader run test` ステップを追加して必須化する。

## OpenAPI 型再生成の運用

本番環境では `/openapi.json` を 404 にしているため、フロントの `pnpm openapi:ts`
は **本番 URL を叩いてはいけない**。以下のいずれかで運用する：

1. **ローカル開発**（推奨）
   ```bash
   # 別ターミナルで API を起動
   cd apps/api && make run
   # フロント側で型生成（http://localhost:8000/openapi.json を読む）
   pnpm -F @flow/reader run openapi:ts
   ```
2. **CI / staging**: `ENVIRONMENT=staging` でデプロイされたインスタンスから取得
3. **静的エクスポート**（将来）: `apps/api/src/main.py` の `app.openapi()` を CLI で
   実行して JSON を出力するスクリプトを追加

`apps/reader/src/lib/openapi-schema/schema.ts` は生成成果物。手動編集しない。

## ディレクトリ構造

```
src/
├── components/             # UI コンポーネント
├── hooks/                  # SWR / podcast / theme 等のフック
├── lib/
│   ├── apiHandler/         # apiClient / fetch ラッパー
│   ├── auth/               # CR-1 トークン管理ヘルパー
│   └── openapi-schema/     # 自動生成された API 型
├── models/                 # Reader / ePub の domain 状態
├── pages/                  # Next.js ページ
└── workers/                # Web Worker
```

## ビルド

```bash
pnpm build              # 全ワークスペース
pnpm -F @flow/reader run build  # Reader のみ
```

Docker:

```bash
docker build -f apps/reader/Dockerfile -t bookwith-reader .
```
