import contextlib
import logging
from abc import ABC, abstractmethod

from src.domain.book.entities.book import Book
from src.domain.book.exceptions.book_exceptions import BookNotFoundException, BookPermissionDeniedException
from src.domain.book.repositories.book_repository import BookRepository
from src.domain.book.value_objects.book_id import BookId
from src.infrastructure.external.gcs import GCSClient
from src.infrastructure.memory.memory_service import MemoryService
from src.usecase.shared.access_control import resolve_owned_or_raise

logger = logging.getLogger(__name__)


def _delete_book_objects(gcs_client: GCSClient, book: Book) -> None:
    """Best-effort delete of GCS objects associated with a book."""
    for path in (book.file_path, book.cover_path):
        if not path:
            continue
        with contextlib.suppress(Exception):
            gcs_client.delete_object(gcs_client.strip_public_url_prefix(path))


class DeleteBookUseCase(ABC):
    """DeleteBookUseCase defines the use case interface for deleting a book."""

    @abstractmethod
    def execute(self, book_id: str, user_id: str) -> None:
        """Delete a specific book."""


class DeleteBookUseCaseImpl(DeleteBookUseCase):
    """DeleteBookUseCaseImpl is the implementation of the use case for deleting a book."""

    def __init__(self, book_repository: BookRepository, memory_service: MemoryService) -> None:
        self.book_repository = book_repository
        self.memory_service = memory_service
        self.gcs_client = GCSClient()

    def execute(self, book_id: str, user_id: str) -> None:
        """Delete a specific book and its related files."""
        book_id_obj = BookId(book_id)
        book = resolve_owned_or_raise(
            find_for_user=lambda: self.book_repository.find_by_id_for_user(book_id_obj, user_id),
            find_any=lambda: self.book_repository.find_by_id(book_id_obj),
            not_found_exc=BookNotFoundException(book_id),
            forbidden_exc=BookPermissionDeniedException(),
        )
        book.assert_owned_by(user_id)

        # 楽観的に user_id 付き削除。並列削除でも所有者でなければ false が返る。
        if not self.book_repository.delete_for_user(book_id_obj, user_id):
            raise BookPermissionDeniedException

        _delete_book_objects(self.gcs_client, book)

        try:
            self.memory_service.delete_book_memories(user_id=book.user_id, book_id=book_id)
        except Exception:
            # L-12: ベクタ DB が消せなくても SQL 行は既に消えている。stack trace を残し
            # 運用側で再同期できるようにする（今後 outbox/再試行キュー導入を推奨）。
            logger.exception("Failed to delete book memories for %s", book_id)


class BulkDeleteBooksUseCase(ABC):
    """BulkDeleteBooksUseCase defines the use case interface for bulk deleting multiple books."""

    @abstractmethod
    def execute(self, book_ids: list[str], user_id: str) -> list[str]:
        """Bulk delete multiple books and return a list of deleted IDs."""


class BulkDeleteBooksUseCaseImpl(BulkDeleteBooksUseCase):
    """BulkDeleteBooksUseCaseImpl is the implementation of the use case for bulk deleting multiple books."""

    def __init__(self, book_repository: BookRepository, memory_service: MemoryService) -> None:
        self.book_repository = book_repository
        self.memory_service = memory_service
        self.gcs_client = GCSClient()

    def execute(self, book_ids: list[str], user_id: str) -> list[str]:
        """Bulk delete multiple books owned by user_id and return a list of deleted IDs."""
        if not book_ids:
            return []

        book_id_objects = [BookId(book_id) for book_id in book_ids]
        # 単一 IN クエリで所有書籍だけを取得し、N+1 を回避する。
        books_to_delete = self.book_repository.find_by_ids_for_user(book_id_objects, user_id)

        if not books_to_delete:
            return []

        deleted_book_ids = self.book_repository.bulk_delete_for_user([book.id for book in books_to_delete], user_id)

        for book in books_to_delete:
            _delete_book_objects(self.gcs_client, book)

            try:
                self.memory_service.delete_book_memories(user_id=book.user_id, book_id=book.id.value)
            except Exception:
                logger.exception("Failed to delete book memories for %s", book.id.value)

        return [book_id.value for book_id in deleted_book_ids]
