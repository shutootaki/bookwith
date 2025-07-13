import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from src.config.app_config import TEST_USER_ID
from src.domain.book.value_objects.book_id import BookId
from src.domain.chat.value_objects.user_id import UserId
from src.domain.podcast.exceptions.podcast_exceptions import PodcastAlreadyExistsError, PodcastNotFoundError
from src.domain.podcast.repositories.podcast_repository import PodcastRepository
from src.domain.podcast.value_objects.podcast_id import PodcastId
from src.domain.podcast.value_objects.podcast_status import PodcastStatus
from src.infrastructure.di.injection import (
    get_create_podcast_usecase,
    get_find_podcast_by_id_usecase,
    get_find_podcasts_by_book_id_usecase,
    get_generate_podcast_usecase,
    get_podcast_repository,
    get_podcast_status_usecase,
)
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
async def create_podcast(
    request: CreatePodcastRequest,
    background_tasks: BackgroundTasks,
    create_usecase: CreatePodcastUseCase = Depends(get_create_podcast_usecase),
    generate_usecase: GeneratePodcastUseCase = Depends(get_generate_podcast_usecase),
):
    """Create a new podcast for a book"""
    try:
        book_id = BookId(request.book_id)
        user_id = UserId(TEST_USER_ID)

        # Generate title if not provided
        title = request.title or f"Podcast for book {request.book_id}"

        # Create podcast
        podcast_id = await create_usecase.execute(book_id, user_id, title, request.language)

        # Start background generation
        background_tasks.add_task(generate_usecase.execute, podcast_id)

        return CreatePodcastResponse(id=podcast_id.value, status="PENDING", message="Podcast creation started. Generation is in progress.")

    except PodcastAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Podcast already exists for this book") from e
    except Exception as e:
        logger.error(f"Error creating podcast: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create podcast") from e


@router.get("/{podcast_id}", response_model=PodcastResponse)
async def get_podcast(
    podcast_id: str,
    find_usecase: FindPodcastByIdUseCase = Depends(get_find_podcast_by_id_usecase),
):
    """Get podcast details by ID"""
    try:
        # Usecase is injected via Depends
        # Find podcast
        podcast_domain_id = PodcastId(podcast_id)
        podcast = await find_usecase.execute(podcast_domain_id)

        if not podcast:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Podcast not found")

        # converterを使わず直接Pydanticモデルで返す
        return PodcastResponse.model_validate(podcast.model_dump(mode="json"))

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid podcast ID format") from e
    except Exception as e:
        logger.error(f"Error getting podcast {podcast_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve podcast") from e


@router.get("/book/{book_id}", response_model=PodcastListResponse)
async def get_podcasts_by_book(
    book_id: str,
    find_usecase: FindPodcastsByBookIdUseCase = Depends(get_find_podcasts_by_book_id_usecase),
):
    """Get all podcasts for a specific book"""
    try:
        # Usecase is injected via Depends
        # Find podcasts
        book_domain_id = BookId(book_id)
        podcasts = await find_usecase.execute(book_domain_id)

        # converterを使わず直接Pydanticモデルで返す
        podcast_responses = [PodcastResponse.model_validate(p.model_dump(mode="json")) for p in podcasts]
        return PodcastListResponse(podcasts=podcast_responses, total=len(podcast_responses))

    except Exception as e:
        logger.error(f"Error getting podcasts for book {book_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve podcasts") from e


@router.get("/{podcast_id}/status", response_model=PodcastStatusResponse)
async def get_podcast_status(
    podcast_id: str,
    status_usecase: GetPodcastStatusUseCase = Depends(get_podcast_status_usecase),
):
    """Get podcast generation status"""
    try:
        # Usecase is injected via Depends
        # Get status
        podcast_domain_id = PodcastId(podcast_id)
        status_info = await status_usecase.execute(podcast_domain_id)

        return PodcastStatusResponse(
            id=status_info["id"],
            status=status_info["status"],
            title=status_info["title"],
            language=status_info["language"],
            audio_url=status_info.get("audio_url"),
            error_message=status_info.get("error_message"),
            has_script=status_info["has_script"],
            script_turn_count=status_info.get("script_turn_count"),
            script_character_count=status_info.get("script_character_count"),
            created_at=status_info["created_at"],
            updated_at=status_info["updated_at"],
        )

    except PodcastNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Podcast not found") from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid podcast ID format") from e
    except Exception as e:
        logger.error(f"Error getting podcast status {podcast_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get podcast status") from e


@router.post("/{podcast_id}/retry", response_model=CreatePodcastResponse)
async def retry_podcast(
    podcast_id: str,
    background_tasks: BackgroundTasks,
    find_usecase: FindPodcastByIdUseCase = Depends(get_find_podcast_by_id_usecase),
    generate_usecase: GeneratePodcastUseCase = Depends(get_generate_podcast_usecase),
    podcast_repository: PodcastRepository = Depends(get_podcast_repository),
):
    """Retry failed podcast generation"""
    try:
        podcast_domain_id = PodcastId(podcast_id)
        podcast = await find_usecase.execute(podcast_domain_id)

        if not podcast:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Podcast not found")

        if not podcast.is_failed():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Podcast cannot be retried. Current status: {podcast.status}")

        podcast.update_status(PodcastStatus.pending(), error_message="")
        await podcast_repository.update(podcast)
        background_tasks.add_task(generate_usecase.execute, podcast_domain_id)

        return CreatePodcastResponse(id=podcast_domain_id.value, status="PENDING", message="Podcast retry started. Generation is in progress.")

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid podcast ID format") from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying podcast {podcast_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retry podcast") from e
