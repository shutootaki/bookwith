import asyncio
import logging

from src.infrastructure.external.epub import Chapter
from src.infrastructure.external.gemini import GeminiClient
from src.infrastructure.external.gemini.prompts import BOOK_SUMMARY_PROMPT, CHAPTER_SUMMARY_PROMPT

logger = logging.getLogger(__name__)


class SummarizeChaptersUseCase:
    """Use case for summarizing book chapters"""

    def __init__(self, gemini_client: GeminiClient) -> None:
        self.gemini_client = gemini_client
        self.max_concurrent_requests = 2

    async def execute(self, chapters: list[Chapter], book_title: str) -> str:
        """Summarize all chapters and create a comprehensive book summary

        Args:
            chapters: List of chapters to summarize
            book_title: Title of the book

        Returns:
            Comprehensive book summary

        """
        try:
            # First, summarize individual chapters
            logger.info(f"Starting summarization of {len(chapters)} chapters")
            chapter_summaries = await self._summarize_chapters_batch(chapters)

            # Then, combine chapter summaries into a book summary
            logger.info("Combining chapter summaries into book summary")
            return await self._create_book_summary(chapter_summaries, book_title)

        except Exception as e:
            logger.error(f"Error during chapter summarization: {str(e)}")
            raise

    async def execute_quick_summary(self, chapters: list[Chapter], book_title: str, max_chapters: int = 5) -> str:
        """Create a quick summary using only the first few chapters

        Args:
            chapters: List of chapters
            book_title: Title of the book
            max_chapters: Maximum number of chapters to use

        Returns:
            Quick book summary

        """
        # Use only first few chapters for quick summary
        sample_chapters = chapters[:max_chapters]

        # Summarize sample chapters
        summaries = await self._summarize_chapters_batch(sample_chapters)

        # Create a note about partial summary
        note = f"\n\nNote: This summary is based on the first {len(sample_chapters)} chapters of the book."

        # Combine into book summary
        book_summary = await self._create_book_summary(summaries, book_title)

        return book_summary + note

    async def _summarize_chapters_batch(self, chapters: list[Chapter]) -> list[str]:
        """Summarize chapters in batches to avoid overwhelming the API

        Args:
            chapters: List of chapters to summarize

        Returns:
            List of chapter summaries

        """
        summaries = []

        # Process chapters in batches
        for i in range(0, len(chapters), self.max_concurrent_requests):
            batch = chapters[i : i + self.max_concurrent_requests]
            batch_tasks = [self._summarize_single_chapter(chapter) for chapter in batch]

            # Wait for batch to complete
            batch_summaries = await asyncio.gather(*batch_tasks)
            summaries.extend(batch_summaries)

            # Small delay between batches to avoid rate limiting
            if i + self.max_concurrent_requests < len(chapters):
                await asyncio.sleep(1)

        return summaries

    async def _summarize_single_chapter(self, chapter: Chapter) -> str:
        """Summarize a single chapter

        Args:
            chapter: Chapter to summarize

        Returns:
            Chapter summary

        """
        try:
            # Get plain text content once (may be large)
            raw_text = chapter.get_text_content()

            # ---- Retry with progressively shorter inputs ----
            # Tuple = (max_characters, max_output_tokens)
            attempts: list[tuple[int, int]] = [
                (6000, 400),  # initial try with more tokens
                (4000, 350),  # shorter text
                (2000, 300),  # fallback for stubborn LENGTH errors
            ]

            for idx, (clip_len, max_tokens) in enumerate(attempts):
                try:
                    prompt = CHAPTER_SUMMARY_PROMPT.format(chapter_content=raw_text[:clip_len])

                    return await self.gemini_client.summarize_text(
                        prompt,
                        max_output_tokens=max_tokens,
                        temperature=0.3,
                    )
                except ValueError as ve:
                    # retry only on MAX_TOKENS (finish_reason=2)
                    if "finish_reason=2" in str(ve) and idx + 1 < len(attempts):
                        logger.warning(f"Retrying chapter {chapter.index} summarization with shorter input (len={clip_len}) due to token limit")
                        await asyncio.sleep(0.5)
                        continue
                    # For other errors or final attempt, raise
                    raise ve

        except Exception as e:
            logger.error(f"Error summarizing chapter {chapter.index}: {str(e)}")
            # Return a fallback summary on error;
            return f"Chapter {chapter.index + 1}: Summary unavailable due to processing error."

        # Safety net: ensure the function always returns a string even if all retries somehow fail
        return f"Chapter {chapter.index + 1}: Summary unavailable."

    async def _create_book_summary(self, chapter_summaries: list[str], book_title: str) -> str:
        """Two-pass summarization to stay within token limits.

        1. Chunk the chapter summaries (default 5 per chunk) and get partial summaries
        2. Combine those partial summaries into the final book summary
        """
        CHUNK_SIZE = 5  # noqa: N806

        # If we already have少ない chapters,直接 combine
        if len(chapter_summaries) <= CHUNK_SIZE:
            return await self.gemini_client.combine_summaries(chapter_summaries, book_title, max_output_tokens=1200, temperature=0.3)

        # --- 1st pass: create partial summaries ---
        partial_summaries: list[str] = []
        for i in range(0, len(chapter_summaries), CHUNK_SIZE):
            chunk = chapter_summaries[i : i + CHUNK_SIZE]
            try:
                partial = await self.gemini_client.combine_summaries(
                    chunk,
                    book_title,
                    max_output_tokens=800,
                    temperature=0.3,
                )
                partial_summaries.append(partial)
            except ValueError as ve:
                # If even a small chunk hits length, fall back to summarize_text on truncated text
                logger.warning(f"Partial summarization failed for chapters {i}-{i + len(chunk) - 1}: {ve}")
                truncated_prompt = BOOK_SUMMARY_PROMPT.format(
                    book_title=book_title,
                    chapter_summaries="\n\n".join(chunk)[:2000],
                )
                partial = await self.gemini_client.summarize_text(truncated_prompt, max_output_tokens=800, temperature=0.3)
                partial_summaries.append(partial)

        # --- 2nd pass: combine partial summaries into final summary ---
        return await self.gemini_client.combine_summaries(
            partial_summaries,
            book_title,
            max_output_tokens=1200,
            temperature=0.3,
        )
