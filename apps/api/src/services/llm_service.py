from typing import Any, List

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableSerializable
from langchain_openai import ChatOpenAI
from src.prompts import rag_prompt
from src.vector import get_shared_vector_store


# ドキュメントをフォーマット
def format_documents_as_string(documents: List[Document]) -> str:
    return "\n\n".join([doc.page_content for doc in documents])


def process_question(question: str) -> str:
    """質問処理のためのサービス関数"""
    # ベクトルストアを取得
    vector_store = get_shared_vector_store()

    # OpenAIモデルの設定
    model = ChatOpenAI(model="gpt-4o-mini")

    if vector_store:
        # ベクトルストアが存在する場合はRAGを使用
        # リトリーバーを使って関連ドキュメントを取得
        vector_store_retriever = vector_store.as_retriever()

        # RAGチェーンの構築
        chain: RunnableSerializable[Any, str] = (
            {
                "context": vector_store_retriever | format_documents_as_string,
                "question": RunnablePassthrough(),
            }
            | rag_prompt
            | model
            | StrOutputParser()
        )
    else:
        # ベクトルストアが存在しない場合は直接LLMにリクエスト
        chain = RunnablePassthrough() | model | StrOutputParser()

    # 質問を処理して回答を返す
    return chain.invoke(question)
