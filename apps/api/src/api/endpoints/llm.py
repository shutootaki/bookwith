from fastapi import APIRouter, HTTPException
from src.models import Answer, Question
from src.services import process_question

router = APIRouter()


@router.post("/llm", response_model=Answer)
async def process_llm(question: Question):
    print("Received question:", question.question)
    try:
        answer = process_question(question.question)
        return Answer(answer=answer)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
