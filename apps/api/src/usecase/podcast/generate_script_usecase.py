import logging
import random

from src.domain.podcast.exceptions.podcast_exceptions import PodcastScriptGenerationError
from src.domain.podcast.value_objects.language import PodcastLanguage
from src.domain.podcast.value_objects.podcast_script import PodcastScript, ScriptTurn
from src.domain.podcast.value_objects.speaker_role import SpeakerRole
from src.infrastructure.external.gemini import GeminiClient
from src.infrastructure.external.gemini.prompts.podcast_prompts import get_prompts_with_language
from src.usecase.podcast.podcast_config import PodcastConfig

logger = logging.getLogger(__name__)


class GenerateScriptUseCase:
    """Use case for generating podcast scripts from book summaries"""

    def __init__(self, config: PodcastConfig | None = None) -> None:
        self.gemini_client = GeminiClient()
        self.config = config or PodcastConfig()

    async def execute(
        self,
        book_summary: str,
        book_title: str,
        target_words: int | None = None,
        include_intro_outro: bool = True,
        language: PodcastLanguage = PodcastLanguage.EN_US,
    ) -> PodcastScript:
        """Generate a podcast script from book summary

        Args:
            book_summary: Summary of the book
            book_title: Title of the book
            target_words: Target word count for the script (defaults to config value)
            include_intro_outro: Whether to add intro and outro
            language: Language of the script

        Returns:
            PodcastScript domain object

        """
        target_words = target_words or self.config.target_words

        for attempt in range(self.config.max_retries_script_generation):
            try:
                return await self._generate_script_attempt(book_summary, book_title, target_words, include_intro_outro, language, attempt)
            except PodcastScriptGenerationError:
                raise
            except Exception as e:
                if attempt == self.config.max_retries_script_generation - 1:
                    error_msg = f"Failed after {self.config.max_retries_script_generation} attempts: {str(e)}"
                    if "finish_reason=10" in str(e) or "safety" in str(e).lower():
                        error_msg += " (Content blocked by Gemini safety filters. The content may contain sensitive topics. Please try with different content.)"
                    raise PodcastScriptGenerationError(error_msg)
                logger.error(f"Error generating podcast script (attempt {attempt + 1}): {str(e)}")

        raise PodcastScriptGenerationError("Unexpected error in script generation")

    async def _generate_script_attempt(
        self,
        book_summary: str,
        book_title: str,
        target_words: int,
        include_intro_outro: bool,
        language: PodcastLanguage,
        attempt: int,
    ) -> PodcastScript:
        """Single attempt to generate a script"""
        temperature = self.config.initial_temperature + (attempt * self.config.temperature_increment)

        logger.info(f"Generating podcast script for '{book_title}' (attempt {attempt + 1}/{self.config.max_retries_script_generation})")
        dialogue_turns = await self.gemini_client.generate_podcast_script(
            summary=book_summary, book_title=book_title, target_words=target_words, temperature=temperature, language=language
        )

        if not dialogue_turns:
            raise PodcastScriptGenerationError("No dialogue generated")

        self._validate_speaker_count(dialogue_turns)

        script_turns = self._build_script_turns(dialogue_turns, book_title, language, include_intro_outro)

        if len(script_turns) < self.config.min_script_turns:
            if attempt < self.config.max_retries_script_generation - 1:
                logger.warning(f"Generated script too short: {len(script_turns)} turns. Retrying...")
                raise PodcastScriptGenerationError(f"Script too short: {len(script_turns)} turns")
            raise PodcastScriptGenerationError(
                f"Generated script too short: {len(script_turns)} turns after {self.config.max_retries_script_generation} attempts"
            )

        script = PodcastScript(turns=script_turns)
        self._validate_script_balance(script)

        logger.info(f"Generated script with {script.get_turn_count()} turns and {script.get_total_length()} characters")
        return script

    def _build_script_turns(
        self,
        dialogue_turns: list[dict],
        book_title: str,
        language: PodcastLanguage,
        include_intro_outro: bool,
    ) -> list[ScriptTurn]:
        """Build script turns from dialogue data"""
        script_turns = []

        if include_intro_outro:
            script_turns.append(self._create_intro_turn(book_title, language))

        for turn_data in dialogue_turns:
            try:
                speaker = SpeakerRole.from_string(turn_data["speaker"])
                turn = ScriptTurn(speaker=speaker, text=turn_data["text"])
                script_turns.append(turn)
            except Exception as e:
                logger.warning(f"Skipping invalid turn: {e}")
                continue

        if include_intro_outro:
            script_turns.append(self._create_outro_turn(book_title, language))

        return script_turns

    def _create_intro_turn(self, book_title: str, language: PodcastLanguage = PodcastLanguage.EN_US) -> ScriptTurn:
        """Create an introduction turn"""
        lang_prompts = get_prompts_with_language(language)
        template = random.choice(lang_prompts["openings"])
        intro_text = template.format(book_title=book_title)

        return ScriptTurn(
            speaker=SpeakerRole.host(),
            text=intro_text,
        )

    def _create_outro_turn(self, book_title: str, language: PodcastLanguage = PodcastLanguage.EN_US) -> ScriptTurn:
        """Create a closing turn"""
        lang_prompts = get_prompts_with_language(language)
        template = random.choice(lang_prompts["closings"])
        outro_text = template.format(book_title=book_title)

        return ScriptTurn(
            speaker=SpeakerRole.host(),
            text=outro_text,
        )

    def _validate_speaker_count(self, dialogue_turns: list[dict]) -> None:
        """Validate that speaker count is within limits (maximum 2 speakers)"""
        unique_speakers = {turn["speaker"] for turn in dialogue_turns}
        if len(unique_speakers) > 2:
            raise PodcastScriptGenerationError(f"Maximum 2 speakers supported. {len(unique_speakers)} speakers detected: {unique_speakers}")
        logger.info(f"Speaker validation passed: {len(unique_speakers)} speakers detected")

    def _validate_script_balance(self, script: PodcastScript) -> None:
        """Validate that the script has reasonable balance between speakers"""
        host_count = sum(1 for turn in script.turns if turn.speaker.is_host())
        guest_count = sum(1 for turn in script.turns if turn.speaker.is_guest())
        total_turns = len(script.turns)

        if host_count < total_turns * self.config.min_speaker_participation:
            raise PodcastScriptGenerationError(f"Speaker HOST has too few turns: {host_count}/{total_turns}")
        if guest_count < total_turns * self.config.min_speaker_participation:
            raise PodcastScriptGenerationError(f"Speaker GUEST has too few turns: {guest_count}/{total_turns}")

        logger.info(f"Script balance validated: HOST={host_count}, GUEST={guest_count}, Total={total_turns}")
