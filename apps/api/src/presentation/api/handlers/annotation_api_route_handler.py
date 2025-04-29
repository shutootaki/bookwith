from fastapi import APIRouter, Depends, status

from src.infrastructure.di.injection import get_sync_annotations_usecase
from src.presentation.api.schemas.book_schema import BookUpdateRequest
from src.usecase.annotation.update_annotation_use_case import SyncAnnotationsUseCase

# Router configuration
router = APIRouter(prefix="/books/{book_id}/annotations", tags=["annotations"])


@router.put("", status_code=status.HTTP_204_NO_CONTENT)
async def update_annotation(
    book_id: str,
    changes: BookUpdateRequest,
    sync_annotations_usecase: SyncAnnotationsUseCase = Depends(get_sync_annotations_usecase),
) -> None:
    sync_annotations_usecase.execute(book_id=book_id, annotations=changes.annotations)
