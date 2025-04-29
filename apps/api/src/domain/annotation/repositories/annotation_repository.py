from abc import ABC, abstractmethod

from src.domain.book.entities.book import Book


class AnnotationRepository(ABC):
    @abstractmethod
    def sync_annotations(self, book: Book) -> None:
        """書籍に関連する全てのアノテーションを同期する"""
