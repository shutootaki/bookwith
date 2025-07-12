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

        metadata_dict: dict[str, Any] = {}
        if book_metadata:
            with contextlib.suppress(json.JSONDecodeError):
                metadata_dict = json.loads(book_metadata)

        book_id = BookId.generate()
        book_id_value = book_id.value
        book_base_path = f"books/{user_id}/{book_id_value}"

        uploaded_files: list[str] = []

        try:
            epub_blob_name = f"{book_base_path}/book.epub"
            file_path = self.gcs_client.upload_file(epub_blob_name, decoded_file_data, "application/epub+zip")
            uploaded_files.append(epub_blob_name)

            cover_path = None
            if cover_image and cover_image.startswith("data:image/"):
                try:
                    image_data = cover_image.split(",")[1]
                    image_binary = base64.b64decode(image_data)

                    cover_blob_name = f"{book_base_path}/cover.jpg"
                    cover_path = self.gcs_client.upload_file(cover_blob_name, image_binary, "image/jpeg")
                    uploaded_files.append(cover_blob_name)
                except Exception as e:
                    self._logger.error(f"カバー画像の保存中にエラーが発生しました: {str(e)}")

            book = Book.create(
                id=book_id,
                name=BookTitle(book_name if book_name else file_name),
                user_id=user_id,
                file_path=file_path,
                author=metadata_dict.get("creator") or None,
                size=len(decoded_file_data),
                cover_path=cover_path,
                metadata_title=metadata_dict.get("title"),
                metadata_creator=metadata_dict.get("creator"),
                metadata_description=metadata_dict.get("description"),
                metadata_pubdate=metadata_dict.get("pubdate"),
                metadata_publisher=metadata_dict.get("publisher"),
                metadata_identifier=metadata_dict.get("identifier"),
                metadata_language=metadata_dict.get("language"),
                metadata_rights=metadata_dict.get("rights"),
                metadata_modified_date=metadata_dict.get("modified_date"),
                metadata_layout=metadata_dict.get("layout"),
                metadata_orientation=metadata_dict.get("orientation"),
                metadata_flow=metadata_dict.get("flow"),
                metadata_viewport=metadata_dict.get("viewport"),
                metadata_spread=metadata_dict.get("spread"),
            )

            self.book_repository.save(book)

            return book

        except Exception as e:
            self._logger.error(f"Book作成中にエラーが発生しました: {str(e)}")
            self._rollback_storage(uploaded_files)
            raise

    def _rollback_storage(self, file_names: list[str]) -> None:
        for file_name in file_names:
            with contextlib.suppress(Exception):
                self.gcs_client.delete_object(file_name)
