from typing import Any, List, Optional

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableSerializable
from langchain_openai import ChatOpenAI
from src.prompts import rag_prompt
from src.vector import get_vector_store


# ドキュメントをフォーマット
def format_documents_as_string(documents: List[Document]) -> str:
    """ドキュメントリストを文字列にフォーマット"""
    return "\n\n".join(doc.page_content for doc in documents)


def process_question(question: str, tenant_id: Optional[str] = None) -> str:
    """
    質問処理のためのサービス関数

    Args:
        question: 処理する質問文
        tenant_id: 使用するテナントID

    Returns:
        回答文字列
    """
    # インデックス名とテナントIDを使用してベクトルストアを取得
    vector_store = get_vector_store("BookContentIndex")
    if not vector_store:
        return f"インデックス '{f'BookContent_{tenant_id}'}' が見つかりませんでした。"

    # OpenAIモデルの設定
    model = ChatOpenAI(model="gpt-4o-mini")

    # ベクトルストアからリトリーバーを作成（テナントを指定）
    vector_store_retriever = vector_store.as_retriever(
        search_kwargs={
            "k": 4,  # 取得するドキュメント数
            "tenant": tenant_id,  # テナントを指定
        }
    )

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

    # 質問を処理して回答を返す
    return chain.invoke(question)
