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
    def execute(
        self,
        content: str,
        sender_id: str,
        chat_id: str,
        book_id: str | None = None,
        tenant_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[Message, Message]:
        """新しいMessageを作成して返す."""


class CreateMessageUseCaseImpl(CreateMessageUseCase):
    def __init__(
        self,
        message_repository: MessageRepository,
        chat_repository: ChatRepository,
    ) -> None:
        self.message_repository = message_repository
        self.chat_repository = chat_repository

    def execute(
        self,
        content: str,
        sender_id: str,
        chat_id: str,
        book_id: str | None = None,
        tenant_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[Message, Message]:
        """新しいMessageを作成して保存し、ユーザーとAIのMessageエンティティのタプルを返す."""
        chat_id_obj = ChatId(chat_id)
        chat = self.chat_repository.find_by_id(chat_id_obj)

        if chat is None:
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

        ai_response = self._process_question(content, tenant_id)
        ai_content = MessageContent(ai_response)

        ai_message = Message.create(
            content=ai_content,
            sender_id=sender_id,
            sender_type=SenderType.assistant(),
            chat_id=chat_id,
            metadata=meta,
        )
        self.message_repository.save(ai_message)

        return user_message, ai_message

    def _process_question(self, question: str, tenant_id: str | None = None) -> str:
        def _format_documents_as_string(documents: list[Document]) -> str:
            return "\n\n".join(doc.page_content for doc in documents)

        model = ChatOpenAI(name="gpt-4o-mini")

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

        chain: RunnableSerializable[Any, str] = (
            {
                "context": vector_store_retriever | _format_documents_as_string,
                "question": RunnablePassthrough(),
            }
            | rag_prompt
            | model
            | StrOutputParser()
        )

        return chain.invoke(question)

    def _get_chat_title(self, question: str) -> str:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are the chat title generation AI.
Based on the user's initial question, generate a concise and precise chat title.
The title should be no longer than 30 characters.
It should be in a format that summarises the content of the question.""",
                ),
                ("human", "{question}"),
            ]
        )

        return (prompt | ChatOpenAI(name="gpt-4o-mini") | StrOutputParser()).invoke({"question": question})
