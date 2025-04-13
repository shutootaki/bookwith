"""
アノテーションリポジトリの実装
Postgresを使用したリポジトリ実装
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from src.domain.annotation.entities.annotation import Annotation
from src.domain.annotation.repositories.annotation_repository import (
    AnnotationRepository,
)
from src.domain.annotation.value_objects.annotation_id import AnnotationId
from src.infrastructure.postgres.annotation.annotation_dto import AnnotationDTO


class PostgresAnnotationRepository(AnnotationRepository):
    """Postgresを使用したAnnotationRepositoryの実装。"""

    def __init__(self, session: Session):
        self._session = session

    def save(self, annotation: Annotation) -> None:
        """アノテーションを保存または更新する"""
        try:
            existing_dto = (
                self._session.query(AnnotationDTO)
                .filter(AnnotationDTO.id == annotation.id.value)
                .first()
            )

            if existing_dto:
                # 更新
                orm_dict = AnnotationDTO.to_orm_dict(annotation)
                for key, value in orm_dict.items():
                    if key != "id":  # IDは更新しない
                        setattr(existing_dto, key, value)
            else:
                # 新規作成
                dto = AnnotationDTO.from_entity(annotation)
                self._session.add(dto)

            self._session.commit()
        except Exception as e:
            self._session.rollback()
            raise e

    def find_by_id(self, annotation_id: AnnotationId) -> Optional[Annotation]:
        """IDでアノテーションを検索する"""
        dto = (
            self._session.query(AnnotationDTO)
            .filter(AnnotationDTO.id == annotation_id.value)
            .first()
        )
        return dto.to_entity() if dto else None

    def find_all(self) -> List[Annotation]:
        """全てのアノテーションを取得する"""
        dtos = self._session.query(AnnotationDTO).all()
        return [dto.to_entity() for dto in dtos]

    def find_by_book_id(self, book_id: str) -> List[Annotation]:
        """書籍IDでアノテーションを検索する"""
        dtos = (
            self._session.query(AnnotationDTO)
            .filter(AnnotationDTO.book_id == book_id)
            .all()
        )
        return [dto.to_entity() for dto in dtos]

    def find_by_user_id(self, user_id: str) -> List[Annotation]:
        """ユーザーIDでアノテーションを検索する"""
        dtos = (
            self._session.query(AnnotationDTO)
            .filter(AnnotationDTO.user_id == user_id)
            .all()
        )
        return [dto.to_entity() for dto in dtos]

    def find_by_book_id_and_user_id(
        self, book_id: str, user_id: str
    ) -> List[Annotation]:
        """書籍IDとユーザーIDでアノテーションを検索する"""
        dtos = (
            self._session.query(AnnotationDTO)
            .filter(
                AnnotationDTO.book_id == book_id,
                AnnotationDTO.user_id == user_id,
            )
            .all()
        )
        return [dto.to_entity() for dto in dtos]

    def delete(self, annotation_id: AnnotationId) -> None:
        """IDでアノテーションを削除する"""
        try:
            dto = (
                self._session.query(AnnotationDTO)
                .filter(AnnotationDTO.id == annotation_id.value)
                .first()
            )
            if dto:
                self._session.delete(dto)
                self._session.commit()
        except Exception as e:
            self._session.rollback()
            raise e

    def sync_annotations_for_book(
        self, book_id: str, annotations: List[Annotation]
    ) -> None:
        """指定された書籍IDのアノテーションを同期（差分更新）する"""
        try:
            existing_dtos = (
                self._session.query(AnnotationDTO)
                .filter(AnnotationDTO.book_id == book_id)
                .all()
            )
            existing_ids = {dto.id for dto in existing_dtos}
            new_ids = {anno.id.value for anno in annotations}

            # 削除するアノテーションを特定して削除
            ids_to_delete = existing_ids - new_ids
            if ids_to_delete:
                self._session.query(AnnotationDTO).filter(
                    AnnotationDTO.id.in_(ids_to_delete)
                ).delete(synchronize_session=False)

            # 更新または新規作成するアノテーションを処理
            dtos_to_update = []
            dtos_to_create = []
            existing_dtos_map = {dto.id: dto for dto in existing_dtos}

            for anno in annotations:
                if anno.id.value in existing_ids:
                    # 更新
                    existing_dto = existing_dtos_map[anno.id.value]
                    orm_dict = AnnotationDTO.to_orm_dict(anno)
                    for key, value in orm_dict.items():
                        if key != "id":
                            setattr(existing_dto, key, value)
                    # SQLAlchemyは変更を追跡するので、セッションに追加する必要はない
                else:
                    # 新規作成
                    dto = AnnotationDTO.from_entity(anno)
                    # book_idがエンティティに含まれていない場合があるので、ここで設定
                    dto.book_id = book_id
                    dtos_to_create.append(dto)

            # 新規作成をバルクで実行
            if dtos_to_create:
                self._session.add_all(dtos_to_create)

            self._session.commit()
        except Exception as e:
            self._session.rollback()
            raise e
