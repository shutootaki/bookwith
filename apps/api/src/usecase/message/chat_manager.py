"""チャット管理サービス."""

from textwrap import dedent

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.domain.chat.entities.chat import Chat
from src.domain.chat.repositories.chat_repository import ChatRepository
from src.domain.chat.value_objects.book_id import BookId
from src.domain.chat.value_objects.chat_id import ChatId
from src.domain.chat.value_objects.chat_title import ChatTitle
from src.domain.chat.value_objects.user_id import UserId


class ChatManager:
    """チャットの作成と管理を行うサービス."""

    def __init__(self, chat_repository: ChatRepository) -> None:
        """チャット管理サービスの初期化."""
        self.chat_repository = chat_repository

    def ensure_chat_exists(self, chat_id: str, sender_id: str, book_id: str | None, content: str) -> None:
        """チャットが存在することを確認し、存在しない場合は作成する."""
        chat_id_obj = ChatId(chat_id)
        chat = self.chat_repository.find_by_id(chat_id_obj)

        if chat is None:
            chat_title = self._generate_chat_title(content)
            new_chat = Chat(id=chat_id_obj, user_id=UserId(sender_id), title=ChatTitle(chat_title), book_id=BookId(book_id) if book_id else None)
            self.chat_repository.save(new_chat)

    def _generate_chat_title(self, question: str) -> str:
        """初回質問からチャットタイトルを生成する."""
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    dedent(
                        """\
                        You are the chat title generation AI.
                        Based on the user's initial question, generate a concise and precise chat title.
                        It should be in a format that summarizes the content of the question.

                        Rules:
                        - Generate titles only, without prefixes or suffixes.
                        - Titles should be in the same language as the user entered.
                        - Titles should be 30 characters or less and concise.
                        """
                    ),
                ),
                ("human", "{question}"),
            ]
        )

        return (prompt | ChatOpenAI(name="gpt-4o") | StrOutputParser()).invoke({"question": question})
