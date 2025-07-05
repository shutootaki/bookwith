import contextlib
import logging
from abc import ABC, abstractmethod

from src.domain.book.exceptions.book_exceptions import BookNotFoundException
from src.domain.book.repositories.book_repository import BookRepository
from src.domain.book.value_objects.book_id import BookId
from src.infrastructure.external.gcs import GCSClient
from src.infrastructure.memory.memory_service import MemoryService

logger = logging.getLogger(__name__)


class DeleteBookUseCase(ABC):
    """DeleteBookUseCase defines the use case interface for deleting a book."""

    @abstractmethod
    def execute(self, book_id: str) -> None:
        """Delete a specific book."""


class DeleteBookUseCaseImpl(DeleteBookUseCase):
    """DeleteBookUseCaseImpl is the implementation of the use case for deleting a book."""

    def __init__(self, book_repository: BookRepository, memory_service: MemoryService) -> None:
        self.book_repository = book_repository
        self.memory_service = memory_service
        self.gcs_client = GCSClient()

    def execute(self, book_id: str) -> None:
        """Delete a specific book and its related files."""
        book_id_obj = BookId(book_id)
        book = self.book_repository.find_by_id(book_id_obj)

        if book is None:
            raise BookNotFoundException(book_id)

        # Logical deletion of the book
        book.mark_as_deleted()
        self.book_repository.save(book)

        # Delete files from GCS
        bucket = self.gcs_client.get_client().bucket(self.gcs_client.bucket_name)

        # Delete book file
        if book.file_path:
            file_path = book.file_path.replace(f"{self.gcs_client.get_gcs_url()}/{self.gcs_client.bucket_name}/", "")
            blob = bucket.blob(file_path)
            with contextlib.suppress(Exception):
                blob.delete()

        # Delete cover image
        if book.cover_path:
            cover_path = book.cover_path.replace(f"{self.gcs_client.get_gcs_url()}/{self.gcs_client.bucket_name}/", "")
            blob = bucket.blob(cover_path)
            with contextlib.suppress(Exception):
                blob.delete()

        # ベクターDBから本のデータを削除
        try:
            self.memory_service.delete_book_memories(user_id=book.user_id, book_id=book_id)
        except Exception as e:
            logger.error(f"Failed to delete book memories: {str(e)}")


class BulkDeleteBooksUseCase(ABC):
    """BulkDeleteBooksUseCase defines the use case interface for bulk deleting multiple books."""

    @abstractmethod
    def execute(self, book_ids: list[str]) -> list[str]:
        """Bulk delete multiple books and return a list of deleted IDs."""


class BulkDeleteBooksUseCaseImpl(BulkDeleteBooksUseCase):
    """BulkDeleteBooksUseCaseImpl is the implementation of the use case for bulk deleting multiple books."""

    def __init__(self, book_repository: BookRepository, memory_service: MemoryService) -> None:
        self.book_repository = book_repository
        self.memory_service = memory_service
        self.gcs_client = GCSClient()

    def execute(self, book_ids: list[str]) -> list[str]:
        """Bulk delete multiple books and return a list of deleted IDs."""
        if not book_ids:
            return []

        # Convert to a list of BookId objects
        book_id_objects = [BookId(book_id) for book_id in book_ids]

        # Get books to delete
        books_to_delete = []
        for book_id_obj in book_id_objects:
            book = self.book_repository.find_by_id(book_id_obj)
            if book:
                books_to_delete.append(book)

        if not books_to_delete:
            return []

        # Bulk delete books
        deleted_book_ids = self.book_repository.bulk_delete([book.id for book in books_to_delete])

        # Delete files from GCS
        bucket = self.gcs_client.get_client().bucket(self.gcs_client.bucket_name)

        for book in books_to_delete:
            # Delete book file
            if book.file_path:
                file_path = book.file_path.replace(
                    f"{self.gcs_client.get_gcs_url()}/{self.gcs_client.bucket_name}/",
                    "",
                )
                blob = bucket.blob(file_path)
                with contextlib.suppress(Exception):
                    blob.delete()

            # Delete cover image
            if book.cover_path:
                cover_path = book.cover_path.replace(
                    f"{self.gcs_client.get_gcs_url()}/{self.gcs_client.bucket_name}/",
                    "",
                )
                blob = bucket.blob(cover_path)
                with contextlib.suppress(Exception):
                    blob.delete()

            # ベクターDBから本のデータを削除
            try:
                self.memory_service.delete_book_memories(user_id=book.user_id, book_id=book.id.value)
            except Exception as e:
                logger.error(f"Failed to delete book memories for {book.id.value}: {str(e)}")

        # Return a list of deleted ID strings
        return [book_id.value for book_id in deleted_book_ids]
