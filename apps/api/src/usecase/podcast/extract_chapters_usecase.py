import logging
import os
import tempfile

import aiohttp
from ebooklib import ITEM_DOCUMENT, epub

from src.infrastructure.external.epub import Chapter

logger = logging.getLogger(__name__)


class ExtractChaptersUseCase:
    """Use case for extracting and processing chapters from EPUB files"""

    def __init__(self) -> None:
        self.max_chapter_length = 10000  # Maximum characters per chapter for processing

    async def execute(self, epub_path: str) -> list[Chapter]:
        """Extract and process chapters from an EPUB file

        Args:
            epub_path: Path to the EPUB file (can be URL)
            max_chapters: Maximum number of chapters to process (defaults to config value)

        Returns:
            List of processed chapters ready for summarization

        """
        logger.info(f"Extracting chapters from {epub_path}")

        # Extract chapters using infrastructure service
        chapters = await self._extract_chapters(epub_path)

        # Apply business logic for filtering and processing
        filtered_chapters = self._filter_chapters(chapters)
        processed_chapters = self._split_long_chapters(filtered_chapters)

        logger.info(f"Processed {len(processed_chapters)} chapters (original: {len(chapters)})")

        return processed_chapters

    async def _extract_chapters(self, epub_path: str) -> list[Chapter]:
        """Extract chapters from an EPUB file

        Args:
            epub_path: Path to the EPUB file

        Returns:
            List of Chapter objects

        """
        try:
            # If `epub_path` is a URL, download it first.
            if epub_path.startswith(("http://", "https://")):
                try:
                    async with aiohttp.ClientSession() as session, session.get(epub_path) as resp:
                        resp.raise_for_status()
                        data = await resp.read()

                    # ebooklib.read_epub expects a file path or a file-like object that
                    # behaves like a zip file. Passing BytesIO directly triggers an
                    # os.path.isdir check inside ebooklib and results in a TypeError.
                    # To avoid this, write the bytes to a temporary file and pass the
                    # file path to read_epub, then clean up the file afterwards.

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as tmp_file:
                        tmp_file.write(data)
                        tmp_path = tmp_file.name

                    try:
                        book = epub.read_epub(tmp_path)
                    finally:
                        # Ensure the temporary file is removed
                        try:
                            os.remove(tmp_path)
                        except OSError:
                            logger.warning(
                                "Failed to remove temporary EPUB file %s after processing.",
                                tmp_path,
                            )
                except Exception as url_err:
                    logger.error(f"Failed to download EPUB from URL {epub_path}: {url_err}")
                    raise
            else:
                # Assume local filesystem path
                book = epub.read_epub(epub_path)
            chapters = []
            chapter_index = 0

            # Get all items of type ITEM_DOCUMENT
            for item in book.get_items_of_type(ITEM_DOCUMENT):
                # Get content
                content = item.get_content().decode("utf-8", errors="ignore")

                # Skip if content is too short (likely navigation or metadata)
                if len(content) < 100:
                    continue

                # Extract title if available
                title = item.get_name()
                if hasattr(item, "title") and item.title:
                    title = item.title

                chapter = Chapter(index=chapter_index, title=title, content=content)

                # Only include chapters with substantial text content
                text_content = chapter.get_text_content()
                if len(text_content) > 50:  # Minimum text length
                    chapters.append(chapter)
                    chapter_index += 1

            if not chapters:
                raise ValueError("No chapters found in EPUB file")

            logger.info(f"Extracted {len(chapters)} chapters from EPUB")
            return chapters

        except Exception as e:
            logger.error(f"Error extracting chapters from EPUB: {str(e)}")
            raise

    def _split_long_chapters(self, chapters: list[Chapter]) -> list[Chapter]:
        """Split chapters that are too long for processing

        Args:
            chapters: List of chapters to process

        Returns:
            List of chapters with long ones split

        """
        processed_chapters = []

        for chapter in chapters:
            text = chapter.get_text_content()

            if len(text) <= self.max_chapter_length:
                processed_chapters.append(chapter)
            else:
                # Split long chapter into chunks
                chunks = []
                words = text.split()
                current_chunk: list[str] = []
                current_length = 0

                for word in words:
                    word_length = len(word) + 1  # +1 for space
                    if current_length + word_length > self.max_chapter_length and current_chunk:
                        chunk_text = " ".join(current_chunk)
                        chunks.append(chunk_text)
                        current_chunk = [word]
                        current_length = word_length
                    else:
                        current_chunk.append(word)
                        current_length += word_length

                # Add remaining words
                if current_chunk:
                    chunks.append(" ".join(current_chunk))

                # Create new Chapter objects for each chunk
                for i, chunk_text in enumerate(chunks):
                    chunk_title = f"{chapter.title or 'Chapter'} (Part {i + 1})"
                    processed_chapters.append(
                        Chapter(
                            index=chapter.index,
                            title=chunk_title,
                            content=chunk_text,  # Already plain text
                        )
                    )

        return processed_chapters

    def _filter_chapters(self, chapters: list[Chapter]) -> list[Chapter]:
        """Filter chapters to a manageable number for processing

        Args:
            chapters: List of all chapters

        Returns:
            Filtered list of chapters

        """
        if len(chapters) <= self.max_chapter_length:
            return chapters

        # Try to evenly sample chapters
        step = len(chapters) / self.max_chapter_length
        selected_indices = [int(i * step) for i in range(self.max_chapter_length)]

        return [chapters[i] for i in selected_indices if i < len(chapters)]
