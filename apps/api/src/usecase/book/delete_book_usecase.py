"""書籍削除のユースケース"""

from abc import ABC, abstractmethod
from typing import List

from src.domain.book.exceptions.book_exceptions import BookNotFoundException
from src.domain.book.repositories.book_repository import BookRepository
from src.domain.book.value_objects.book_id import BookId
from src.infrastructure.external.gcs import GCSClient


class DeleteBookUseCase(ABC):
    """DeleteBookUseCaseは、書籍を削除するためのユースケースインターフェースを定義する。"""

    @abstractmethod
    def execute(self, book_id: str) -> None:
        """特定の書籍を削除する"""
        pass


class DeleteBookUseCaseImpl(DeleteBookUseCase):
    """DeleteBookUseCaseImplは、書籍を削除するユースケース実装。"""

    def __init__(self, book_repository: BookRepository):
        self.book_repository = book_repository
        self.gcs_client = GCSClient()

    def execute(self, book_id: str) -> None:
        """特定の書籍を削除し、関連するファイルも削除する"""
        book_id_obj = BookId(book_id)
        book = self.book_repository.find_by_id(book_id_obj)

        if book is None:
            raise BookNotFoundException(book_id)

        # 書籍を論理削除
        book.mark_as_deleted()
        self.book_repository.save(book)

        # GCSからファイルを削除
        bucket = self.gcs_client.get_client().bucket(self.gcs_client.bucket_name)

        # 書籍ファイルの削除
        if book.file_path:
            file_path = book.file_path.replace(
                f"{self.gcs_client.get_gcs_url()}/{self.gcs_client.bucket_name}/", ""
            )
            blob = bucket.blob(file_path)
            try:
                blob.delete()
            except Exception as e:
                print(f"書籍ファイルの削除中にエラーが発生しました: {str(e)}")

        # カバー画像の削除
        if book.cover_path:
            cover_path = book.cover_path.replace(
                f"{self.gcs_client.get_gcs_url()}/{self.gcs_client.bucket_name}/", ""
            )
            blob = bucket.blob(cover_path)
            try:
                blob.delete()
            except Exception as e:
                print(f"カバー画像の削除中にエラーが発生しました: {str(e)}")


class BulkDeleteBooksUseCase(ABC):
    """BulkDeleteBooksUseCaseは、複数の書籍を一括削除するためのユースケースインターフェースを定義する。"""

    @abstractmethod
    def execute(self, book_ids: List[str]) -> List[str]:
        """複数の書籍を一括削除し、削除されたIDのリストを返す"""
        pass


class BulkDeleteBooksUseCaseImpl(BulkDeleteBooksUseCase):
    """BulkDeleteBooksUseCaseImplは、複数の書籍を一括削除するユースケース実装。"""

    def __init__(self, book_repository: BookRepository):
        self.book_repository = book_repository
        self.gcs_client = GCSClient()

    def execute(self, book_ids: List[str]) -> List[str]:
        """複数の書籍を一括削除し、削除されたIDのリストを返す"""
        if not book_ids:
            return []

        # BookIdオブジェクトのリストに変換
        book_id_objects = [BookId(book_id) for book_id in book_ids]

        # 削除対象の書籍を取得
        books_to_delete = []
        for book_id_obj in book_id_objects:
            book = self.book_repository.find_by_id(book_id_obj)
            if book:
                books_to_delete.append(book)

        if not books_to_delete:
            return []

        # 書籍を一括削除
        deleted_book_ids = self.book_repository.bulk_delete(
            [book.id for book in books_to_delete]
        )

        # GCSからファイルを削除
        bucket = self.gcs_client.get_client().bucket(self.gcs_client.bucket_name)

        for book in books_to_delete:
            # 書籍ファイルの削除
            if book.file_path:
                file_path = book.file_path.replace(
                    f"{self.gcs_client.get_gcs_url()}/{self.gcs_client.bucket_name}/",
                    "",
                )
                blob = bucket.blob(file_path)
                try:
                    blob.delete()
                except Exception as e:
                    print(f"書籍ファイルの削除中にエラーが発生しました: {str(e)}")

            # カバー画像の削除
            if book.cover_path:
                cover_path = book.cover_path.replace(
                    f"{self.gcs_client.get_gcs_url()}/{self.gcs_client.bucket_name}/",
                    "",
                )
                blob = bucket.blob(cover_path)
                try:
                    blob.delete()
                except Exception as e:
                    print(f"カバー画像の削除中にエラーが発生しました: {str(e)}")

        # 削除されたIDの文字列リストを返す
        return [book_id.value for book_id in deleted_book_ids]
