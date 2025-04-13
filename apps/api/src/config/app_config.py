from typing import Self

from pydantic import Field
from pydantic_settings import BaseSettings

TEST_USER_ID = "91527c9d-48aa-41d0-bb85-dc96f26556a0"


class AppConfig(BaseSettings):
    openai_api_key: str = Field(min_length=1, description="OpenAI API Key")
    dropbox_client_id: str = Field(min_length=1, description="Dropbox Client ID")
    dropbox_client_secret: str = Field(min_length=1, description="Dropbox Client Secret")
    database_url: str = Field(description="データベースURL")
    cloud_storage_emulator_host: str | None = Field(default=None, description="Cloud Storage Emulator Host")

    @classmethod
    def get_config(cls) -> Self:
        """get_config."""
        return cls()
