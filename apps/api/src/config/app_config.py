from typing import Self

from pydantic import Field
from pydantic_settings import BaseSettings

TEST_USER_ID = "91527c9d-48aa-41d0-bb85-dc96f26556a0"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"


class AppConfig(BaseSettings):
    openai_api_key: str = Field(min_length=1, description="OpenAI API Key")
    database_url: str = Field(description="データベースURL")
    cloud_storage_emulator_host: str | None = Field(default=None, description="Cloud Storage Emulator Host")

    # 記憶管理関連の設定
    memory_buffer_size: int = Field(default=5, description="最新メッセージバッファのサイズ")
    memory_summarize_threshold: int = Field(default=20, description="要約を生成するメッセージ数の閾値")
    memory_chat_results: int = Field(default=3, description="チャットから取得する関連記憶の数")
    memory_profile_results: int = Field(default=2, description="ユーザープロファイルから取得する関連記憶の数")
    memory_profile_keywords: list[str] = Field(
        default=["好き", "趣味は", "住んで", "名前は", "職業は", "興味", "関心", "専門"],
        description="ユーザープロファイルとして抽出するためのキーワード",
    )
    max_prompt_tokens: int = Field(default=8192, description="プロンプトの最大トークン数")

    @classmethod
    def get_config(cls) -> Self:
        return cls()
