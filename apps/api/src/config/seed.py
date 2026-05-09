"""開発・テスト用 seed スクリプト.

I-01 / 運用上の注意:
- 本ファイルは **開発環境専用**。固定 UUID のテストユーザーを Postgres に挿入する。
- 本番ビルド・本番起動からは **絶対に呼び出されない** ことを保証する。
- 直接 `python seed.py` で実行された場合のみ動作し、`ENVIRONMENT=production` の場合は中断する。
"""

from src.config.app_config import TEST_USER_ID, AppConfig
from src.config.db import SessionLocal
from src.infrastructure.postgres.user.user_dto import UserDTO


def seed_data() -> None:
    config = AppConfig.get_config()
    if config.is_production:
        # I-01: 本番では絶対に走らない。誤実行で TEST_USER_ID が混入するのを防ぐ。
        raise RuntimeError("seed_data() must not be executed in production")

    session = SessionLocal()
    try:
        seed_items = [UserDTO(id=TEST_USER_ID, username="testuser", email="example@example.com")]

        session.add_all(seed_items)
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    seed_data()
