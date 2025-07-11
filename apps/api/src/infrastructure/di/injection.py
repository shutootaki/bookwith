from fastapi import Depends
from sqlalchemy.orm import Session

from src.config.db import get_db
from src.domain.annotation.repositories.annotation_repository import AnnotationRepository
from src.domain.book.repositories.book_repository import BookRepository
from src.domain.chat.repositories.chat_repository import ChatRepository
from src.domain.message.repositories.message_repository import MessageRepository
from src.domain.podcast.repositories.podcast_repository import PodcastRepository
from src.infrastructure.external.cloud_tts.tts_client import CloudTTSClient
from src.infrastructure.external.gcs import GCSClient
from src.infrastructure.external.gemini import GeminiClient
from src.infrastructure.memory.memory_service import MemoryService
from src.infrastructure.postgres.annotation.annotation_repository import AnnotationRepositoryImpl
from src.infrastructure.postgres.book.book_repository import BookRepositoryImpl
from src.infrastructure.postgres.chat.chat_repository import ChatRepositoryImpl
from src.infrastructure.postgres.message.message_repository import MessageRepositoryImpl
from src.infrastructure.postgres.podcast import PodcastRepositoryImpl
from src.usecase.annotation.update_annotation_use_case import SyncAnnotationsUseCase, SyncAnnotationsUseCaseImpl
from src.usecase.book.create_book_usecase import (
    CreateBookUseCase,
    CreateBookUseCaseImpl,
)
from src.usecase.book.create_book_vector_index_usecase import (
    CreateBookVectorIndexUseCase,
    CreateBookVectorIndexUseCaseImpl,
)
from src.usecase.book.delete_book_usecase import (
    BulkDeleteBooksUseCase,
    BulkDeleteBooksUseCaseImpl,
    DeleteBookUseCase,
    DeleteBookUseCaseImpl,
)
from src.usecase.book.find_book_by_id_usecase import (
    FindBookByIdUseCase,
    FindBookByIdUseCaseImpl,
)
from src.usecase.book.find_books_usecase import (
    FindBooksByUserIdUseCase,
    FindBooksByUserIdUseCaseImpl,
    FindBooksUseCase,
    FindBooksUseCaseImpl,
)
from src.usecase.book.update_book_usecase import (
    UpdateBookUseCase,
    UpdateBookUseCaseImpl,
)
from src.usecase.chat.create_chat_usecase import (
    CreateChatUseCase,
    CreateChatUseCaseImpl,
)
from src.usecase.chat.delete_chat_usecase import (
    DeleteChatUseCase,
    DeleteChatUseCaseImpl,
)
from src.usecase.chat.find_chat_by_id_usecase import (
    FindChatByIdUseCase,
    FindChatByIdUseCaseImpl,
)
from src.usecase.chat.find_chats_by_user_id_and_book_id_usecase import (
    FindChatsByUserIdAndBookIdUseCase,
    FindChatsByUserIdAndBookIdUseCaseImpl,
)
from src.usecase.chat.find_chats_by_user_id_usecase import (
    FindChatsByUserIdUseCase,
    FindChatsByUserIdUseCaseImpl,
)
from src.usecase.chat.update_chat_title_usecase import (
    UpdateChatTitleUseCase,
    UpdateChatTitleUseCaseImpl,
)
from src.usecase.message.create_message_usecase import (
    CreateMessageUseCase,
    CreateMessageUseCaseImpl,
)
from src.usecase.message.delete_message_usecase import (
    DeleteMessageUseCase,
    DeleteMessageUseCaseImpl,
)
from src.usecase.message.find_message_by_id_usecase import (
    FindMessageByIdUseCase,
    FindMessageByIdUseCaseImpl,
)
from src.usecase.message.find_messages_usecase import (
    FindMessagesUseCase,
    FindMessagesUseCaseImpl,
)
from src.usecase.podcast.create_podcast_usecase import CreatePodcastUseCase
from src.usecase.podcast.find_podcast_by_id_usecase import FindPodcastByIdUseCase
from src.usecase.podcast.find_podcasts_by_book_id_usecase import FindPodcastsByBookIdUseCase
from src.usecase.podcast.generate_podcast_usecase import GeneratePodcastUseCase
from src.usecase.podcast.get_podcast_status_usecase import GetPodcastStatusUseCase

# ==============================================================================
# Book
# ==============================================================================


def get_book_repository(db: Session = Depends(get_db)) -> BookRepository:
    return BookRepositoryImpl(session=db, memory_service=MemoryService())


def get_create_book_usecase(
    book_repository: BookRepositoryImpl = Depends(get_book_repository),
) -> CreateBookUseCase:
    return CreateBookUseCaseImpl(book_repository)


def get_find_books_usecase(
    book_repository: BookRepositoryImpl = Depends(get_book_repository),
) -> FindBooksUseCase:
    return FindBooksUseCaseImpl(book_repository)


def get_find_books_by_user_id_usecase(
    book_repository: BookRepository = Depends(get_book_repository),
) -> FindBooksByUserIdUseCase:
    return FindBooksByUserIdUseCaseImpl(book_repository)


def get_find_book_by_id_usecase(
    book_repository: BookRepository = Depends(get_book_repository),
) -> FindBookByIdUseCase:
    return FindBookByIdUseCaseImpl(book_repository)


def get_update_book_usecase(
    book_repository: BookRepository = Depends(get_book_repository),
) -> UpdateBookUseCase:
    return UpdateBookUseCaseImpl(book_repository)


def get_delete_book_usecase(
    book_repository: BookRepository = Depends(get_book_repository),
) -> DeleteBookUseCase:
    return DeleteBookUseCaseImpl(book_repository, memory_service=MemoryService())


