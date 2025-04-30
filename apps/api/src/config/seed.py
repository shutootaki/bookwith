from src.config.app_config import TEST_USER_ID
from src.config.db import SessionLocal
from src.infrastructure.postgres.user.user_dto import UserDTO

# ※ 初回のみ、テーブル作成を実行（すでにテーブルが存在する場合は不要）
# Base.metadata.create_all(bind=engine)


def seed_data():
    session = SessionLocal()
    try:
        # シードデータの作成例
        seed_items = [UserDTO(id=TEST_USER_ID, username="testuser", email="example@example.com")]

        # 複数のシードデータを一括で追加
        session.add_all(seed_items)
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    seed_data()
