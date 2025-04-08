from typing import Self

from pydantic import Field
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    openai_api_key: str = Field(min_length=1, description="OpenAI API Key")
    dropbox_client_id: str = Field(min_length=1, description="Dropbox Client ID")
    dropbox_client_secret: str = Field(
        min_length=1, description="Dropbox Client Secret"
    )
    database_url: str = Field(description="データベースURL")

    @classmethod
    def get_config(cls) -> Self:
        """get_config."""
        return cls()
