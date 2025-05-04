import asyncio

from fastapi import APIRouter, Depends, File, Form, UploadFile

from src.infrastructure.di.injection import get_create_book_vector_index_usecase
from src.presentation.api.error_messages.error_handlers import (
    BadRequestException,
    ServiceUnavailableException,
)
from src.presentation.api.schemas.book_schema import RagProcessResponse
from src.usecase.book.create_book_vector_index_usecase import CreateBookVectorIndexUseCase

router = APIRouter()


@router.post("", response_model=RagProcessResponse)
async def upload_and_process_rag(
    user_id: str = Form(...),
    file: UploadFile = File(...),  # noqa: B008
    usecase: CreateBookVectorIndexUseCase = Depends(get_create_book_vector_index_usecase),
):
    try:
        # 5秒間sleep
        await asyncio.sleep(5)
        return RagProcessResponse(
            file_name=file.filename,
            chunk_count=10,
            user_id=user_id,
            index_name="test",
            chunks=[],
        )
        # return await usecase.execute(file, user_id)
    except ValueError as e:
        raise BadRequestException(str(e))
    except Exception as e:
        raise ServiceUnavailableException(f"Error occurred while processing file: {str(e)}")
