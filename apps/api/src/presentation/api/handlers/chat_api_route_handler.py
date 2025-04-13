from fastapi import APIRouter

from src.application.schemas.base import Answer, Question
from src.presentation.api.error_messages.error_handlers import (
    BadRequestException,
    ServiceUnavailableException,
)
from src.usecase.services.llm_service import process_question

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def all_chat():
    pass


@router.get("")
async def get_chat():
    pass


@router.post("", response_model=Answer)
async def process_llm(question: Question):
    try:
        answer = process_question(question=question.question, tenant_id=question.tenant_id)
        return Answer(answer=answer)
    except ValueError as e:
        raise BadRequestException(str(e))
    except Exception as e:
        raise ServiceUnavailableException(f"Error occurred while processing question: {str(e)}")


@router.put("")
async def re_generate():
    pass
