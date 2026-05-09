import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status

from src.domain.book.exceptions.book_exceptions import BookNotFoundException, BookPermissionDeniedException
from src.domain.book.value_objects.book_id import BookId
from src.domain.chat.value_objects.user_id import UserId
from src.domain.podcast.exceptions.podcast_exceptions import (
    PodcastAlreadyExistsError,
    PodcastNotFoundError,
    PodcastPermissionDeniedError,
)
from src.domain.podcast.value_objects.podcast_id import PodcastId
from src.domain.podcast.value_objects.podcast_status import PodcastStatus, PodcastStatusEnum
from src.infrastructure.di.injection import (
    get_create_podcast_usecase,
    get_find_podcast_by_id_usecase,
    get_find_podcasts_by_book_id_usecase,
    get_generate_podcast_usecase,
    get_podcast_repository,
    get_podcast_status_usecase,
)
from src.presentation.api.auth import require_user_id
from src.presentation.api.middleware import expensive_limit
from src.presentation.api.schemas.podcast_schema import (
    CreatePodcastRequest,
    CreatePodcastResponse,
    PodcastListResponse,
    PodcastResponse,
    PodcastStatusResponse,
)
from src.usecase.podcast.create_podcast_usecase import CreatePodcastUseCase
from src.usecase.podcast.find_podcast_by_id_usecase import FindPodcastByIdUseCase
from src.usecase.podcast.find_podcasts_by_book_id_usecase import FindPodcastsByBookIdUseCase
from src.usecase.podcast.generate_podcast_usecase import GeneratePodcastUseCase
from src.usecase.podcast.get_podcast_status_usecase import GetPodcastStatusUseCase

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=CreatePodcastResponse)
@expensive_limit()
async def create_podcast(
    request: Request,
    body: CreatePodcastRequest,
    background_tasks: BackgroundTasks,
    user_id_str: str = Depends(require_user_id),
    create_usecase: CreatePodcastUseCase = Depends(get_create_podcast_usecase),
    generate_usecase: GeneratePodcastUseCase = Depends(get_generate_podcast_usecase),
):
    """Create a new podcast for a book"""
    try:
        # CR-4: 認証 user_id を強制使用。
        book_id = BookId(body.book_id)
        user_id = UserId(user_id_str)

        title = body.title or f"Podcast for book {body.book_id}"

        podcast_id = await create_usecase.execute(book_id, user_id, title, body.language)

        background_tasks.add_task(generate_usecase.execute, podcast_id)

        return CreatePodcastResponse(id=podcast_id.value, status=PodcastStatusEnum.PENDING, message="Podcast creation started. Generation is in progress.")

    except BookPermissionDeniedException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden") from e
    except BookNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found") from e
    except PodcastAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Podcast already exists for this book") from e
    except Exception:
        logger.exception("Error creating podcast")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create podcast")


@router.get("/book/{book_id}", response_model=PodcastListResponse)
async def get_podcasts_by_book(
    book_id: str,
    user_id_str: str = Depends(require_user_id),
    find_usecase: FindPodcastsByBookIdUseCase = Depends(get_find_podcasts_by_book_id_usecase),
):
    """Get all podcasts for a specific book owned by the authenticated user."""
    try:
        book_domain_id = BookId(book_id)
        podcasts = await find_usecase.execute(book_domain_id, UserId(user_id_str))

        # PodcastResponse は from_attributes=True なので JSON 経由の round-trip は不要。
        podcast_responses = [PodcastResponse.model_validate(p) for p in podcasts]
        return PodcastListResponse(podcasts=podcast_responses, total=len(podcast_responses))

    except BookPermissionDeniedException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden") from e
    except BookNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found") from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid book ID format") from e
    except Exception:
        logger.exception(f"Error getting podcasts for book {book_id}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve podcasts")


@router.get("/{podcast_id}", response_model=PodcastResponse)
async def get_podcast(
    podcast_id: str,
    user_id_str: str = Depends(require_user_id),
    find_usecase: FindPodcastByIdUseCase = Depends(get_find_podcast_by_id_usecase),
):
    """Get podcast details by ID"""
    try:
        podcast_domain_id = PodcastId(podcast_id)
        podcast = await find_usecase.execute(podcast_domain_id, UserId(user_id_str))

        return PodcastResponse.model_validate(podcast)

    except PodcastPermissionDeniedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    except PodcastNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Podcast not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid podcast ID format") from e
    except Exception:
        logger.exception(f"Error getting podcast {podcast_id}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve podcast")


@router.get("/{podcast_id}/status", response_model=PodcastStatusResponse)
async def get_podcast_status(
    podcast_id: str,
    user_id_str: str = Depends(require_user_id),
    status_usecase: GetPodcastStatusUseCase = Depends(get_podcast_status_usecase),
):
    """Get podcast generation status"""
    try:
        podcast_domain_id = PodcastId(podcast_id)
        status_info = await status_usecase.execute(podcast_domain_id, UserId(user_id_str))

        return PodcastStatusResponse(**status_info)

    except PodcastPermissionDeniedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    except PodcastNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Podcast not found") from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid podcast ID format") from e
    except Exception:
        logger.exception(f"Error getting podcast status {podcast_id}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get podcast status")


@router.post("/{podcast_id}/retry", response_model=CreatePodcastResponse)
async def retry_podcast(
    podcast_id: str,
    background_tasks: BackgroundTasks,
    user_id_str: str = Depends(require_user_id),
    find_usecase: FindPodcastByIdUseCase = Depends(get_find_podcast_by_id_usecase),
    generate_usecase: GeneratePodcastUseCase = Depends(get_generate_podcast_usecase),
    podcast_repository=Depends(get_podcast_repository),
):
    """Retry failed podcast generation (with ownership verification + optimistic lock)."""
    try:
        podcast_domain_id = PodcastId(podcast_id)
        # CR-3: 認証ユーザーが所有しているか先に検証。
        podcast = await find_usecase.execute(podcast_domain_id, UserId(user_id_str))

        if not podcast.is_failed():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Podcast cannot be retried. Current status: {podcast.status}")

        # M-1: 楽観的ロック付き更新。並行リトライによる二重課金を回避。
        # L-13: 前回失敗時の error_message を NULL に戻す（空文字だと UI が「エラー有り」と誤検知する）。
        updated = await podcast_repository.update_status_with_optimistic_lock(
            podcast_domain_id,
            expected_status=PodcastStatus.failed(),
            new_status=PodcastStatus.pending(),
            clear_error_message=True,
        )
        if not updated:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Podcast retry conflict")

        background_tasks.add_task(generate_usecase.execute, podcast_domain_id)

        return CreatePodcastResponse(id=podcast_domain_id.value, status=PodcastStatusEnum.PENDING, message="Podcast retry started. Generation is in progress.")

    except PodcastPermissionDeniedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    except PodcastNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Podcast not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid podcast ID format") from e
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Error retrying podcast {podcast_id}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retry podcast")
