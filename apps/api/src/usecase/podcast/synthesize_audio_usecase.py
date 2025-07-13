import logging

from src.domain.podcast.exceptions.podcast_exceptions import PodcastAudioSynthesisError
from src.domain.podcast.value_objects.language import PodcastLanguage
from src.domain.podcast.value_objects.podcast_script import PodcastScript
from src.infrastructure.external.cloud_tts.tts_client import CloudTTSClient
from src.usecase.podcast.podcast_config import PodcastConfig

logger = logging.getLogger(__name__)


class SynthesizeAudioUseCase:
    """Use case for synthesizing audio from podcast scripts"""

    def __init__(
        self,
        config: PodcastConfig | None = None,
    ) -> None:
        self.tts_client = CloudTTSClient()
        self.config = config or PodcastConfig()

    async def execute(self, script: PodcastScript, language: PodcastLanguage = PodcastLanguage.EN_US) -> bytes:
        """Synthesize audio from a podcast script

        Args:
            script: PodcastScript to synthesize
            language: Language of the script

        Returns:
            Complete audio data in MP3 format

        """
        try:
            # Validate script for TTS
            self._validate_for_tts(script)

            # Convert script to dict format
            dialogue_turns = self._script_to_dict_list(script)

            # Check if we need to split into chunks
            if self._should_use_chunking(script, self.config.max_chars_per_tts_request):
                logger.info(f"Splitting script into chunks (total: {script.get_total_length()} chars)")
                audio_chunks = await self.tts_client.synthesize_with_chunks(dialogue_turns, self.config.max_chars_per_tts_request, language.value)
            else:
                logger.info("Synthesizing script in single request")
                audio_chunks = [await self.tts_client.synthesize_multi_speaker(dialogue_turns, language.value)]

            return audio_chunks[0] if len(audio_chunks) == 1 else b"".join(audio_chunks)

        except Exception as e:
            logger.error(f"Error during audio synthesis: {str(e)}")
            raise PodcastAudioSynthesisError(str(e))

    def _script_to_dict_list(self, script: PodcastScript) -> list[dict[str, str]]:
        """Convert PodcastScript to list of dictionaries for TTS processing"""
        return [{"speaker": str(turn.speaker), "text": turn.text} for turn in script.turns]

    def _should_use_chunking(self, script: PodcastScript, max_chars_per_request: int = 5000) -> bool:
        """Determine if script should be synthesized in chunks

        Args:
            script: PodcastScript to check
            max_chars_per_request: Maximum characters per TTS request

        Returns:
            True if chunking should be used

        """
        return script.get_total_length() > max_chars_per_request

    def _validate_for_tts(self, script: PodcastScript) -> None:
        """Validate that a script is suitable for TTS synthesis

        Args:
            script: PodcastScript to validate

        Raises:
            ValueError: If script is invalid for TTS

        """
        if not script.turns:
            raise ValueError("Script has no turns")

        # Check each turn
        for i, turn in enumerate(script.turns):
            if not turn.text.strip():
                raise ValueError(f"Turn {i} has empty text")

            # Check for excessively long turns
            if len(turn.text) > 5000:
                logger.warning(f"Turn {i} has very long text ({len(turn.text)} chars)")

        # Check total length
        total_length = script.get_total_length()
        if total_length == 0:
            raise ValueError("Script has no content")

        logger.info(f"Script validated: {script.get_turn_count()} turns, {total_length} chars")
