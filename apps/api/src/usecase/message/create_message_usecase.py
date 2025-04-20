from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from src.domain.chat.entities.chat import Chat
from src.domain.chat.value_objects.book_id import BookId
from src.domain.chat.value_objects.chat_title import ChatTitle
from src.infrastructure.prompts import rag_prompt
from src.infrastructure.vector import get_vector_store

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
        tenant_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AsyncGenerator[str]:
        """ユーザーメッセージを保存し、AIの応答をストリーミングで返す."""


class CreateMessageUseCaseImpl(CreateMessageUseCase):
    def __init__(
        self,
        message_repository: MessageRepository,
        chat_repository: ChatRepository,
    ) -> None:
        self.message_repository = message_repository
        self.chat_repository = chat_repository

    async def execute(
        self,
        content: str,
        sender_id: str,
        chat_id: str,
        book_id: str | None = None,
        tenant_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AsyncGenerator[str]:
        """ユーザーメッセージを保存し、AIの応答をストリーミングで返す."""
        chat_id_obj = ChatId(chat_id)
        chat = self.chat_repository.find_by_id(chat_id_obj)

        if chat is None:
            # TODO: タイトル生成を非同期にするか検討
            chat_title = self._get_chat_title(content)
            new_chat = Chat(id=chat_id_obj, user_id=UserId(sender_id), title=ChatTitle(chat_title), book_id=BookId(book_id) if book_id else None)
            self.chat_repository.save(new_chat)

        message_content = MessageContent(content)
        meta = metadata or {}

        user_message = Message.create(
            content=message_content,
            sender_id=sender_id,
            sender_type=SenderType.user(),
            chat_id=chat_id,
            metadata=meta,
        )
        self.message_repository.save(user_message)

        ai_response_chunks = []
        async for chunk in self._stream_ai_response(content, tenant_id):
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

    async def _stream_ai_response(self, question: str, tenant_id: str | None = None) -> AsyncGenerator[str]:
        def _format_documents_as_string(documents: list[Document]) -> str:
            return "\n\n".join(doc.page_content for doc in documents)

        model = ChatOpenAI(model_name="gpt-4o-mini", streaming=True)

        vector_store = get_vector_store("BookContentIndex")
        if tenant_id is None:
            basic_chain: RunnableSerializable[Any, str] = RunnablePassthrough() | model | StrOutputParser()
            async for chunk in basic_chain.astream(question):
                yield chunk

        vector_store_retriever = vector_store.as_retriever(
            search_kwargs={
                "k": 4,
                "tenant": tenant_id,
            }
        )

        rag_chain: RunnableSerializable[Any, str] = (
            {
                "context": vector_store_retriever | _format_documents_as_string,
                "question": RunnablePassthrough(),
            }
            | rag_prompt
            | model
            | StrOutputParser()
        )

        async for chunk in rag_chain.astream(question):
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

        return (prompt | ChatOpenAI(name="gpt-4o-mini") | StrOutputParser()).invoke({"question": question})
