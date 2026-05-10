"""SECURITY.md とコード実装の整合性テスト.

`apps/api/SECURITY.md` の環境変数表に、本番運用上必須/推奨のセキュリティ関連環境変数が
すべて列挙されていることを検証する。

このテストは「実装に新しいセキュリティ環境変数を追加したのに SECURITY.md を更新し忘れる」
という、運用ミスの源泉になりやすい documentation drift を CI で検出するための装置。
"""

from __future__ import annotations

import os
from pathlib import Path

# Repository ルート → apps/api/SECURITY.md
_API_DIR = Path(__file__).resolve().parents[1]
_SECURITY_MD = _API_DIR / "SECURITY.md"


# 本番運用で必ずドキュメントに載っているべき環境変数（セキュリティ・運用観点）
_REQUIRED_DOCUMENTED_ENV_VARS: tuple[str, ...] = (
    "ENVIRONMENT",
    "AUTH_DEV_BYPASS",
    "SUPABASE_JWT_SECRET",
    "SUPABASE_JWT_AUDIENCE",
    "SUPABASE_JWT_ALGORITHMS",
    "SUPABASE_JWT_ISSUER",
    "SUPABASE_JWT_LEEWAY_SECONDS",
    "CORS_ALLOW_ORIGINS",
    "SQL_ECHO",
    "WEAVIATE_URL",
    "WEAVIATE_API_KEY",
    "WEAVIATE_AUTO_TENANT_CREATION",
    "EPUB_FETCH_ALLOWED_HOSTS",
    "AUDIO_BGM_DIRS",
    "AUDIO_OUTPUT_DIRS",
    "MAX_UPLOAD_BYTES",
    "MAX_CHAPTERS",
    "GCS_SIGNED_URL_EXPIRES_SECONDS",
    "SSE_STREAM_TIMEOUT_SECONDS",
)


def test_security_md_exists() -> None:
    assert _SECURITY_MD.is_file(), f"{_SECURITY_MD} not found"


def test_security_md_lists_all_required_env_vars() -> None:
    """SECURITY.md にすべての本番関連 env var が列挙されている."""
    text = _SECURITY_MD.read_text(encoding="utf-8")

    missing: list[str] = [name for name in _REQUIRED_DOCUMENTED_ENV_VARS if name not in text]

    assert not missing, f"SECURITY.md is missing documentation for: {missing}. Add them to the env-vars table in apps/api/SECURITY.md."


def test_app_config_fields_match_documented_env_vars() -> None:
    """AppConfig の Field 名（=env var 名）が _REQUIRED_DOCUMENTED_ENV_VARS と整合している.

    実装側で新規 Field を追加した場合は `_REQUIRED_DOCUMENTED_ENV_VARS` または
    意図的な除外リストに登録するよう促す。
    """
    os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
    os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")

    from src.config.app_config import AppConfig

    # AppConfig のフィールド名（env var 化される）
    field_names_lower = set(AppConfig.model_fields.keys())

    # ドキュメント済みの env var 名を lower 形式に揃えて突合
    documented_lower = {name.lower() for name in _REQUIRED_DOCUMENTED_ENV_VARS}

    # 公開不要・運用上ドキュメントしなくてよい内部フィールド
    intentionally_undocumented_lower = {
        "database_url",  # 別管理（Secret Manager）
        "openai_api_key",  # 別管理
        "gemini_api_key",  # 別管理
        "gcs_emulator_host",  # ローカル専用
        "gcp_project_id",  # 別管理
        "gcs_bucket_name",  # 別管理
        "auth_dev_bypass_user_id",  # AUTH_DEV_BYPASS とセット
        "weaviate_grpc_host",  # 別管理
        "weaviate_grpc_port",  # デフォルトで充分
        "sqlalchemy_auto_create",  # 開発フラグ
    }

    untracked = field_names_lower - documented_lower - intentionally_undocumented_lower
    assert not untracked, (
        f"New AppConfig fields {untracked} are neither documented in SECURITY.md "
        f"nor in the intentionally-undocumented allow-list of this test. "
        f"Either add them to SECURITY.md and update _REQUIRED_DOCUMENTED_ENV_VARS, "
        f"or add them to intentionally_undocumented_lower above with a comment."
    )
