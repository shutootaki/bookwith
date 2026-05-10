# Alembic Migrations

M-15 対応として導入された Alembic マイグレーション領域。

## 使い方

```bash
# 1) 開発用 DATABASE_URL を export しておく
export DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres

# 2) 現在のスキーマと差分から migration を自動生成
uv run alembic revision --autogenerate -m "describe change"

# 3) 適用
uv run alembic upgrade head

# 4) ロールバック
uv run alembic downgrade -1
```

## 注意点

- `apps/api/src/config/db.py` の `init_db()` は本番では `Base.metadata.create_all` を
  呼ばない（M-15）。本番ではこの Alembic マイグレーションをデプロイ前に必ず適用する。
- Supabase Auth 経由でアクセスされる場合、`supabase/migrations/20260505000000_enable_rls_policies.sql`
  との整合を維持すること（テーブルが新規追加された時は、対応する RLS ポリシーも作る）。
