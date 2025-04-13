from fastapi import APIRouter, File, Form, UploadFile

from src.application.schemas.base import RagProcessResponse
from src.presentation.api.error_messages.error_handlers import (
    BadRequestException,
    ServiceUnavailableException,
)
from src.usecase.services.rag_service import process_epub_file

router = APIRouter()


@router.post("/rag", response_model=RagProcessResponse)
async def upload_and_process_rag(user_id: str = Form(...), book_id: str = Form(...), file: UploadFile = File(...)):
    try:
        return await process_epub_file(file, user_id, book_id)
    except ValueError as e:
        raise BadRequestException(str(e))
    except Exception as e:
        raise ServiceUnavailableException(f"Error occurred while processing file: {str(e)}")
