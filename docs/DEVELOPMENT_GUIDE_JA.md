# BookWith 開発環境構築ガイド

このガイドでは、BookWith プロジェクトのコントリビューター・開発者向けに、開発環境の構築手順を詳しく説明します。

## 📚 目次

- [プロジェクト概要](#プロジェクト概要)
- [前提条件](#前提条件)
- [クイックスタート](#クイックスタート)
- [詳細な環境構築手順](#詳細な環境構築手順)
- [開発フロー](#開発フロー)
- [トラブルシューティング](#トラブルシューティング)
- [ディレクトリ構成](#ディレクトリ構成)
- [貢献ガイドライン](#貢献ガイドライン)

## 🎯 プロジェクト概要

BookWith は、AI 駆動の次世代ブラウザベース ePub リーダーです。書籍内容を理解した AI アシスタントとの対話を通じて、より深い読書体験を提供します。

### アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────┐
│  フロントエンド (Next.js + TypeScript)                    │
│  ・Pages Router                                         │
│  ・ePub.js によるレンダリング                              │
│  ・リアルタイムAI対話                                      │
└─────────────────────────────────────────────────────────┘
                           ↓ API通信
┌─────────────────────────────────────────────────────────┐
│  バックエンド (FastAPI + Python)                          │
│  ・DDD レイヤードアーキテクチャ                             │
│  ・LangChain による AI 統合                               │
│  ・記憶管理システム                                        │
└─────────────────────────────────────────────────────────┘
                           ↓ データ永続化
┌─────────────────────────────────────────────────────────┐
│  データストア                                             │
│  ・Supabase (メインDB)                                 │
│  ・Weaviate (ベクトルDB)                                  │
│  ・GCS エミュレータ (開発用ストレージ)                       │
└─────────────────────────────────────────────────────────┘
```

## 🛠 前提条件

### 必須ツール

| ツール         | バージョン  | 確認方法                 |
| -------------- | ----------- | ------------------------ |
| Node.js        | 18.0.0 以上 | `node -v`                |
| pnpm           | 9.15.4      | `pnpm -v`                |
| Python         | 3.13 以上   | `python --version`       |
| Poetry         | 最新版      | `poetry --version`       |
| Docker         | 最新版      | `docker --version`       |
| Docker Compose | v2 以上     | `docker compose version` |

### インストール方法

#### pnpm のインストール

```bash
# Node.js がインストール済みの場合
npm install -g pnpm@9.15.4

# または Homebrew (macOS)
brew install pnpm
```

#### Poetry のインストール

```bash
# 公式インストーラー
curl -sSL https://install.python-poetry.org | python3 -

# または Homebrew (macOS)
brew install poetry
```

## 🚀 クイックスタート

以下のコマンドで開発環境を素早く立ち上げることができます：

```bash
# 1. リポジトリのクローン
git clone https://github.com/your-org/bookwith.git
cd bookwith

# 2. 依存関係のインストール
pnpm i

# 3. 環境変数の設定
cd apps/api
cp src/config/.env.example src/config/.env
# .envファイルを編集してAPIキーを設定

# 4. Supabase の起動（別途インストールが必要）
supabase start

# 5. Docker サービスの起動
cd apps/api
make docker.up

# 6. 開発サーバーの起動（ルートディレクトリに戻って）
cd ../..
pnpm dev
```

これで以下の URL でアクセスできます：

- フロントエンド: http://localhost:7127
- バックエンド API: http://localhost:8000
- API ドキュメント: http://localhost:8000/docs

## 📋 詳細な環境構築手順

### 1. リポジトリのクローンとセットアップ

```bash
# GitHubからクローン
git clone https://github.com/your-org/bookwith.git
cd bookwith

# 依存関係のインストール（モノリポ全体）
pnpm i
```

### 2. 環境変数の設定

#### バックエンド（API）の環境変数

```bash
cd apps/api
cp src/config/.env.example src/config/.env
```

`.env` ファイルを編集して以下の設定を行います：

```env
# 基本設定
PORT=8000

# 必須: OpenAI API キー
OPENAI_API_KEY=sk-...  # OpenAIのダッシュボードから取得

# オプション: LangSmith（トレーシング用）
LANGCHAIN_API_KEY=ls__...  # LangSmithから取得
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=bookwith

# データベース
# Supabaseローカル環境のデフォルトポート（54322）を使用
# 注意: 通常のPostgreSQLのポート（5432）ではありません
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres

# ストレージ（Docker Compose使用時はデフォルトのまま）
GCS_EMULATOR_HOST=http://127.0.0.1:4443

# Memory設定（デフォルト値で開始可能）
MEMORY_BUFFER_SIZE=10
MEMORY_SUMMARIZE_THRESHOLD=50
MEMORY_CHAT_RESULTS=3
MAX_PROMPT_TOKENS=8192
```

#### フロントエンドの環境変数（必要に応じて）

```bash
cd apps/reader
cp .env.example .env
```

### 3. Docker 環境の起動

#### PostgreSQL データベース（Supabase）の起動

このプロジェクトでは PostgreSQL データベースとして Supabase を使用しています。別途 Supabase をローカルで起動する必要があります：

```bash
# Supabaseの起動（別のプロジェクトまたはグローバルにインストール済みの場合）
# npx supabase start
# または
# supabase start

# Supabaseのステータス確認
# supabase status
```

**注意**: `apps/api/docker-compose.yml`には PostgreSQL は含まれていません。Supabase を別途起動してください。

#### その他の Docker サービスの起動

```bash
cd apps/api
make docker.up
```

これにより以下のサービスが起動します：

- **Weaviate** (ベクトル DB): http://localhost:8080
- **GCS エミュレータ**: http://localhost:4443

### 4. データベースの初期化

初回起動時またはデータベーススキーマに変更があった場合：

```bash
cd apps/api

# Pythonインタープリタで実行
poetry run python
>>> from src.config.db import init_db
>>> init_db()
>>> exit()
```

これにより、SQLAlchemy のモデル定義に基づいて必要なテーブルが自動的に作成されます。

### 5. バックエンド（API）の起動

```bash
cd apps/api

# 初回のみ: Poetry 依存関係のインストール
make configure

# 開発サーバーの起動
make run
```

API ドキュメントの確認：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 6. フロントエンドの起動

新しいターミナルを開いて：

```bash
cd apps/reader

# OpenAPI スキーマから型定義を生成（初回または API 変更時）
pnpm openapi:ts

# 開発サーバーの起動
pnpm dev
```

フロントエンド: http://localhost:7127

### 7. 動作確認

1. ブラウザで http://localhost:7127 にアクセス
2. ePub ファイルをドラッグ&ドロップまたは選択してインポート
3. 書籍が表示されたら、右側のチャットパネルで AI と対話

## 💻 開発フロー

### コード変更時の流れ

#### バックエンド開発

1. **コード変更**

   ```bash
   # DDD レイヤーを意識して適切な場所に実装
   # src/domain/    - エンティティ、値オブジェクト
   # src/usecase/   - ビジネスロジック
   # src/infrastructure/ - 外部連携
   # src/presentation/  - API エンドポイント
   ```

2. **型チェックとリント**

   ```bash
   cd apps/api
   make lint  # MyPy + pre-commit
   ```

3. **API の再起動**
   - FastAPI は自動リロードに対応しているため、通常は自動的に反映されます

#### フロントエンド開発

1. **コード変更**

   ```bash
   # 主要なディレクトリ
   # src/components/  - Reactコンポーネント
   # src/hooks/      - カスタムフック
   # src/pages/      - ページコンポーネント
   # src/lib/        - ユーティリティ
   ```

2. **型チェック**

   ```bash
   cd apps/reader
   pnpm ts:check
   ```

3. **ホットリロード**
   - Next.js は変更を自動検出して再読み込みします

### ビルドとテスト

#### 全体のビルド

```bash
# ルートディレクトリで
pnpm build
```

#### リントの実行

```bash
# 全体
pnpm lint

# API のみ
cd apps/api && make lint

# フロントエンドのみ
cd apps/reader && pnpm lint
```

### OpenAPI スキーマの更新

API の型定義を変更した場合：

```bash
# APIサーバーが起動している状態で
cd apps/reader
pnpm openapi:ts
```

## 🔧 トラブルシューティング

### よくある問題と解決方法

#### 1. pnpm install でエラーが発生する

```bash
# キャッシュのクリア
pnpm store prune

# node_modules の削除と再インストール
rm -rf node_modules pnpm-lock.yaml
pnpm i
```

#### 2. Docker サービスが起動しない

```bash
# 既存のコンテナを停止・削除
cd apps/api
docker compose down -v

# ポートの確認
lsof -i :8080  # Weaviate
lsof -i :4443  # GCS エミュレータ

# 再起動
make docker.up
```

#### 3. API が起動しない

```bash
# Poetry の環境を再構築
cd apps/api
poetry env remove python
poetry install --no-root

# 環境変数の確認
cat src/config/.env  # APIキーが設定されているか確認
```

#### 4. フロントエンドで API との通信エラー

```bash
# APIが起動しているか確認
curl http://localhost:8000/health

# CORSエラーの場合は、APIのCORS設定を確認
```

#### 5. Weaviate 接続エラー

```bash
# Weaviate が起動しているか確認
curl http://localhost:8080/v1/.well-known/ready

# ログの確認
cd apps/api
docker compose logs weaviate
```

#### 6. PostgreSQL/Supabase 接続エラー

```bash
# Supabase が起動しているか確認
supabase status

# ポート 54322 が使用されているか確認
lsof -i :54322

# 接続テスト
psql postgresql://postgres:postgres@127.0.0.1:54322/postgres -c "SELECT 1"

# Supabase が起動していない場合
supabase start
```

#### 7. データベーステーブルが存在しないエラー

```bash
# データベースの初期化を実行
cd apps/api
poetry run python
>>> from src.config.db import init_db
>>> init_db()
>>> exit()
```

### デバッグのヒント

1. **API ログの確認**

   ```bash
   # FastAPI のログはターミナルに表示されます
   # LangSmith を有効にしている場合は、トレース情報も確認可能
   ```

2. **ブラウザの開発者ツール**

   - Network タブで API リクエストを確認
   - Console でエラーメッセージを確認

3. **Docker ログ**
   ```bash
   cd apps/api
   docker compose logs -f  # 全サービスのログ
   docker compose logs -f weaviate  # Weaviate のみ
   ```

## 📁 ディレクトリ構成

### プロジェクト全体構造

```
bookwith/
├── apps/
│   ├── api/          # FastAPI バックエンド
│   │   ├── src/
│   │   │   ├── domain/          # ドメイン層（DDD）
│   │   │   ├── usecase/         # ユースケース層
│   │   │   ├── infrastructure/  # インフラ層
│   │   │   ├── presentation/    # プレゼンテーション層
│   │   │   └── config/          # 設定ファイル
│   │   ├── Makefile            # 便利コマンド
│   │   └── docker-compose.yml  # Docker設定
│   │
│   └── reader/       # Next.js フロントエンド
│       ├── src/
│       │   ├── components/      # UIコンポーネント
│       │   ├── hooks/          # カスタムフック
│       │   ├── pages/          # ページコンポーネント
│       │   └── lib/            # ユーティリティ
│       └── package.json
│
├── packages/         # 共有パッケージ（将来拡張予定）
├── docs/            # ドキュメント
├── package.json     # モノリポ設定
├── pnpm-workspace.yaml
└── turbo.json       # Turbo設定
```

### バックエンドの主要ファイル

- `apps/api/src/domain/` - エンティティ、値オブジェクト、リポジトリインターフェース
- `apps/api/src/usecase/` - ビジネスロジック実装
- `apps/api/src/infrastructure/memory/` - AI 記憶管理機能
- `apps/api/src/presentation/api/` - API エンドポイント定義

### フロントエンドの主要ファイル

- `apps/reader/src/components/viewlets/chat/` - AI 対話機能
- `apps/reader/src/components/Reader.tsx` - ePub リーダーコア
- `apps/reader/src/lib/apiHandler/` - API 通信処理
- `apps/reader/src/models/reader.ts` - 状態管理（Valtio）

## 🤝 貢献ガイドライン

### コード規約

#### Python（バックエンド）

1. **フォーマッター**: Black を使用
2. **型チェック**: MyPy でエラーがないこと
3. **命名規則**:
   - クラス名: PascalCase
   - 関数・変数: snake_case
   - 定数: UPPER_SNAKE_CASE

```python
# 良い例
class BookRepository(ABC):
    def find_by_id(self, book_id: BookId) -> Optional[Book]:
        pass

# 悪い例
class bookRepository:
    def findById(self, bookId):  # 型ヒントがない
        pass
```

#### TypeScript（フロントエンド）

1. **フォーマッター**: Prettier を使用
2. **リンター**: ESLint の設定に従う
3. **型定義**: 厳密モード（strict: true）

```typescript
// 良い例
interface BookProps {
  id: string
  title: string
  onSelect?: (id: string) => void
}

// 悪い例
interface BookProps {
  id: any // any 型は避ける
  title: string
}
```

### コミット規約

Conventional Commits を推奨：

```bash
# 形式
<type>(<scope>): <subject>

# 例
feat(reader): AI対話機能のストリーミング対応を追加
fix(api): メモリリークを修正
docs: 環境構築ガイドを追加
refactor(domain): Book エンティティのバリデーションを改善
test(usecase): CreateBookUseCase のユニットテストを追加
```

#### Type 一覧

- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメントのみの変更
- `style`: コードの意味に影響を与えない変更
- `refactor`: バグ修正や機能追加を含まないコード変更
- `test`: テストの追加・修正
- `chore`: ビルドプロセスやツールの変更

### プルリクエスト

1. **ブランチ命名**: `feature/xxx`, `fix/xxx`, `docs/xxx`
2. **PR テンプレート**: 以下を含める
   - 変更内容の概要
   - 関連する Issue 番号
   - テスト方法
   - スクリーンショット（UI 変更の場合）

### レビューのポイント

- [ ] 型安全性が保たれているか
- [ ] DDD の原則に従っているか（バックエンド）
- [ ] エラーハンドリングが適切か
- [ ] パフォーマンスへの影響はないか
- [ ] テストは追加されているか

## 📚 参考リソース

### 公式ドキュメント

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Weaviate Documentation](https://weaviate.io/developers/weaviate)
- [LangChain Documentation](https://python.langchain.com/)

### プロジェクト固有のドキュメント

- [CLAUDE.md](../CLAUDE.md) - AI アシスタント向けガイド
- [backend-architecture.md](./backend-architecture.md) - バックエンドアーキテクチャ詳細
- [frontend-directory-structure.md](./frontend-directory-structure.md) - フロントエンド構成詳細

### 開発に役立つツール

- [Swagger Editor](https://editor.swagger.io/) - OpenAPI スキーマの編集
- [Weaviate Console](http://localhost:8080/v1/console) - ベクトル DB の管理
- [React Developer Tools](https://react.dev/learn/react-developer-tools) - React デバッグ

## 🆘 サポート

問題が解決しない場合は：

1. [GitHub Issues](https://github.com/your-org/bookwith/issues) で既存の問題を検索
2. 新しい Issue を作成（再現手順を含めてください）
3. [Discussions](https://github.com/your-org/bookwith/discussions) で質問

---

Happy Coding! 🚀
