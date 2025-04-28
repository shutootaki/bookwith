import base64
import contextlib
import json
import logging
from abc import ABC, abstractmethod
from typing import Any

from src.domain.book.entities.book import Book
from src.domain.book.repositories.book_repository import BookRepository
from src.domain.book.value_objects.book_id import BookId
from src.domain.book.value_objects.book_title import BookTitle
from src.domain.book.value_objects.tennant_id import TenantId
from src.infrastructure.external.gcs import GCSClient


class CreateBookUseCase(ABC):
    @abstractmethod
    def execute(
        self,
        user_id: str,
        file_name: str,
        file_data: str,
        book_name: str | None = None,
        cover_image: str | None = None,
        book_metadata: str | None = None,
    ) -> Book:
        """新しいBookを作成して返す"""


class CreateBookUseCaseImpl(CreateBookUseCase):
    def __init__(self, book_repository: BookRepository) -> None:
        self.book_repository = book_repository
        self.gcs_client = GCSClient()
        self._logger = logging.getLogger(__name__)

    def execute(
        self,
        user_id: str,
        file_name: str,
        file_data: str,
        book_name: str | None = None,
        cover_image: str | None = None,
        book_metadata: str | None = None,
    ) -> Book:
        """新しいBookを作成して保存し、作成したBookエンティティを返す."""
        decoded_file_data = base64.b64decode(file_data)

        metadata: dict[str, Any] = {}
        if book_metadata:
            with contextlib.suppress(json.JSONDecodeError):
                metadata = json.loads(book_metadata)

        bucket = self.gcs_client.get_client().bucket(self.gcs_client.bucket_name)
        gcs_base_url = f"{self.gcs_client.get_gcs_url()}/{self.gcs_client.bucket_name}"

        book_id = BookId.generate()
        tenant_id = TenantId.generate(user_id, book_id.value)
        book_id_value = book_id.value
        book_base_path = f"books/{user_id}/{book_id_value}"

        uploaded_blobs = []

        try:
            epub_blob_name = f"{book_base_path}/book.epub"
            blob = bucket.blob(epub_blob_name)
            blob.upload_from_string(decoded_file_data, content_type="application/epub+zip")
            uploaded_blobs.append(blob)
            file_path = f"{gcs_base_url}/{epub_blob_name}"

            cover_path = None
            if cover_image and cover_image.startswith("data:image/"):
                try:
                    image_data = cover_image.split(",")[1]
                    image_binary = base64.b64decode(image_data)

                    cover_blob_name = f"{book_base_path}/cover.jpg"
                    cover_blob = bucket.blob(cover_blob_name)
                    cover_blob.upload_from_string(image_binary, content_type="image/jpeg")
                    uploaded_blobs.append(cover_blob)

                    cover_path = f"{gcs_base_url}/{cover_blob_name}"
                except Exception as e:
                    self._logger.error(f"カバー画像の保存中にエラーが発生しました: {str(e)}")

            book = Book.create(
                id=book_id,
                name=BookTitle(book_name if book_name else file_name),
                user_id=user_id,
                file_path=file_path,
                author=metadata.get("creator", None),
                size=len(decoded_file_data),
                book_metadata=metadata,
                tenant_id=tenant_id,
                cover_path=cover_path,
            )

            self.book_repository.save(book)

            return book

        except Exception as e:
            self._logger.error(f"Book作成中にエラーが発生しました: {str(e)}")
            self._rollback_storage(uploaded_blobs)
            raise

    def _rollback_storage(self, blobs: list[Any]) -> None:
        for blob in blobs:
            with contextlib.suppress(Exception):
                blob.delete()
