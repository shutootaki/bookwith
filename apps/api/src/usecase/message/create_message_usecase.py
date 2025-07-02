from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from weaviate.classes.query import Filter

from src.domain.chat.entities.chat import Chat
from src.domain.chat.value_objects.book_id import BookId
from src.domain.chat.value_objects.chat_title import ChatTitle
from src.infrastructure.memory.memory_service import MemoryService
from src.infrastructure.memory.memory_vector_store import MemoryVectorStore
from src.infrastructure.vector import get_book_content_vector_store

if TYPE_CHECKING:
    from langchain_core.runnables import RunnableSerializable


from abc import ABC, abstractmethod

from src.domain.chat.repositories.chat_repository import ChatRepository
from src.domain.chat.value_objects.chat_id import ChatId
from src.domain.chat.value_objects.user_id import UserId
from src.domain.message.entities.message import Message
from src.domain.message.repositories.message_repository import MessageRepository
from src.domain.message.value_objects.message_content import MessageContent
from src.domain.message.value_objects.sender_type import SenderType


class CreateMessageUseCase(ABC):
    @abstractmethod
    async def execute(
        self,
        content: str,
        sender_id: str,
        chat_id: str,
        book_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """ユーザーメッセージを保存し、AIの応答をストリーミングで返す."""


class CreateMessageUseCaseImpl(CreateMessageUseCase):
    def __init__(
        self,
        message_repository: MessageRepository,
        chat_repository: ChatRepository,
        memory_service: MemoryService,
    ) -> None:
        self.message_repository = message_repository
        self.chat_repository = chat_repository
        self.memory_service = memory_service

    async def execute(
        self,
        content: str,
        sender_id: str,
        chat_id: str,
        book_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """ユーザーメッセージを保存し、AIの応答をストリーミングで返す."""
        chat_id_obj = ChatId(chat_id)
        chat = self.chat_repository.find_by_id(chat_id_obj)

        if chat is None:
            chat_title = self._get_chat_title(content)
            new_chat = Chat(id=chat_id_obj, user_id=UserId(sender_id), title=ChatTitle(chat_title), book_id=BookId(book_id) if book_id else None)
            self.chat_repository.save(new_chat)

        meta = metadata or {}

        user_message = Message.create(
            content=MessageContent(content),
            sender_id=sender_id,
            sender_type=SenderType.user(),
            chat_id=chat_id,
            metadata=meta,
        )
        self.message_repository.save(user_message)

        # メッセージをベクトル化（同期処理）
        # note: メッセージをベクトル化する必要があるのか？
        self.memory_service.vectorize_message(user_message)

        # チャットのメッセージ数を取得
        # todo: 全件取得によるパフォーマンスの影響を考慮する
        message_count = self.message_repository.count_by_chat_id(chat_id)

        # 必要に応じて要約を実行（同期処理）
        self.memory_service.summarize_chat(
            chat_id=chat_id,
            user_id=sender_id,
            message_count=message_count,
        )

        # 新しい順（降順）で必要な分だけ取得し、古い順（昇順）に並べ直す
        latest_messages = self.message_repository.find_latest_by_chat_id(chat_id, limit=self.memory_service.config.memory_buffer_size)

        # 記憶を考慮したプロンプトを構築
        memory_prompt = self.memory_service.build_memory_prompt(
            buffer=sorted(latest_messages, key=lambda msg: msg.created_at), user_query=content, user_id=sender_id, chat_id=chat_id
        )

        ai_response_chunks = []
        async for chunk in self._stream_ai_response(question=memory_prompt, user_id=sender_id, book_id=book_id):
            ai_response_chunks.append(chunk)
            yield chunk

        full_ai_response = "".join(ai_response_chunks)

        ai_message = Message.create(
            content=MessageContent(full_ai_response),
            sender_id=sender_id,
            sender_type=SenderType.assistant(),
            chat_id=chat_id,
            metadata=meta,
        )
        self.message_repository.save(ai_message)

        # AIのレスポンスもベクトル化（同期処理）
        self.memory_service.vectorize_message(ai_message)

    async def _stream_memory_based_response(self, prompt: str) -> AsyncGenerator[str]:
        """記憶ベースのレスポンスをストリーミングで返す."""
        model = ChatOpenAI(model_name="gpt-4o", streaming=True)
        async for chunk in (model | StrOutputParser()).astream(prompt):
            yield chunk

    async def _stream_ai_response(
        self,
        question: str,
        user_id: str,
        book_id: str | None = None,
    ) -> AsyncGenerator[str]:
        """LLMの応答をストリーミングで返す.

        tenant_idがNoneの場合は記憶情報のみを使用し、
        tenant_idがある場合は記憶情報とBookの知識ベースを組み合わせて応答を生成する。
        """

        def _format_documents_as_string(documents: list[Document]) -> str:
            return "\n\n".join(doc.page_content for doc in documents)

        model = ChatOpenAI(model_name="gpt-4o", streaming=True)

        # tenant_idがない場合は記憶ベースの応答のみを返す
        if book_id is None:
            basic_chain: RunnableSerializable[Any, str] = RunnablePassthrough() | model | StrOutputParser()
            async for chunk in basic_chain.astream(question):
                yield chunk
            return

        # tenant_idがある場合は記憶ベースとRAGベースを組み合わせる
        vector_store = get_book_content_vector_store()
        vector_store_retriever = vector_store.as_retriever(
            search_kwargs={"k": 4, "tenant": user_id, "filters": Filter.by_property("book_id").equal(book_id)}
        )

        highlight_texts = []
        if user_id and book_id:
            memory_vector_store = MemoryVectorStore()
            query_vector = memory_vector_store.encode_text(question)
            highlights = memory_vector_store.search_highlights(user_id=user_id, book_id=book_id, query_vector=query_vector, limit=3)
            if highlights:
                for h in highlights:
                    highlight_text = h["content"]
                    if h.get("notes"):
                        highlight_text += f"\n{h['notes']}"
                    highlight_texts.append(f"【ハイライト】{highlight_text}")
            else:
                highlight_texts = ["No highlights found"]

        hybrid_chain: RunnableSerializable[Any, str] = (
            {
                "book_content": vector_store_retriever | (lambda docs: _format_documents_as_string(docs)),
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

    def _get_chat_title(self, question: str) -> str:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are the chat title generation AI.
Based on the user's initial question, generate a concise and precise chat title.
The title should be no longer than 30 characters.
It should be in a format that summaries the content of the question.""",
                ),
                ("human", "{question}"),
            ]
        )

        return (prompt | ChatOpenAI(name="gpt-4o") | StrOutputParser()).invoke({"question": question})
