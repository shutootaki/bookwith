from datetime import UTC, datetime

from sqlalchemy import update
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from src.domain.book.value_objects.book_id import BookId
from src.domain.chat.value_objects.user_id import UserId
from src.domain.podcast.entities.podcast import Podcast
from src.domain.podcast.exceptions.podcast_exceptions import PodcastNotFoundError
from src.domain.podcast.repositories.podcast_repository import PodcastRepository
from src.domain.podcast.value_objects.podcast_id import PodcastId
from src.domain.podcast.value_objects.podcast_status import PodcastStatus
from src.infrastructure.postgres.podcast.podcast_dto import PodcastDTO


class PodcastRepositoryImpl(PodcastRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    async def save(self, podcast: Podcast) -> Podcast:
        """Save a podcast entity"""
        dto = PodcastDTO.from_entity(podcast)
        try:
            self._session.add(dto)
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise
        return dto.to_entity()

    async def find_by_id(self, podcast_id: PodcastId) -> Podcast | None:
        """Find a podcast by its ID"""
        stmt = select(PodcastDTO).where(PodcastDTO.id == podcast_id.value)
        result = self._session.execute(stmt)
        dto = result.scalar_one_or_none()
        return dto.to_entity() if dto else None

    async def find_by_id_for_user(self, podcast_id: PodcastId, user_id: UserId) -> Podcast | None:
        # CR-3: user_id を WHERE 句に必ず含める。
        stmt = select(PodcastDTO).where((PodcastDTO.id == podcast_id.value) & (PodcastDTO.user_id == user_id.value))
        result = self._session.execute(stmt)
        dto = result.scalar_one_or_none()
        return dto.to_entity() if dto else None

    async def find_by_book_id(self, book_id: BookId) -> list[Podcast]:
        """Find all podcasts for a specific book"""
        stmt = select(PodcastDTO).where(PodcastDTO.book_id == book_id.value).order_by(PodcastDTO.created_at.desc())
        result = self._session.execute(stmt)
        dtos = result.scalars().all()
        return [dto.to_entity() for dto in dtos]

    async def find_by_book_id_for_user(self, book_id: BookId, user_id: UserId) -> list[Podcast]:
        stmt = (
            select(PodcastDTO)
            .where((PodcastDTO.book_id == book_id.value) & (PodcastDTO.user_id == user_id.value))
            .order_by(PodcastDTO.created_at.desc())
        )
        result = self._session.execute(stmt)
        dtos = result.scalars().all()
        return [dto.to_entity() for dto in dtos]

    async def find_by_book_id_and_user_id(self, book_id: BookId, user_id: UserId) -> Podcast | None:
        """Find a podcast by book ID and user ID"""
        stmt = select(PodcastDTO).where((PodcastDTO.book_id == book_id.value) & (PodcastDTO.user_id == user_id.value))
        result = self._session.execute(stmt)
        dto = result.scalar_one_or_none()
        return dto.to_entity() if dto else None

    async def update(self, podcast: Podcast) -> Podcast:
        """Update an existing podcast"""
        existing = await self.find_by_id(podcast.id)
        if not existing:
            raise PodcastNotFoundError(str(podcast.id))

        dto = PodcastDTO.from_entity(podcast)
        try:
            self._session.merge(dto)
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise
        return dto.to_entity()

    async def update_status(
        self,
        podcast_id: PodcastId,
        status: PodcastStatus,
        audio_url: str | None = None,
        error_message: str | None = None,
    ) -> None:
        """Update podcast status and optionally audio_url or error_message"""
        stmt = (
            update(PodcastDTO)
            .where(PodcastDTO.id == podcast_id.value)
            .values(
                status=status.value,
                updated_at=datetime.now(UTC),
            )
        )

        if audio_url is not None:
            stmt = stmt.values(audio_url=audio_url)
        if error_message is not None:
            stmt = stmt.values(error_message=error_message)

        result = self._session.execute(stmt)
        if result.rowcount == 0:
            raise PodcastNotFoundError(str(podcast_id))
        self._session.commit()

    async def update_status_with_optimistic_lock(
        self,
        podcast_id: PodcastId,
        expected_status: PodcastStatus,
        new_status: PodcastStatus,
        audio_url: str | None = None,
        error_message: str | None = None,
        clear_error_message: bool = False,
    ) -> bool:
        # M-1: TOCTOU を避けるため、expected_status での原子更新。
        # L-13: retry 時は `error_message` を NULL に戻したい。空文字を入れると
        # `error_message IS NULL` フィルタや UI の存在判定が誤動作するため、明示的に NULL 化する。
        stmt = (
            update(PodcastDTO)
            .where((PodcastDTO.id == podcast_id.value) & (PodcastDTO.status == expected_status.value))
            .values(
                status=new_status.value,
                updated_at=datetime.now(UTC),
            )
        )
        if audio_url is not None:
            stmt = stmt.values(audio_url=audio_url)
        if clear_error_message:
            stmt = stmt.values(error_message=None)
        elif error_message is not None:
            stmt = stmt.values(error_message=error_message)

        result = self._session.execute(stmt)
        if result.rowcount == 0:
            return False
        self._session.commit()
        return True

    async def delete_for_user(self, podcast_id: PodcastId, user_id: UserId) -> bool:
        stmt = select(PodcastDTO).where((PodcastDTO.id == podcast_id.value) & (PodcastDTO.user_id == user_id.value))
        result = self._session.execute(stmt)
        dto = result.scalar_one_or_none()
        if not dto:
            return False

        try:
            self._session.delete(dto)
            self._session.commit()
            return True
        except Exception:
            self._session.rollback()
            raise

    async def find_by_status(self, status: PodcastStatus) -> list[Podcast]:
        """Find all podcasts with a specific status"""
        stmt = select(PodcastDTO).where(PodcastDTO.status == status.value).order_by(PodcastDTO.created_at.asc())
        result = self._session.execute(stmt)
        dtos = result.scalars().all()
        return [dto.to_entity() for dto in dtos]
