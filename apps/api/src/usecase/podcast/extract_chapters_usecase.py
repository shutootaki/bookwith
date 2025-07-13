import logging

from src.domain.podcast.services.chapter_processor import ChapterProcessor
from src.infrastructure.external.epub import Chapter, EpubReader
from src.usecase.podcast.podcast_config import PodcastConfig

logger = logging.getLogger(__name__)


class ExtractChaptersUseCase:
    """Use case for extracting and processing chapters from EPUB files"""

    def __init__(
        self,
        config: PodcastConfig | None = None,
    ) -> None:
        self.epub_reader = EpubReader()
        self.chapter_processor = ChapterProcessor()
        self.config = config or PodcastConfig()

    async def execute(self, epub_path: str, max_chapters: int | None = None) -> list[Chapter]:
        """Extract and process chapters from an EPUB file

        Args:
            epub_path: Path to the EPUB file (can be URL)
            max_chapters: Maximum number of chapters to process (defaults to config value)

        Returns:
            List of processed chapters ready for summarization

        """
        max_chapters = max_chapters or self.config.max_chapters
        logger.info(f"Extracting chapters from {epub_path}")

        # Extract chapters using infrastructure service
        chapters = await self.epub_reader.extract_chapters(epub_path)

        # Apply business logic for filtering and processing
        filtered_chapters = self.chapter_processor.filter_chapters(chapters, max_chapters=max_chapters)
        processed_chapters = self.chapter_processor.split_long_chapters(filtered_chapters)

        logger.info(f"Processed {len(processed_chapters)} chapters (original: {len(chapters)})")

        return processed_chapters
