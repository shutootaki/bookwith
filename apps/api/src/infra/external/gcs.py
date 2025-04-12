from google.auth.credentials import AnonymousCredentials
from google.cloud import storage
from src.config.app_config import AppConfig


class GCSClient:
    def __init__(self, bucket_name: str = "bookwith-storage"):
        self.config = AppConfig().get_config()
        self.bucket_name = bucket_name
        self.use_emulator = self.config.cloud_storage_emulator_host is not None

    def get_client(self):
        return storage.Client(
            project="bookwith-storage",
            client_options={"api_endpoint": self.config.cloud_storage_emulator_host}
            if self.use_emulator
            else None,
            credentials=AnonymousCredentials() if self.use_emulator else None,
        )

    def get_gcs_url(self) -> str:
        return (
            "https://storage.googleapis.com"
            if not self.use_emulator
            else self.config.cloud_storage_emulator_host
        )
