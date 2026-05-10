from functools import cached_property, lru_cache
from typing import Self
from urllib.parse import urlparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

_ALLOWED_ENVIRONMENTS = {"development", "staging", "production"}
_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}


def _origin_is_loopback(origin: str) -> bool:
    """Origin (scheme://host[:port]) のホスト名が loopback / unspecified なら True."""
    try:
        host = urlparse(origin).hostname or ""
    except ValueError:
        return False
    return host.lower() in _LOOPBACK_HOSTS


# 互換性のため残置（テスト・seed のみ使用）。本番経路では認証から user_id を取得する。
TEST_USER_ID = "91527c9d-48aa-41d0-bb85-dc96f26556a0"


class AppConfig(BaseSettings):
    gcs_emulator_host: str | None = Field(default=None, description="Cloud Storage Emulator Host")
    database_url: str = Field(description="データベースURL")
    gcp_project_id: str = Field(default="bookwith", description="Google Cloud Project ID")
    gcs_bucket_name: str = Field(default="bookwith-bucket", description="GCS bucket name")
    gemini_api_key: str | None = Field(default=None, description="Gemini API Key")
    openai_api_key: str = Field(min_length=1, description="OpenAI API Key")

    # SQL echo は開発時のみ。デフォルトは無効（H-6）
    sql_echo: bool = Field(default=False, description="SQLAlchemy echo を有効にするか")

    # CORS 許可オリジン（CR-2）。カンマ区切り。本番では必ず明示する。
    cors_allow_origins: str = Field(
        default="http://localhost:7127,http://127.0.0.1:7127",
        description="CORS で許可するオリジン（カンマ区切り）",
    )

    # 認証（CR-1）。Supabase JWT を使う場合は SUPABASE_JWT_SECRET を設定。
    supabase_jwt_secret: str | None = Field(default=None, description="Supabase Auth の JWT 署名検証鍵")
    supabase_jwt_audience: str = Field(default="authenticated", description="Supabase JWT の audience")
    supabase_jwt_algorithms: str = Field(default="HS256", description="Supabase JWT の許可アルゴリズム（カンマ区切り）")
    # Issuer pinning: 設定されていれば `iss` クレームを厳密一致させ、別プロジェクトの JWT を弾く。
    # Supabase の典型値: `https://<project-ref>.supabase.co/auth/v1`
    supabase_jwt_issuer: str | None = Field(default=None, description="Supabase JWT の iss クレーム（設定時のみ検証）")
    # JWT クロックスキュー許容（秒）。負荷の高いインフラでは 5〜30 秒を推奨。
    supabase_jwt_leeway_seconds: int = Field(default=10, ge=0, le=300, description="JWT 検証のクロックスキュー（秒）")
    # 開発・テスト用の認証バイパス。本番では絶対 false。
    auth_dev_bypass: bool = Field(default=False, description="認証バイパス（開発・テスト用）")
    auth_dev_bypass_user_id: str = Field(default=TEST_USER_ID, description="バイパス時に使うユーザーID")

    # アップロード上限（H-1）
    max_upload_bytes: int = Field(default=25 * 1024 * 1024, description="EPUB ファイルアップロード上限（base64 デコード後の概算）")
    max_chapters: int = Field(default=15, description="ポッドキャスト生成で使う最大チャプター数（B-3）")

    # GCS 署名 URL の有効期限（M-7）
    gcs_signed_url_expires_seconds: int = Field(default=600, description="GCS 署名 URL 有効期限（秒）")

    # 環境名
    environment: str = Field(default="development", description="動作環境（development / staging / production）")

    # C-02: Weaviate の接続先と認証. 未設定なら local 接続（dev のみ）
    weaviate_url: str | None = Field(default=None, description="Weaviate Cloud / 本番ホストの URL（https）")
    weaviate_grpc_host: str | None = Field(default=None, description="Weaviate gRPC ホスト")
    weaviate_grpc_port: int = Field(default=50051, description="Weaviate gRPC ポート")
    weaviate_api_key: str | None = Field(default=None, description="Weaviate API キー（AuthApiKey）")
    weaviate_auto_tenant_creation: bool = Field(
        default=False,
        description="Weaviate のテナント自動作成を許可するか（C-04 対策で本番では False）",
    )

    # B-2 (アドエンダム): SSE ストリームの全体タイムアウト（秒）。LLM 応答が長時間ハングしてもサーバ側で打ち切る。
    sse_stream_timeout_seconds: float = Field(
        default=180.0,
        ge=10.0,
        le=600.0,
        description="SSE ストリーム生成全体に適用する asyncio.timeout（秒）",
    )

    # H-3: EPUB の外部 fetch を許可するホスト（カンマ区切り）。空なら外部 fetch を完全禁止。
    epub_fetch_allowed_hosts: str = Field(default="", description="EPUB fetch allow-list ホスト")
    # H-9: 音声ファイル用 BGM / 出力ディレクトリ allow-list（カンマ区切り）。
    audio_bgm_dirs: str = Field(default="", description="背景音楽として参照可能なディレクトリ")
    audio_output_dirs: str = Field(default="", description="音声ファイル書き込み許可ディレクトリ")
    # M-15: 開発時のみ create_all を呼ぶ。
    sqlalchemy_auto_create: bool = Field(default=True, description="開発時のみ create_all を呼ぶ")

    @staticmethod
    def _split_csv(raw: str) -> list[str]:
        return [item.strip() for item in raw.split(",") if item.strip()]

    # `get_config()` が lru_cache(maxsize=1) で同一インスタンスを返すため
    # cached_property で per-instance キャッシュ → 実質 module 定数として扱える。
    # 認証パスや SSE で毎リクエスト走るので split を毎回やらない。
    @cached_property
    def allowed_cors_origins(self) -> list[str]:
        return self._split_csv(self.cors_allow_origins)

    @cached_property
    def epub_fetch_allowed_hosts_list(self) -> list[str]:
        return self._split_csv(self.epub_fetch_allowed_hosts)

    @cached_property
    def audio_bgm_dirs_list(self) -> list[str]:
        return self._split_csv(self.audio_bgm_dirs)

    @cached_property
    def audio_output_dirs_list(self) -> list[str]:
        return self._split_csv(self.audio_output_dirs)

    @cached_property
    def jwt_algorithms_list(self) -> list[str]:
        return self._split_csv(self.supabase_jwt_algorithms)

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @field_validator("environment")
    @classmethod
    def _normalize_environment(cls, v: str) -> str:
        """ENVIRONMENT 値を strict にバリデートし、大文字混在やタイポを弾く."""
        normalized = (v or "").strip().lower()
        if normalized not in _ALLOWED_ENVIRONMENTS:
            raise ValueError(f"ENVIRONMENT must be one of {sorted(_ALLOWED_ENVIRONMENTS)} (got {v!r})")
        return normalized

    @classmethod
    @lru_cache(maxsize=1)
    def get_config(cls) -> Self:
        # `.env` の再読込が必要なテストでは `AppConfig.get_config.cache_clear()` を呼ぶこと。
        return cls()

    # MAX_UPLOAD_BYTES の本番ハードキャップ（メモリ枯渇 DoS 防止）。
    # 100 MiB を超える書籍は通常の運用では想定外。
    _MAX_UPLOAD_BYTES_HARD_CAP = 100 * 1024 * 1024

    def assert_production_ready(self) -> None:
        """本番環境で必須となる設定値を検証する.

        起動時に呼び、設定漏れがあれば RuntimeError を上げて fail-fast する。
        """
        if not self.is_production:
            return

        problems: list[str] = []

        if self.auth_dev_bypass:
            problems.append("AUTH_DEV_BYPASS must be false in production")
        if not self.supabase_jwt_secret:
            problems.append("SUPABASE_JWT_SECRET is required in production")
        if "*" in self.allowed_cors_origins or not self.allowed_cors_origins:
            problems.append("CORS_ALLOW_ORIGINS must be a non-wildcard explicit list")
        # localhost / 127.0.0.1 を本番 CORS allowlist に含めない (dev 設定の本番流入防止)。
        if any(_origin_is_loopback(origin) for origin in self.allowed_cors_origins):
            problems.append("CORS_ALLOW_ORIGINS must not contain localhost / 127.0.0.1 in production")
        if self.sql_echo:
            problems.append("SQL_ECHO must be false in production (PII / log cost)")
        if self.weaviate_auto_tenant_creation:
            problems.append("WEAVIATE_AUTO_TENANT_CREATION must be false in production")
        if not self.weaviate_url or not self.weaviate_api_key:
            problems.append("WEAVIATE_URL / WEAVIATE_API_KEY are required in production")
        if self.gcs_emulator_host:
            problems.append("GCS_EMULATOR_HOST must be unset in production")
        # メモリ枯渇 DoS 防止: 1 リクエストあたりの上限を運用 sane な値に拘束する。
        if self.max_upload_bytes > self._MAX_UPLOAD_BYTES_HARD_CAP:
            problems.append(
                f"MAX_UPLOAD_BYTES ({self.max_upload_bytes}) exceeds hard cap "
                f"({self._MAX_UPLOAD_BYTES_HARD_CAP}); reduce to prevent memory-exhaustion DoS"
            )

        if problems:
            joined = "; ".join(problems)
            raise RuntimeError(f"Invalid production configuration: {joined}")
