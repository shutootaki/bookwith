"""
アノテーション検索ユースケース
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.annotation.entities.annotation import Annotation
from src.domain.annotation.repositories.annotation_repository import (
    AnnotationRepository,
)


class FindAnnotationsUseCase(ABC):
    """アノテーション検索ユースケースのインターフェース"""

    @abstractmethod
    def execute(
        self, book_id: Optional[str] = None, user_id: Optional[str] = None
    ) -> List[Annotation]:
        """条件に基づいてアノテーションを検索する"""
        pass


class FindAnnotationsUseCaseImpl(FindAnnotationsUseCase):
    """アノテーション検索ユースケースの実装"""

    def __init__(self, annotation_repository: AnnotationRepository):
        self.annotation_repository = annotation_repository

    def execute(
        self, book_id: Optional[str] = None, user_id: Optional[str] = None
    ) -> List[Annotation]:
        """条件に基づいてアノテーションを検索する"""
        if book_id and user_id:
            return self.annotation_repository.find_by_book_id_and_user_id(
                book_id, user_id
            )
        elif book_id:
            return self.annotation_repository.find_by_book_id(book_id)
        elif user_id:
            return self.annotation_repository.find_by_user_id(user_id)
        else:
            return self.annotation_repository.find_all()
