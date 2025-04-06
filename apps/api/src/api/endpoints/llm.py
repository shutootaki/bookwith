from fastapi import APIRouter
from src.models import Answer, Question
from src.services import process_question
from src.utils import BadRequestException, ServiceUnavailableException

router = APIRouter()


@router.post("/llm", response_model=Answer)
async def process_llm(question: Question):
    try:
        # テナントIDが指定されている場合は、それを使用して質問を処理
        answer = process_question(
            question=question.question, tenant_id=question.tenant_id
        )
        return Answer(answer=answer)
    except ValueError as e:
        # 入力値に関するエラーの場合
        raise BadRequestException(str(e))
    except Exception as e:
        # その他のエラーの場合
        raise ServiceUnavailableException(
            f"Error occurred while processing question: {str(e)}"
        )
