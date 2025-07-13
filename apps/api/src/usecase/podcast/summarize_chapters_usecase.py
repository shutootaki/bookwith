import asyncio
import logging

from src.domain.podcast.value_objects.language import PodcastLanguage
from src.infrastructure.external.epub import Chapter
from src.infrastructure.external.gemini import GeminiClient
from src.infrastructure.external.gemini.prompts.podcast_prompts import get_prompts_with_language
from src.usecase.podcast.podcast_config import PodcastConfig

logger = logging.getLogger(__name__)


class SummarizeChaptersUseCase:
    """Use case for summarizing book chapters"""

    def __init__(self) -> None:
        self.gemini_client = GeminiClient()
        self.config = PodcastConfig()

    async def execute(self, chapters: list[Chapter], book_title: str, language: PodcastLanguage = PodcastLanguage.EN_US) -> str:
        """Summarize all chapters and create a comprehensive book summary"""
        try:
            # NOTE: Limit chapters to 6 to avoid API rate limits
            chapters_to_summarize = chapters[:6]
            logger.info(f"Starting summarization of {len(chapters_to_summarize)} chapters (limited to 6)")

            # First, summarize individual chapters
            chapter_summaries = await self._summarize_chapters_batch(chapters_to_summarize, language)

            # Then, combine chapter summaries into a book summary
            logger.info("Combining chapter summaries into book summary")
            return await self._create_book_summary(chapter_summaries, book_title, language)

        except Exception as e:
            logger.error(f"Error during chapter summarization: {str(e)}")
            raise

    async def _summarize_chapters_batch(self, chapters: list[Chapter], language: PodcastLanguage = PodcastLanguage.EN_US) -> list[str]:
        """Summarize chapters sequentially with a delay to respect rate limits."""
        summaries = []
        # 15 requests per minute for the free tier. Wait 4 seconds between requests.
        delay_seconds = 4
        for i, chapter in enumerate(chapters):
            summary = await self._summarize_single_chapter(chapter, language)
            summaries.append(summary)
            if i < len(chapters) - 1:  # Don't sleep after the last chapter
                await asyncio.sleep(delay_seconds)
        return summaries

    async def _summarize_single_chapter(self, chapter: Chapter, language: PodcastLanguage = PodcastLanguage.EN_US) -> str:
        """Summarize a single chapter"""
        try:
            # Get plain text content once (may be large)
            raw_text = chapter.get_text_content()

            # Retry with progressively shorter inputs
            # Tuple = (max_characters, max_output_tokens)
            attempts = list(zip(self.config.chapter_content_clip_lengths, self.config.chapter_summary_max_tokens, strict=False))

            for idx, (clip_len, max_tokens) in enumerate(attempts):
                try:
                    lang_prompts = get_prompts_with_language(language)
                    prompt = lang_prompts["chapter_summary"]
                    if isinstance(prompt, str):
                        prompt = prompt.format(chapter_content=raw_text[:clip_len])
                    else:
                        raise ValueError(f"Expected string for chapter_summary prompt, got {type(prompt)}")

                    return await self.gemini_client.summarize_text(
                        text=prompt,
                        max_output_tokens=max_tokens,
                        temperature=0.3,
                    )
                except ValueError as ve:
                    # retry only on MAX_TOKENS (finish_reason=2)
                    if "finish_reason=2" in str(ve) and idx + 1 < len(attempts):
                        logger.warning(f"Retrying chapter {chapter.index} summarization with shorter input (len={clip_len}) due to token limit")
                        continue
                    # For other errors or final attempt, raise
                    raise ve
            return f"Chapter {chapter.index + 1}: Summary unavailable due to processing error."
        except Exception as e:
            logger.error(f"Error summarizing chapter {chapter.index}: {str(e)}")
            # Return a fallback summary on error
            return f"Chapter {chapter.index + 1}: Summary unavailable due to processing error."

    async def _create_book_summary(self, chapter_summaries: list[str], book_title: str, language: PodcastLanguage = PodcastLanguage.EN_US) -> str:
        """Two-pass summarization to stay within token limits.

        1. Chunk the chapter summaries (default 5 per chunk) and get partial summaries
        2. Combine those partial summaries into the final book summary
        """
        chunk_size = self.config.chapter_summary_chunk_size

        # If we have few chapters, combine directly
        if len(chapter_summaries) <= chunk_size:
            return await self.gemini_client.combine_summaries(
                chapter_summaries,
                book_title,
                max_output_tokens=self.config.final_summary_max_tokens,
                temperature=self.config.summarization_temperature,
                language=language,
            )

        # 1st pass: create partial summaries
        partial_summaries: list[str] = []
        # 15 requests per minute for the free tier. Wait 4 seconds between requests.
        delay_seconds = 4
        for i in range(0, len(chapter_summaries), chunk_size):
            chunk = chapter_summaries[i : i + chunk_size]
            try:
                partial = await self.gemini_client.combine_summaries(
                    chunk,
                    book_title,
                    max_output_tokens=self.config.partial_summary_max_tokens,
                    temperature=self.config.summarization_temperature,
                    language=language,
                )
                partial_summaries.append(partial)
                if i + chunk_size < len(chapter_summaries):
                    await asyncio.sleep(delay_seconds)
            except ValueError as ve:
                # If even a small chunk hits length, fall back to summarize_text on truncated text
                logger.warning(f"Partial summarization failed for chapters {i}-{i + len(chunk) - 1}: {ve}")
                lang_prompts = get_prompts_with_language(language)
                truncated_prompt = lang_prompts["book_summary"]
                if isinstance(truncated_prompt, str):
                    truncated_prompt = truncated_prompt.format(
                        book_title=book_title,
                        chapter_summaries="\n\n".join(chunk)[:2000],
                    )
                else:
                    raise ValueError(f"Expected string for book_summary prompt, got {type(truncated_prompt)}")
                partial = await self.gemini_client.summarize_text(
                    truncated_prompt, max_output_tokens=self.config.partial_summary_max_tokens, temperature=self.config.summarization_temperature
                )
                partial_summaries.append(partial)

        # 2nd pass: combine partial summaries into final summary
        return await self.gemini_client.combine_summaries(
            partial_summaries,
            book_title,
            max_output_tokens=self.config.final_summary_max_tokens,
            temperature=self.config.summarization_temperature,
            language=language,
        )
