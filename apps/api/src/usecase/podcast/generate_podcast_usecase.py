import logging

from src.domain.book.entities.book import Book
from src.domain.book.repositories.book_repository import BookRepository
from src.domain.podcast.entities.podcast import Podcast
from src.domain.podcast.exceptions.podcast_exceptions import PodcastGenerationError, PodcastNotFoundError
from src.domain.podcast.repositories.podcast_repository import PodcastRepository
from src.domain.podcast.value_objects.podcast_id import PodcastId
from src.domain.podcast.value_objects.podcast_script import PodcastScript
from src.domain.podcast.value_objects.podcast_status import PodcastStatus
from src.infrastructure.external.audio import AudioProcessor
from src.infrastructure.external.cloud_tts.tts_client import CloudTTSClient
from src.infrastructure.external.gcs import GCSBucketError, GCSClient
from src.infrastructure.external.gemini import GeminiClient
from src.usecase.podcast.extract_chapters_usecase import ExtractChaptersUseCase
from src.usecase.podcast.generate_script_usecase import GenerateScriptUseCase
from src.usecase.podcast.summarize_chapters_usecase import SummarizeChaptersUseCase
from src.usecase.podcast.synthesize_audio_usecase import SynthesizeAudioUseCase

logger = logging.getLogger(__name__)


class GeneratePodcastUseCase:
    """Use case for generating podcast audio from a book"""

    def __init__(
        self,
        podcast_repository: PodcastRepository,
        book_repository: BookRepository,
        gemini_client: GeminiClient,
        tts_client: CloudTTSClient,
        gcs_client: GCSClient,
    ) -> None:
        self.podcast_repository = podcast_repository
        self.book_repository = book_repository

        # Initialize use cases and services
        self.chapter_extractor = ExtractChaptersUseCase()
        self.summarizer = SummarizeChaptersUseCase(gemini_client)
        self.script_generator = GenerateScriptUseCase(gemini_client)
        self.audio_synthesizer = SynthesizeAudioUseCase(tts_client)
        self.audio_processor = AudioProcessor()
        self.gcs_client = gcs_client

    async def execute(self, podcast_id: PodcastId) -> None:
        """Generate podcast audio for the given podcast ID

        Args:
            podcast_id: ID of the podcast to generate

        Raises:
            PodcastNotFoundError: If podcast doesn't exist
            PodcastGenerationError: If generation fails

        """
        try:
            # Get podcast
            podcast = await self.podcast_repository.find_by_id(podcast_id)
            if not podcast:
                raise PodcastNotFoundError(str(podcast_id))

            # Check if podcast can be processed
            if not podcast.can_be_processed():
                logger.warning(f"Podcast {podcast_id} cannot be processed (status: {podcast.status})")
                return

            # Mark as processing
            await self.podcast_repository.update_status(podcast_id, PodcastStatus.processing())

            # Get book information
            book = self.book_repository.find_by_id(podcast.book_id)
            if not book:
                await self._mark_as_failed(podcast_id, "Book not found")
                return

            # Generate podcast
            await self._generate_podcast_audio(podcast, book)

        except Exception as e:
            logger.error(f"Error generating podcast {podcast_id}: {str(e)}")
            await self._mark_as_failed(podcast_id, str(e))
            raise PodcastGenerationError(str(e))

    async def _generate_podcast_audio(self, podcast: Podcast, book: Book) -> None:
        """Generate the actual podcast audio

        Args:
            podcast: Podcast entity
            book: Book entity

        """
        try:
            # Step 1: Extract and process chapters
            processed_chapters = await self._extract_and_process_chapters(book)

            # Step 2: Generate book summary
            book_summary = await self._generate_book_summary(processed_chapters, book.name.value)

            # Step 3: Generate and save podcast script
            script = await self._generate_and_save_script(podcast, book_summary, book.name.value)

            # Step 4: Synthesize and process audio
            processed_audio = await self._synthesize_and_process_audio(script)

            # Step 5: Upload audio and mark as completed
            await self._upload_and_complete(podcast, processed_audio)

            logger.info(f"Podcast {podcast.id} generated successfully")

        except Exception as e:
            logger.error(f"Error in podcast generation steps: {str(e)}")
            raise

    async def _extract_and_process_chapters(self, book: Book) -> list:
        """Extract chapters from EPUB and process them

        Args:
            book: Book entity

        Returns:
            List of processed chapters

        """
        return await self.chapter_extractor.execute(book.file_path, max_chapters=15)

    async def _generate_book_summary(self, chapters: list, book_title: str) -> str:
        """Generate book summary from chapters

        Args:
            chapters: List of processed chapters
            book_title: Title of the book

        Returns:
            Book summary

        """
        logger.info(f"Summarizing {len(chapters)} chapters")
        return await self.summarizer.execute(chapters, book_title)

    async def _generate_and_save_script(self, podcast: Podcast, book_summary: str, book_title: str) -> PodcastScript:
        """Generate podcast script and save it

        Args:
            podcast: Podcast entity
            book_summary: Summary of the book
            book_title: Title of the book

        Returns:
            Generated script

        """
        logger.info("Generating podcast script")
        script = await self.script_generator.execute(book_summary=book_summary, book_title=book_title, target_words=1000)

        # Save script to podcast
        podcast.set_script(script)
        await self.podcast_repository.update(podcast)

        return script

    async def _synthesize_and_process_audio(self, script: PodcastScript) -> bytes:
        """Synthesize and process audio from script

        Args:
            script: Podcast script

        Returns:
            Processed audio data

        """
        logger.info("Synthesizing audio")
        audio_data = await self.audio_synthesizer.execute(script)

        logger.info("Processing audio")
        return await self.audio_processor.process_audio(audio_data)

    async def _upload_and_complete(self, podcast: Podcast, audio_data: bytes) -> None:
        """Upload audio and mark podcast as completed

        Args:
            podcast: Podcast entity
            audio_data: Processed audio data

        """
        logger.info("Uploading to storage")
        audio_url = await self._upload_audio(podcast, audio_data)

        # Mark as completed
        await self.podcast_repository.update_status(podcast.id, PodcastStatus.completed(), audio_url=audio_url)

    async def _upload_audio(self, podcast: Podcast, audio_data: bytes) -> str:
        """Upload audio to cloud storage

        Args:
            podcast: Podcast entity
            audio_data: Processed audio data

        Returns:
            URL to the uploaded audio file

        """
        file_name = f"podcasts/{podcast.id.value}/{podcast.id.value}.mp3"
        try:
            return self.gcs_client.upload_file(file_name, audio_data, "audio/mpeg")
        except GCSBucketError as e:
            logger.error(f"Podcast upload failed: {str(e)}")
            raise PodcastGenerationError(f"Upload failed due to bucket issue: {str(e)}") from e

    async def _mark_as_failed(self, podcast_id: PodcastId, error_message: str) -> None:
        """Mark podcast as failed with error message"""
        try:
            await self.podcast_repository.update_status(podcast_id, PodcastStatus.failed(), error_message=error_message)
        except Exception as e:
            logger.error(f"Error marking podcast as failed: {str(e)}")
