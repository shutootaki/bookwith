import base64
import contextlib
import json
import logging
from abc import ABC, abstractmethod
from typing import Any

from src.config.app_config import AppConfig
from src.domain.book.entities.book import Book
from src.domain.book.repositories.book_repository import BookRepository
from src.domain.book.value_objects.book_id import BookId
from src.domain.book.value_objects.book_title import BookTitle
from src.domain.shared.identifiers import is_strict_uuid
from src.infrastructure.external.gcs import GCSClient


def _looks_like_image(data: bytes) -> bool:
    """M-01: バイト先頭のマジックナンバーで JPEG/PNG/WebP を識別する."""
    if len(data) < 12:
        return False
    # JPEG: FF D8 FF
    if data[:3] == b"\xff\xd8\xff":
        return True
    # PNG: 89 50 4E 47 0D 0A 1A 0A
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return True
    # WebP: "RIFF....WEBP"
    return bool(data[:4] == b"RIFF" and data[8:12] == b"WEBP")


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
        # H-4: GCS prefix 注入を防ぐため UUID 検証。
        if not is_strict_uuid(user_id):
            raise ValueError("user_id must be a valid UUID")

        config = AppConfig.get_config()

        try:
            decoded_file_data = base64.b64decode(file_data, validate=True)
        except Exception as e:
            raise ValueError("file_data must be valid base64") from e

        # H-1 / M-3: ファイルサイズ上限。
        if len(decoded_file_data) > config.max_upload_bytes:
            raise ValueError("Uploaded file is too large")

        # H-2: EPUB は ZIP コンテナ。先頭 4 バイトの "PK\x03\x04" を最低限確認する。
        if not decoded_file_data.startswith(b"PK\x03\x04"):
            raise ValueError("Uploaded file is not a ZIP-based EPUB")

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
                    # M-01: SVG / HTML を装って data: URI を投げ込まれると Stored XSS 経路になるため、
                    # MIME プレフィックスを raster image だけに絞る。
                    allowed_prefixes = (
                        "data:image/jpeg",
                        "data:image/jpg",
                        "data:image/png",
                        "data:image/webp",
                    )
                    if not cover_image.startswith(allowed_prefixes):
                        raise ValueError("Unsupported cover image type")

                    if "," not in cover_image:
                        raise ValueError("Cover image data URL is malformed")
                    image_data = cover_image.split(",", 1)[1]
                    image_binary = base64.b64decode(image_data, validate=True)
                    if len(image_binary) > config.max_upload_bytes:
                        raise ValueError("Cover image is too large")
                    if not _looks_like_image(image_binary):
                        raise ValueError("Cover image bytes do not match supported image format")

                    cover_blob_name = f"{book_base_path}/cover.jpg"
                    # H-13: content_type は使用箇所毎に固定値を渡す。
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
