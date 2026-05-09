from fastapi import APIRouter, Depends, HTTPException, status

from src.domain.book.exceptions.book_exceptions import BookNotFoundException, BookPermissionDeniedException
from src.infrastructure.di.injection import get_sync_annotations_usecase
from src.presentation.api.auth import require_user_id
from src.presentation.api.error_messages.book_error_message import BOOK_ACCESS_DENIED, BOOK_NOT_FOUND
from src.presentation.api.schemas.book_schema import BookUpdateRequest
from src.usecase.annotation.update_annotation_use_case import SyncAnnotationsUseCase

router = APIRouter()


@router.put("", status_code=status.HTTP_204_NO_CONTENT)
async def update_annotation(
    book_id: str,
    changes: BookUpdateRequest,
    user_id: str = Depends(require_user_id),
    sync_annotations_usecase: SyncAnnotationsUseCase = Depends(get_sync_annotations_usecase),
) -> None:
    try:
        sync_annotations_usecase.execute(book_id=book_id, user_id=user_id, annotations=changes.annotations)
    except BookPermissionDeniedException:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=BOOK_ACCESS_DENIED)
    except BookNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=BOOK_NOT_FOUND)
