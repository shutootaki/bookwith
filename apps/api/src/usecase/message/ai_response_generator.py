"""AIレスポンス生成サービス."""

import logging
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

logger = logging.getLogger(__name__)


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
        logger.info("=== Starting hybrid response generation ===")
        logger.info(f"Question: {question}")
        logger.info(f"User ID: {user_id}, Book ID: {book_id}")

        # 書籍コンテンツのベクトルストアを取得
        vector_store = get_book_content_vector_store()
        vector_store_retriever = vector_store.as_retriever(
            search_kwargs={"k": 4, "tenant": user_id, "filters": Filter.by_property("book_id").equal(book_id)}
        )

        # 関連するハイライトを検索（引用情報付き）
        highlight_texts = self.highlight_searcher.search_relevant_highlights(question, user_id, book_id)
        logger.info(f"Retrieved highlights: {highlight_texts[:200]}...")  # 最初の200文字のみログ出力

        # デバッグ用のラムダ関数
        def debug_book_content(docs_string: str) -> str:
            logger.info("=== Book content being sent to LLM ===")
            logger.info(f"Content length: {len(docs_string)} characters")
            logger.debug(f"Content preview: {docs_string[:500]}...")
            return docs_string

        # ハイブリッドチェーンを構築
        hybrid_chain: RunnableSerializable[Any, str] = (
            {
                "book_content": vector_store_retriever | self._format_documents_as_string | debug_book_content,
                "highlight_texts": lambda _: highlight_texts,
                "question": lambda _: question,
            }
            | ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """あなたは書籍の内容を参照しながら質問に答えるアシスタントです。

【重要な指示】
書籍から情報を引用する際は、必ず以下の形式に従ってください：

1. 書籍の内容を参照したら、文末に上付き数字（¹、²、³など）を付ける
2. 【参照1】【参照2】などの番号と対応させる
3. 回答の最後に必ず「参照箇所：」セクションを追加する

【回答例】
質問：AIについて教えてください
回答：AIは人工知能のことで、機械学習によって発展しています¹。特に深層学習の登場により大きな進歩を遂げました²。

参照箇所：
¹ 第1章: AIの基礎（約15%の位置）
² 第3章: 深層学習（約45%の位置）

【提供された情報】
書籍からの関連情報:
{book_content}

ハイライトした箇所:
{highlight_texts}

【引用位置情報】が提供されているので、必ずそれを「参照箇所：」セクションで使用してください。""",
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
        """ドキュメントのリストを文字列としてフォーマットする（引用情報付き）."""
        if not documents:
            logger.warning("No documents retrieved from vector store")
            return ""

        logger.info(f"=== Formatting {len(documents)} documents ===")
        content_parts = []
        citation_info = []

        for idx, doc in enumerate(documents):
            # デバッグ: ドキュメントのメタデータをログ出力
            logger.debug(f"Document {idx + 1} metadata: {doc.metadata}")
            logger.debug(f"Document {idx + 1} content preview: {doc.page_content[:100]}...")

            # 上付き数字のマッピング
            superscript_map = {1: "¹", 2: "²", 3: "³", 4: "⁴", 5: "⁵", 6: "⁶", 7: "⁷", 8: "⁸", 9: "⁹"}
            ref_num = idx + 1
            superscript = superscript_map.get(ref_num, f"({ref_num})")

            # 引用番号を付けてコンテンツを追加（先頭に番号を明示）
            content_parts.append(f"【参照{ref_num}】 {doc.page_content}")

            # 引用情報を収集
            position = doc.metadata.get("position_percent", "不明")
            chapter_title = doc.metadata.get("chapter_title", "")

            # 章タイトルがある場合は章情報を含める
            if chapter_title and chapter_title != "不明":
                citation_info.append(f"{superscript} {chapter_title}（約{position}%の位置）")
            else:
                citation_info.append(f"{superscript} 約{position}%の位置")

        # コンテンツと引用情報を結合
        formatted_content = "\n\n".join(content_parts)
        citations = "\n".join(citation_info)

        result = f"{formatted_content}\n\n【引用位置情報】\n{citations}"
        logger.info(f"Formatted content length: {len(result)} characters")
        logger.debug(f"Citation info: {citations}")

        return result
