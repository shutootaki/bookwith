import logging
import random

from src.domain.podcast.exceptions.podcast_exceptions import PodcastScriptGenerationError
from src.domain.podcast.value_objects.podcast_script import PodcastScript, ScriptTurn
from src.domain.podcast.value_objects.speaker_role import SpeakerRole
from src.infrastructure.external.gemini import GeminiClient
from src.infrastructure.external.gemini.prompts import (
    PODCAST_CLOSING_TEMPLATES,
    PODCAST_OPENING_TEMPLATES,
)

logger = logging.getLogger(__name__)


class ScriptGeneratorService:
    """Service for generating podcast scripts from book summaries"""

    def __init__(self, gemini_client: GeminiClient) -> None:
        self.gemini_client = gemini_client
        self.min_turns = 6  # Minimum dialogue turns
        self.max_turns = 30  # Maximum dialogue turns

    async def generate_script(self, book_summary: str, book_title: str, target_words: int = 1000, include_intro_outro: bool = True) -> PodcastScript:
        """Generate a podcast script from book summary

        Args:
            book_summary: Summary of the book
            book_title: Title of the book
            target_words: Target word count for the script
            include_intro_outro: Whether to add intro and outro

        Returns:
            PodcastScript domain object

        """
        try:
            # Generate dialogue using Gemini
            logger.info(f"Generating podcast script for '{book_title}'")
            dialogue_turns = await self.gemini_client.generate_podcast_script(
                summary=book_summary, book_title=book_title, target_words=target_words, temperature=0.7
            )

            # Validate generated dialogue
            if not dialogue_turns:
                raise PodcastScriptGenerationError("No dialogue generated")

            # Validate speaker count (maximum 2 speakers limit)
            self._validate_speaker_count(dialogue_turns)

            # Convert to domain objects
            script_turns = []

            # Add intro if requested
            if include_intro_outro:
                intro_turn = self._create_intro_turn(book_title)
                script_turns.append(intro_turn)

            # Add main dialogue
            for turn_data in dialogue_turns:
                try:
                    speaker = SpeakerRole.from_string(turn_data["speaker"])
                    turn = ScriptTurn(speaker=speaker, text=turn_data["text"])
                    script_turns.append(turn)
                except Exception as e:
                    logger.warning(f"Skipping invalid turn: {e}")
                    continue

            # Add outro if requested
            if include_intro_outro:
                outro_turn = self._create_outro_turn(book_title)
                script_turns.append(outro_turn)

            # Validate final script
            if len(script_turns) < self.min_turns:
                raise PodcastScriptGenerationError(f"Generated script too short: {len(script_turns)} turns")

            # Create and return PodcastScript
            script = PodcastScript(turns=script_turns)

            logger.info(f"Generated script with {script.get_turn_count()} turns and {script.get_total_length()} characters")

            return script

        except Exception as e:
            logger.error(f"Error generating podcast script: {str(e)}")
            raise PodcastScriptGenerationError(str(e))

    def _create_intro_turn(self, book_title: str) -> ScriptTurn:
        """Create an introduction turn"""
        template = random.choice(PODCAST_OPENING_TEMPLATES)
        intro_text = template.format(book_title=book_title)

        return ScriptTurn(
            speaker=SpeakerRole.host(),
            text=intro_text,
        )

    def _create_outro_turn(self, book_title: str) -> ScriptTurn:
        """Create a closing turn"""
        template = random.choice(PODCAST_CLOSING_TEMPLATES)
        outro_text = template.format(book_title=book_title)

        return ScriptTurn(
            speaker=SpeakerRole.host(),
            text=outro_text,
        )

    async def enhance_script(self, script: PodcastScript, book_metadata: dict | None = None) -> PodcastScript:
        """Enhance an existing script with additional information

        Args:
            script: Existing podcast script
            book_metadata: Optional book metadata to incorporate

        Returns:
            Enhanced PodcastScript

        """
        enhanced_turns = list(script.turns)

        # Add author information if available
        if book_metadata and book_metadata.get("creator"):
            author_info = f"This book was written by {book_metadata['creator']}."
            # Insert after intro
            if len(enhanced_turns) > 1:
                author_turn = ScriptTurn(
                    speaker=SpeakerRole.guest(),
                    text=author_info,
                )
                enhanced_turns.insert(1, author_turn)

        return PodcastScript(turns=enhanced_turns)

    def _validate_speaker_count(self, dialogue_turns: list[dict]) -> None:
        """Validate that speaker count is within limits (maximum 2 speakers)"""
        unique_speakers = {turn["speaker"] for turn in dialogue_turns}
        if len(unique_speakers) > 2:
            raise PodcastScriptGenerationError(f"Maximum 2 speakers supported. {len(unique_speakers)} speakers detected: {unique_speakers}")
        logger.info(f"Speaker validation passed: {len(unique_speakers)} speakers detected")

    def validate_script_balance(self, script: PodcastScript) -> bool:
        """Validate that the script has reasonable balance between speakers

        Args:
            script: Script to validate

        Returns:
            True if balanced, raises exception otherwise

        """
        r_count = sum(1 for turn in script.turns if turn.speaker.is_host())
        s_count = sum(1 for turn in script.turns if turn.speaker.is_guest())

        total_turns = len(script.turns)

        # Check minimum participation
        min_participation = 0.2  # Each speaker should have at least 20% of turns
        if r_count < total_turns * min_participation:
            raise ValueError(f"Speaker R has too few turns: {r_count}/{total_turns}")
        if s_count < total_turns * min_participation:
            raise ValueError(f"Speaker S has too few turns: {s_count}/{total_turns}")

        return True

    def split_long_turns(self, script: PodcastScript, max_length: int = 500) -> PodcastScript:
        """Split turns that are too long for natural speech

        Args:
            script: Script to process
            max_length: Maximum characters per turn

        Returns:
            Script with split turns

        """
        processed_turns = []

        for turn in script.turns:
            if len(turn.text) <= max_length:
                processed_turns.append(turn)
            else:
                # Split long turn at sentence boundaries
                sentences = turn.text.split(". ")
                current_chunk: list[str] = []
                current_length = 0

                for sentence in sentences:
                    sentence_with_period = sentence + "." if not sentence.endswith(".") else sentence
                    sentence_length = len(sentence_with_period)

                    if current_length + sentence_length > max_length and current_chunk:
                        # Create turn with current chunk
                        chunk_text = " ".join(current_chunk)
                        processed_turns.append(ScriptTurn(speaker=turn.speaker, text=chunk_text))
                        current_chunk = [sentence_with_period]
                        current_length = sentence_length
                    else:
                        current_chunk.append(sentence_with_period)
                        current_length += sentence_length

                # Add remaining sentences
                if current_chunk:
                    chunk_text = " ".join(current_chunk)
                    processed_turns.append(ScriptTurn(speaker=turn.speaker, text=chunk_text))

        return PodcastScript(turns=processed_turns)
