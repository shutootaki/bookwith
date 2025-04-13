"""書籍更新のユースケース"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.domain.book.entities.book import Book
from src.domain.book.exceptions.book_exceptions import BookNotFoundException
from src.domain.book.repositories.book_repository import BookRepository
from src.domain.book.value_objects.book_id import BookId
from src.domain.book.value_objects.book_title import BookTitle


class UpdateBookUseCase(ABC):
    """UpdateBookUseCaseは、書籍情報を更新するためのユースケースインターフェースを定義する。"""

    @abstractmethod
    def execute(
        self,
        book_id: str,
        name: Optional[str] = None,
        author: Optional[str] = None,
        cfi: Optional[str] = None,
        percentage: Optional[float] = None,
        annotations: Optional[List[Dict[str, Any]]] = None,
        book_metadata: Optional[Dict[str, Any]] = None,
        definitions: Optional[List[Dict[str, Any]]] = None,
        configuration: Optional[Dict[str, Any]] = None,
    ) -> Book:
        """書籍情報を更新する"""
        pass


class UpdateBookUseCaseImpl(UpdateBookUseCase):
    """UpdateBookUseCaseImplは、書籍情報を更新するユースケース実装。"""

    def __init__(self, book_repository: BookRepository):
        self.book_repository = book_repository

    def execute(
        self,
        book_id: str,
        name: Optional[str] = None,
        author: Optional[str] = None,
        cfi: Optional[str] = None,
        percentage: Optional[float] = None,
        annotations: Optional[List[Dict[str, Any]]] = None,
        book_metadata: Optional[Dict[str, Any]] = None,
        definitions: Optional[List[Dict[str, Any]]] = None,
        configuration: Optional[Dict[str, Any]] = None,
    ) -> Book:
        """書籍情報を更新する"""
        book_id_obj = BookId(book_id)
        book = self.book_repository.find_by_id(book_id_obj)

        if book is None:
            raise BookNotFoundException(book_id)

        # 名前（タイトル）の更新
        if name is not None and name != book.title.value:
            book_title = BookTitle(name)
            book.update_title(book_title)

        # 著者の更新
        if author is not None:
            book._author = author

        # 読書位置の更新
        if cfi is not None or percentage is not None:
            current_cfi = cfi if cfi is not None else book.cfi
            current_percentage = (
                percentage if percentage is not None else book.percentage
            )
            book.update_reading_progress(current_cfi, current_percentage)

        # メタデータの更新
        if book_metadata is not None:
            book._book_metadata = book_metadata

        # 定義の更新
        if definitions is not None:
            book._definitions = definitions

        # 設定の更新
        if configuration is not None:
            book._configuration = configuration

        # 注釈の更新（アノテーション）
        if annotations is not None:
            book._annotations = annotations

        # 変更をリポジトリに保存
        self.book_repository.save(book)

        return book
