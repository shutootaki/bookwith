from typing import Self

from pydantic import Field
from pydantic_settings import BaseSettings

TEST_USER_ID = "91527c9d-48aa-41d0-bb85-dc96f26556a0"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"


class AppConfig(BaseSettings):
    gcs_emulator_host: str | None = Field(default=None, description="Cloud Storage Emulator Host")
    database_url: str = Field(description="データベースURL")
    gcp_project_id: str = Field(default="bookwith", description="Google Cloud Project ID")
    gcs_bucket_name: str = Field(default="bookwith-bucket", description="GCS bucket name")
    gemini_api_key: str | None = Field(default=None, description="Gemini API Key")
    openai_api_key: str = Field(min_length=1, description="OpenAI API Key")

    @classmethod
    def get_config(cls) -> Self:
        return cls()
