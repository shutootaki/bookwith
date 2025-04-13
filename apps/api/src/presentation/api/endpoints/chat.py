from fastapi import APIRouter
from src.application.error_handlers import (
    BadRequestException,
    ServiceUnavailableException,
)
from src.application.schemas.base import Answer, Question
from src.application.services import process_question

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def all_chat():
    """全てのチャットを取得するエンドポイント"""
    pass


@router.get("")
async def get_chat():
    """特定のチャットを取得するエンドポイント"""
    pass


@router.post("", response_model=Answer)
async def process_llm(question: Question):
    """質問を処理するエンドポイント"""
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


@router.put("")
async def re_generate():
    """LLMの回答を再生成するエンドポイント"""
    pass
