from google.cloud import storage
from src.config.app_config import AppConfig

BUCKET_NAME = "bookwith-storage"


class GCSClient:
    def __init__(self):
        self.config = AppConfig().get_config()

    def get_client(self):
        return storage.Client(
            project="bookwith-storage",
            client_options={"api_endpoint": self.config.cloud_storage_emulator_host}
            if self.config.cloud_storage_emulator_host
            else None,
        )
