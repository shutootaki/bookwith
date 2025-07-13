import logging

from src.domain.podcast.exceptions.podcast_exceptions import PodcastAudioSynthesisError
from src.domain.podcast.services.script_validator import ScriptValidator
from src.domain.podcast.value_objects.language import PodcastLanguage
from src.domain.podcast.value_objects.podcast_script import PodcastScript
from src.infrastructure.external.cloud_tts.markup_builder import script_to_dict_list
from src.infrastructure.external.cloud_tts.tts_client import CloudTTSClient
from src.usecase.podcast.podcast_config import PodcastConfig

logger = logging.getLogger(__name__)


class SynthesizeAudioUseCase:
    """Use case for synthesizing audio from podcast scripts"""

    def __init__(
        self,
        script_validator: ScriptValidator | None = None,
        config: PodcastConfig | None = None,
    ) -> None:
        self.tts_client = CloudTTSClient()
        self.script_validator = script_validator or ScriptValidator()
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
            self.script_validator.validate_for_tts(script)

            # Convert script to dict format
            dialogue_turns = script_to_dict_list(script)

            # Check if we need to split into chunks
            if self.script_validator.should_use_chunking(script, self.config.max_chars_per_tts_request):
                logger.info(f"Splitting script into chunks (total: {script.get_total_length()} chars)")
                audio_chunks = await self.tts_client.synthesize_with_chunks(dialogue_turns, self.config.max_chars_per_tts_request, language.value)
            else:
                logger.info("Synthesizing script in single request")
                audio_chunks = [await self.tts_client.synthesize_multi_speaker(dialogue_turns, language.value)]

            return audio_chunks[0] if len(audio_chunks) == 1 else b"".join(audio_chunks)

        except Exception as e:
            logger.error(f"Error during audio synthesis: {str(e)}")
            raise PodcastAudioSynthesisError(str(e))
