"""書籍作成のユースケース"""

import base64
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from src.domain.book.entities.book import Book
from src.domain.book.repositories.book_repository import BookRepository
from src.domain.book.value_objects.book_description import BookDescription
from src.domain.book.value_objects.book_title import BookTitle
from src.infrastructure.external.gcs import GCSClient


class CreateBookUseCase(ABC):
    """CreateBookUseCaseは、新しいBookを作成するためのユースケースインターフェースを定義する。"""

    @abstractmethod
    def execute(
        self,
        user_id: str,
        file_name: str,
        file_data: str,
        book_name: Optional[str] = None,
        cover_image: Optional[str] = None,
        book_metadata: Optional[str] = None,
    ) -> Book:
        """新しいBookを作成して返す"""
        pass


class CreateBookUseCaseImpl(CreateBookUseCase):
    """CreateBookUseCaseImplは、新しいBookを作成するためのユースケース実装。"""

    def __init__(self, book_repository: BookRepository):
        self.book_repository = book_repository
        self.gcs_client = GCSClient()

    def execute(
        self,
        user_id: str,
        file_name: str,
        file_data: str,
        book_name: Optional[str] = None,
        cover_image: Optional[str] = None,
        book_metadata: Optional[str] = None,
    ) -> Book:
        """新しいBookを作成して保存し、作成したBookエンティティを返す"""
        # タイトルの決定
        title = BookTitle(book_name if book_name else file_name)

        # ファイルデータのデコード
        decoded_file_data = base64.b64decode(file_data)

        # メタデータの処理
        metadata: Dict[str, Any] = {}
        if book_metadata:
            try:
                metadata = json.loads(book_metadata)
            except json.JSONDecodeError:
                pass

        # GCSにファイルを保存
        bucket = self.gcs_client.get_client().bucket(self.gcs_client.bucket_name)

        # 一意なIDを持つBookエンティティを作成
        book = Book.create(
            title=title,
            user_id=user_id,
            file_path="",  # 後で更新
            description=BookDescription(),
            author=metadata.get("creator", None),
            size=len(decoded_file_data),
            book_metadata=metadata,
        )

        # EPUBファイルの保存
        epub_blob_name = f"books/{user_id}/{book.id.value}/book.epub"
        blob = bucket.blob(epub_blob_name)
        blob.upload_from_string(decoded_file_data, content_type="application/epub+zip")

        file_path = f"{self.gcs_client.get_gcs_url()}/{self.gcs_client.bucket_name}/{epub_blob_name}"

        # カバー画像の処理と保存
        cover_path = None
        if cover_image and cover_image.startswith("data:image/"):
            try:
                image_data = cover_image.split(",")[1]
                image_binary = base64.b64decode(image_data)

                cover_blob_name = f"books/{user_id}/{book.id.value}/cover.jpg"
                cover_blob = bucket.blob(cover_blob_name)
                cover_blob.upload_from_string(image_binary, content_type="image/jpeg")

                cover_path = f"{self.gcs_client.get_gcs_url()}/{self.gcs_client.bucket_name}/{cover_blob_name}"
            except Exception as e:
                # エラーログを出力するが、カバー画像がなくても書籍の作成は続行
                print(f"カバー画像の保存中にエラーが発生しました: {str(e)}")

        # ファイルパスとカバーパスを設定した新しいBookエンティティを作成
        updated_book = Book(
            id=book.id,
            title=book.title,
            user_id=book.user_id,
            file_path=file_path,
            description=book.description,
            author=book.author,
            cover_path=cover_path,
            size=book.size,
            book_metadata=book.book_metadata,
            created_at=book.created_at,
            updated_at=book.updated_at,
        )

        # リポジトリに保存
        self.book_repository.save(updated_book)

        return updated_book
