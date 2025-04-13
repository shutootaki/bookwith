from fastapi import APIRouter, File, Form, UploadFile

from src.presentation.api.error_messages.error_handlers import (
    BadRequestException,
    ServiceUnavailableException,
)
from src.presentation.api.schemas.book_schema import RagProcessResponse
from src.usecase.book import CreateBookVectorIndexUseCaseImpl

router = APIRouter()


@router.post("/rag", response_model=RagProcessResponse)
async def upload_and_process_rag(tenant_id: str = Form(...), file: UploadFile = File(...)):
    try:
        usecase = CreateBookVectorIndexUseCaseImpl()
        return await usecase.execute(file, tenant_id)
    except ValueError as e:
        raise BadRequestException(str(e))
    except Exception as e:
        raise ServiceUnavailableException(f"Error occurred while processing file: {str(e)}")
