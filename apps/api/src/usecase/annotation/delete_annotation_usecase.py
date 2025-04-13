"""
アノテーション削除ユースケース
"""

from abc import ABC, abstractmethod

from src.domain.annotation.exceptions.annotation_exceptions import (
    AnnotationNotFoundError,
)
from src.domain.annotation.repositories.annotation_repository import (
    AnnotationRepository,
)
from src.domain.annotation.value_objects.annotation_id import AnnotationId


class DeleteAnnotationUseCase(ABC):
    """アノテーション削除ユースケースのインターフェース"""

    @abstractmethod
    def execute(self, annotation_id: str) -> None:
        """アノテーションを削除する"""
        pass


class DeleteAnnotationUseCaseImpl(DeleteAnnotationUseCase):
    """アノテーション削除ユースケースの実装"""

    def __init__(self, annotation_repository: AnnotationRepository):
        self.annotation_repository = annotation_repository

    def execute(self, annotation_id: str) -> None:
        """アノテーションを削除する"""
        # 存在確認
        annotation = self.annotation_repository.find_by_id(AnnotationId(annotation_id))
        if annotation is None:
            raise AnnotationNotFoundError(annotation_id)

        # 削除実行
        self.annotation_repository.delete(AnnotationId(annotation_id))
