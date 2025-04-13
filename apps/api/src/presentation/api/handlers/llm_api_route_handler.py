from fastapi import APIRouter

from src.application.schemas.base import Answer, Question
from src.presentation.api.error_messages.error_handlers import (
    BadRequestException,
    ServiceUnavailableException,
)
from src.usecase.services.llm_service import process_question

router = APIRouter()


@router.post("/llm", response_model=Answer)
async def process_llm(body: Question):
    try:
        answer = process_question(question=body.question, tenant_id=body.tenant_id)
        return Answer(answer=answer)
    except ValueError as e:
        raise BadRequestException(str(e))
    except Exception as e:
        raise ServiceUnavailableException(f"Error occurred while processing question: {str(e)}")
