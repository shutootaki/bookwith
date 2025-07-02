import base64
from io import BytesIO

from fastapi import APIRouter, Depends, UploadFile
from starlette.datastructures import Headers

from src.infrastructure.di.injection import get_create_book_vector_index_usecase
from src.presentation.api.error_messages.error_handlers import (
    BadRequestException,
    ServiceUnavailableException,
)
from src.presentation.api.schemas.book_schema import RagProcessRequest, RagProcessResponse
from src.usecase.book.create_book_vector_index_usecase import CreateBookVectorIndexUseCase

router = APIRouter()


@router.post("", response_model=RagProcessResponse)
async def upload_and_process_rag(
    request: RagProcessRequest,
    usecase: CreateBookVectorIndexUseCase = Depends(get_create_book_vector_index_usecase),
):
    """Base64 で送られてきた EPUB をデコードし、ベクトルストアにインデックス化する."""
    try:
        decoded_bytes = base64.b64decode(request.file_data)
        file_like = BytesIO(decoded_bytes)
        upload_file = UploadFile(
            file_like,
            filename=request.file_name,
            headers=Headers({"content-type": "application/epub+zip"}),
        )

        return await usecase.execute(upload_file, request.user_id, request.book_id)
    except ValueError as e:
        raise BadRequestException(str(e))
    except Exception as e:
        raise ServiceUnavailableException(f"Error occurred while processing file: {str(e)}")