def get_bulk_delete_books_usecase(
    book_repository: BookRepository = Depends(get_book_repository),
) -> BulkDeleteBooksUseCase:
    return BulkDeleteBooksUseCaseImpl(book_repository, memory_service=MemoryService())


# ==============================================================================
# Vector Index (Related to Book)
# ==============================================================================


def get_create_book_vector_index_usecase() -> CreateBookVectorIndexUseCase:
    return CreateBookVectorIndexUseCaseImpl()


# ==============================================================================
# Chat
# ==============================================================================


def get_chat_repository(db: Session = Depends(get_db)) -> ChatRepository:
    return ChatRepositoryImpl(db)


def get_create_chat_usecase(
    chat_repository: ChatRepository = Depends(get_chat_repository),
) -> CreateChatUseCase:
    return CreateChatUseCaseImpl(chat_repository)


def get_find_chat_by_id_usecase(
    chat_repository: ChatRepository = Depends(get_chat_repository),
) -> FindChatByIdUseCase:
    return FindChatByIdUseCaseImpl(chat_repository)


def get_find_chats_by_user_id_usecase(
    chat_repository: ChatRepository = Depends(get_chat_repository),
) -> FindChatsByUserIdUseCase:
    return FindChatsByUserIdUseCaseImpl(chat_repository)


def get_find_chats_by_user_id_and_book_id_usecase(
    chat_repository: ChatRepository = Depends(get_chat_repository),
) -> FindChatsByUserIdAndBookIdUseCase:
    return FindChatsByUserIdAndBookIdUseCaseImpl(chat_repository)


def get_update_chat_title_usecase(
    chat_repository: ChatRepository = Depends(get_chat_repository),
) -> UpdateChatTitleUseCase:
    return UpdateChatTitleUseCaseImpl(chat_repository)


def get_delete_chat_usecase(
    chat_repository: ChatRepository = Depends(get_chat_repository),
) -> DeleteChatUseCase:
    return DeleteChatUseCaseImpl(chat_repository)


# ==============================================================================
# Message
# ==============================================================================


def get_message_repository(db: Session = Depends(get_db)) -> MessageRepository:
    return MessageRepositoryImpl(db)


def get_find_messages_usecase(
    message_repository: MessageRepository = Depends(get_message_repository),
) -> FindMessagesUseCase:
    return FindMessagesUseCaseImpl(message_repository)


def get_find_message_by_id_usecase(
    message_repository: MessageRepository = Depends(get_message_repository),
) -> FindMessageByIdUseCase:
    return FindMessageByIdUseCaseImpl(message_repository)


def get_create_message_usecase(
    message_repository: MessageRepository = Depends(get_message_repository),
    chat_repository: ChatRepository = Depends(get_chat_repository),
) -> CreateMessageUseCase:
    return CreateMessageUseCaseImpl(
        message_repository=message_repository,
        chat_repository=chat_repository,
        memory_service=MemoryService(),
    )


def get_delete_message_usecase(
    message_repository: MessageRepository = Depends(get_message_repository),
) -> DeleteMessageUseCase:
    return DeleteMessageUseCaseImpl(message_repository)


# ==============================================================================
# Annotation
# ==============================================================================


def get_annotation_repository(db: Session = Depends(get_db)) -> AnnotationRepository:
    return AnnotationRepositoryImpl(session=db, memory_service=MemoryService())


def get_sync_annotations_usecase(
    annotation_repository: AnnotationRepository = Depends(get_annotation_repository),
    book_repository: BookRepository = Depends(get_book_repository),
) -> SyncAnnotationsUseCase:
    return SyncAnnotationsUseCaseImpl(
        annotation_repository=annotation_repository,
        book_repository=book_repository,
    )


# ==============================================================================
# Podcast
# ==============================================================================


def get_podcast_repository(db: Session = Depends(get_db)) -> PodcastRepository:
    return PodcastRepositoryImpl(session=db)


def get_gemini_client() -> GeminiClient:
    return GeminiClient()


def get_cloud_tts_client() -> CloudTTSClient:
    return CloudTTSClient()


def get_gcs_client() -> GCSClient:
    return GCSClient()


async def get_create_podcast_usecase(
    podcast_repository: PodcastRepository = Depends(get_podcast_repository),
) -> CreatePodcastUseCase:
    return CreatePodcastUseCase(podcast_repository)


async def get_find_podcast_by_id_usecase(
    podcast_repository: PodcastRepository = Depends(get_podcast_repository),
) -> FindPodcastByIdUseCase:
    return FindPodcastByIdUseCase(podcast_repository)


async def get_find_podcasts_by_book_id_usecase(
    podcast_repository: PodcastRepository = Depends(get_podcast_repository),
) -> FindPodcastsByBookIdUseCase:
    return FindPodcastsByBookIdUseCase(podcast_repository)


async def get_podcast_status_usecase(
    podcast_repository: PodcastRepository = Depends(get_podcast_repository),
) -> GetPodcastStatusUseCase:
    return GetPodcastStatusUseCase(podcast_repository)


async def get_generate_podcast_usecase(
    podcast_repository: PodcastRepository = Depends(get_podcast_repository),
    book_repository: BookRepository = Depends(get_book_repository),
    gemini_client: GeminiClient = Depends(get_gemini_client),
    tts_client: CloudTTSClient = Depends(get_cloud_tts_client),
    gcs_client: GCSClient = Depends(get_gcs_client),
) -> GeneratePodcastUseCase:
    return GeneratePodcastUseCase(
        podcast_repository=podcast_repository,
        book_repository=book_repository,
        gemini_client=gemini_client,
        tts_client=tts_client,
        gcs_client=gcs_client,
    )
