from fastapi import APIRouter
from src.application.error_handlers import (
    BadRequestException,
    ServiceUnavailableException,
)
from src.application.schemas.base import Answer, Question
from src.application.services import process_question

router = APIRouter()


@router.post("/llm", response_model=Answer)
async def process_llm(body: Question):
    try:
        # テナントIDが指定されている場合は、それを使用して質問を処理
        answer = process_question(question=body.question, tenant_id=body.tenant_id)
        return Answer(answer=answer)
    except ValueError as e:
        # 入力値に関するエラーの場合
        raise BadRequestException(str(e))
    except Exception as e:
        # その他のエラーの場合
        raise ServiceUnavailableException(
            f"Error occurred while processing question: {str(e)}"
        )
