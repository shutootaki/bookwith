from google.auth.credentials import AnonymousCredentials
from google.cloud import storage  # type: ignore[attr-defined]

from src.config.app_config import AppConfig

# Google ホストでの HTML 配信を避けるため、text/html や image/svg+xml は許可しない。
ALLOWED_UPLOAD_CONTENT_TYPES: frozenset[str] = frozenset(
    {
        "application/epub+zip",
        "application/octet-stream",
        "image/jpeg",
        "image/png",
        "image/webp",
        "audio/mpeg",
        "audio/mp4",
        "audio/wav",
    }
)


class GCSBucketError(Exception):
    """Error related to GCS bucket operations."""


class GCSContentTypeNotAllowedError(GCSBucketError):
    """許可されていない content_type を upload しようとした場合."""


class GCSClient:
    def __init__(self, bucket_name: str | None = None) -> None:
        self.config = AppConfig.get_config()
        self.bucket_name = bucket_name or self.config.gcs_bucket_name
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

    def strip_public_url_prefix(self, public_url: str) -> str:
        """`get_gcs_url()/bucket/...` で始まる public URL からバケット相対パスを取り出す."""
        prefix = f"{self.get_gcs_url()}/{self.bucket_name}/"
        return public_url[len(prefix) :] if public_url.startswith(prefix) else public_url

    def generate_signed_get_url(self, blob_path: str) -> str:
        """v4 GET 用の署名付き URL を生成する (有効期限は AppConfig で制御)."""
        bucket = self.get_client().bucket(self.bucket_name)
        blob = bucket.blob(blob_path)
        return blob.generate_signed_url(
            version="v4",
            expiration=self.config.gcs_signed_url_expires_seconds,
            method="GET",
        )

    def upload_file(self, file_name: str, data: bytes, content_type: str) -> str:
        if content_type not in ALLOWED_UPLOAD_CONTENT_TYPES:
            raise GCSContentTypeNotAllowedError(f"Content type not allowed: {content_type}")
        try:
            client = self.get_client()
            bucket = client.bucket(self.bucket_name)
            blob = bucket.blob(file_name)
            # cache_control を no-store にして、HTML 等が誤って入っても long-cache されないようにする。
            blob.cache_control = "private, max-age=0, no-store"
            blob.upload_from_string(data, content_type=content_type)

            base_url = self.get_gcs_url()
            return f"{base_url}/{self.bucket_name}/{file_name}"
        except GCSContentTypeNotAllowedError:
            raise
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
