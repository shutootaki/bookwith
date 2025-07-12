import logging

from src.domain.podcast.services.chapter_processor import ChapterProcessor
from src.infrastructure.external.epub import Chapter, EpubReader

logger = logging.getLogger(__name__)


class ExtractChaptersUseCase:
    """Use case for extracting and processing chapters from EPUB files"""

    def __init__(self) -> None:
        self.epub_reader = EpubReader()
        self.chapter_processor = ChapterProcessor()

    async def execute(self, epub_path: str, max_chapters: int = 15) -> list[Chapter]:
        """Extract and process chapters from an EPUB file

        Args:
            epub_path: Path to the EPUB file (can be URL)
            max_chapters: Maximum number of chapters to process

        Returns:
            List of processed chapters ready for summarization

        """
        logger.info(f"Extracting chapters from {epub_path}")

        # Extract chapters using infrastructure service
        chapters = await self.epub_reader.extract_chapters(epub_path)

        # Apply business logic for filtering and processing
        filtered_chapters = self.chapter_processor.filter_chapters(chapters, max_chapters=max_chapters)
        processed_chapters = self.chapter_processor.split_long_chapters(filtered_chapters)

        logger.info(f"Processed {len(processed_chapters)} chapters (original: {len(chapters)})")

        return processed_chapters

    async def extract_metadata(self, epub_path: str) -> dict:
        """Extract metadata from EPUB file

        Args:
            epub_path: Path to the EPUB file

        Returns:
            Dictionary containing metadata

        """
        return await self.epub_reader.extract_metadata(epub_path)
