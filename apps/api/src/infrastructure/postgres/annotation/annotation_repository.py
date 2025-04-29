from sqlalchemy import inspect
from sqlalchemy.orm import Session

from src.domain.annotation.repositories.annotation_repository import AnnotationRepository
from src.domain.book.entities.book import Book
from src.infrastructure.memory.memory_service import MemoryService
from src.infrastructure.postgres.annotation.annotation_dto import AnnotationDTO


class AnnotationRepositoryImpl(AnnotationRepository):
    def __init__(self, session: Session, memory_service: MemoryService) -> None:
        self._session = session
        self.memory_service = memory_service

    def sync_annotations(self, book: Book) -> None:
        session = self._session
        ann_objs = book.annotations or []
        user_id_val = book.user_id
        existing_ids = {id_ for (id_,) in session.query(AnnotationDTO.id).filter_by(book_id=book.id.value)}
        incoming_ids = {a.id.value for a in ann_objs}

        # delete removed
        to_delete = existing_ids - incoming_ids
        if to_delete:
            session.query(AnnotationDTO).filter(AnnotationDTO.id.in_(to_delete)).delete(synchronize_session=False)
            self.memory_service.delete_book_annotation(user_id=user_id_val, annotation_id=next(iter(to_delete)))

        to_update = [a for a in book.annotations if a.id and a.id.value in existing_ids]
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

        to_create = [a for a in book.annotations if not a.id.value or a.id.value not in existing_ids]
        if to_create:
            self._session.bulk_save_objects([AnnotationDTO.from_dict(a.model_dump(mode="json")) for a in to_create])
            self.memory_service.add_book_annotations(book=book, annotations=to_create)

        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
