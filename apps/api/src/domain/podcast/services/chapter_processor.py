import logging

from src.infrastructure.external.epub import Chapter

logger = logging.getLogger(__name__)


class ChapterProcessor:
    """Domain service for processing book chapters"""

    def __init__(self) -> None:
        self.max_chapter_length = 10000  # Maximum characters per chapter for processing

    def split_long_chapters(self, chapters: list[Chapter]) -> list[Chapter]:
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

    def filter_chapters(self, chapters: list[Chapter], max_chapters: int = 20) -> list[Chapter]:
        """Filter chapters to a manageable number for processing

        Args:
            chapters: List of all chapters
            max_chapters: Maximum number of chapters to process

        Returns:
            Filtered list of chapters

        """
        if len(chapters) <= max_chapters:
            return chapters

        # Try to evenly sample chapters
        step = len(chapters) / max_chapters
        selected_indices = [int(i * step) for i in range(max_chapters)]

        return [chapters[i] for i in selected_indices if i < len(chapters)]
