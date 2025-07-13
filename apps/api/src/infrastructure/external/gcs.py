from google.auth.credentials import AnonymousCredentials
from google.cloud import storage  # type: ignore[attr-defined]

from src.config.app_config import AppConfig

config = AppConfig.get_config()


class GCSBucketError(Exception):
    """Error related to GCS bucket operations."""


class GCSClient:
    def __init__(self, bucket_name: str = config.gcs_bucket_name) -> None:
        self.config = AppConfig.get_config()
        self.bucket_name = bucket_name
        self.use_emulator = self.config.gcs_emulator_host is not None

    def get_client(self) -> storage.Client:
        return storage.Client(
            project=self.config.gcp_project_id,
            client_options={"api_endpoint": self.config.gcs_emulator_host} if self.use_emulator else None,
            credentials=AnonymousCredentials() if self.use_emulator else None,
        )

    def get_gcs_url(self) -> str:
        emulator_host = self.config.gcs_emulator_host or "http://localhost:4443"
        return "https://storage.googleapis.com" if not self.use_emulator else emulator_host

    def upload_file(self, file_name: str, data: bytes, content_type: str) -> str:
        try:
            client = self.get_client()
            bucket = client.bucket(self.bucket_name)
            blob = bucket.blob(file_name)
            blob.upload_from_string(data, content_type=content_type)

            base_url = self.get_gcs_url()
            return f"{base_url}/{self.bucket_name}/{file_name}"
        except Exception as e:
            raise GCSBucketError(f"Failed to upload {file_name}: {str(e)}") from e

    def delete_object(self, file_name: str) -> None:
        try:
            client = self.get_client()
            bucket = client.bucket(self.bucket_name)
            blob = bucket.blob(file_name)
            blob.delete()
        except Exception as e:
            raise GCSBucketError(f"Failed to delete {file_name}: {str(e)}") from e
