"""AIレスポンス生成サービス."""

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from weaviate.classes.query import Filter

from src.infrastructure.vector import get_book_content_vector_store
from src.usecase.message.highlight_searcher import HighlightSearcher

if TYPE_CHECKING:
    from langchain_core.runnables import RunnableSerializable


class AIResponseGenerator:
    """AIレスポンスの生成とストリーミングを行うサービス."""

    def __init__(self) -> None:
        """AIレスポンス生成サービスの初期化."""
        self.highlight_searcher = HighlightSearcher()

    async def stream_ai_response(
        self,
        question: str,
        user_id: str,
        book_id: str | None = None,
    ) -> AsyncGenerator[str]:
        """LLMの応答をストリーミングで返す."""
        model = ChatOpenAI(model_name="gpt-4o", streaming=True)

        # book_idがない場合は記憶ベースの応答のみを返す
        if book_id is None:
            async for chunk in self._stream_memory_based_response(question, model):
                yield chunk
            return

        # book_idがある場合は記憶ベースとRAGベースを組み合わせる
        async for chunk in self._stream_hybrid_response(question, user_id, book_id, model):
            yield chunk

    async def _stream_memory_based_response(self, question: str, model: ChatOpenAI) -> AsyncGenerator[str]:
        """記憶ベースのレスポンスをストリーミングで返す."""
        basic_chain: RunnableSerializable[Any, str] = RunnablePassthrough() | model | StrOutputParser()

        async for chunk in basic_chain.astream(question):
            yield chunk

    async def _stream_hybrid_response(self, question: str, user_id: str, book_id: str, model: ChatOpenAI) -> AsyncGenerator[str]:
        """記憶ベースとRAGベースを組み合わせたレスポンスをストリーミングで返す."""
        # 書籍コンテンツのベクトルストアを取得
        vector_store = get_book_content_vector_store()
        vector_store_retriever = vector_store.as_retriever(
            search_kwargs={"k": 4, "tenant": user_id, "filters": Filter.by_property("book_id").equal(book_id)}
        )

        # 関連するハイライトを検索
        highlight_texts = self.highlight_searcher.search_relevant_highlights(question, user_id, book_id)

        # ハイブリッドチェーンを構築
        hybrid_chain: RunnableSerializable[Any, str] = (
            {
                "book_content": vector_store_retriever | self._format_documents_as_string,
                "highlight_texts": lambda _: highlight_texts,
                "question": lambda _: question,
            }
            | ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """あなたは丁寧で役立つアシスタントです。
ユーザーの質問に対して、以下の情報源を考慮して回答してください：
1. ユーザーとの会話履歴（質問に含まれています）
2. 関連する書籍の内容（コンテキスト情報として提供されます）
3. ユーザーがハイライトした箇所（関連があれば含まれます）

会話の文脈と書籍の情報、ハイライトの両方を考慮して、一貫性のある適切な回答を提供してください。
書籍の情報やハイライトが関連している場合は、それを優先して使用してください。
質問に関連する情報がコンテキストに含まれていない場合は、会話の文脈のみに基づいて回答してください。
\n\n書籍からの関連情報:\n {book_content}\n\nハイライトした箇所:\n {highlight_texts}\n\n
                    """,
                    ),
                    ("human", "会話の文脈を含む質問: {question}"),
                ]
            )
            | model
            | StrOutputParser()
        )

        async for chunk in hybrid_chain.astream(question):
            yield chunk

    def _format_documents_as_string(self, documents: list[Document]) -> str:
        """ドキュメントのリストを文字列としてフォーマットする."""
        return "\n\n".join(doc.page_content for doc in documents)
