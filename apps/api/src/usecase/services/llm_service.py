from typing import TYPE_CHECKING, Any

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from src.infrastructure.prompts import rag_prompt
from src.infrastructure.vector import get_vector_store

if TYPE_CHECKING:
    from langchain_core.runnables import RunnableSerializable


def format_documents_as_string(documents: list[Document]) -> str:
    return "\n\n".join(doc.page_content for doc in documents)


def process_question(question: str, tenant_id: str | None = None) -> str:
    model = ChatOpenAI(model="gpt-4o-mini")

    vector_store = get_vector_store("BookContentIndex")
    if tenant_id is None:
        basic_chain: RunnableSerializable[Any, str] = RunnablePassthrough() | model | StrOutputParser()
        return basic_chain.invoke(question)

    vector_store_retriever = vector_store.as_retriever(
        search_kwargs={
            "k": 4,
            "tenant": tenant_id,
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

    return chain.invoke(question)
