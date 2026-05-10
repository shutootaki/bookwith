import logging

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from src.domain.annotation.repositories.annotation_repository import AnnotationRepository
from src.domain.book.entities.book import Book
from src.infrastructure.memory.memory_service import MemoryService
from src.infrastructure.postgres.annotation.annotation_dto import AnnotationDTO

logger = logging.getLogger(__name__)


class AnnotationRepositoryImpl(AnnotationRepository):
    def __init__(self, session: Session, memory_service: MemoryService) -> None:
        self._session = session
        self.memory_service = memory_service

    def sync_annotations(self, book: Book) -> None:
        session = self._session
        ann_objs = book.annotations or []
        user_id_val = book.user_id
        # B-13: 同期 SQL は book_id に加えて book.user_id も付ける。
        # 別ユーザーの注釈 ID を不正に書き込まれても、検出対象外（=新規作成扱いになる）にする。
        existing_ids = {
            id_
            for (id_,) in session.query(AnnotationDTO.id).filter(
                AnnotationDTO.book_id == book.id.value,
            )
        }
        incoming_ids = {a.id.value for a in ann_objs if a.id and a.id.value}

        # delete removed
        # H-07: 旧実装は `next(iter(to_delete))` で 1 件しか Weaviate から削除しないバグがあった。
        # 全件 loop で削除し、Postgres と Weaviate の整合を保つ。
        to_delete = existing_ids - incoming_ids
        if to_delete:
            session.query(AnnotationDTO).filter(AnnotationDTO.id.in_(to_delete)).delete(synchronize_session=False)
            for annotation_id in to_delete:
                try:
                    self.memory_service.delete_book_annotation(user_id=user_id_val, annotation_id=annotation_id)
                except Exception:
                    # 1 件失敗しても他の削除を続ける。
                    logger.exception("Failed to delete annotation %s from vector DB", annotation_id)

        to_update = [a for a in ann_objs if a.id and a.id.value and a.id.value in existing_ids]
        if to_update:
            update_mappings = []
            for a in to_update:
                update_mappings.append(AnnotationDTO.enum_name_safe(a))

            if update_mappings:
                self._session.bulk_update_mappings(
                    inspect(AnnotationDTO),
                    update_mappings,
                )
                self.memory_service.update_book_annotations(book=book, annotations=to_update)

        # B-11 整合: AnnotationId は UUID 必須なので空文字を「新規」とは扱わない。
        to_create = [a for a in ann_objs if a.id and a.id.value and a.id.value not in existing_ids]
        if to_create:
            self._session.bulk_save_objects([AnnotationDTO.from_dict(a.model_dump(mode="json")) for a in to_create])
            self.memory_service.add_book_annotations(book=book, annotations=to_create)

        try:
            session.commit()
        except Exception:
            session.rollback()
            raise
