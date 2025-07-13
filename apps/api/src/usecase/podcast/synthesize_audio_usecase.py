import logging

from src.domain.podcast.exceptions.podcast_exceptions import PodcastAudioSynthesisError
from src.domain.podcast.services.script_validator import ScriptValidator
from src.domain.podcast.value_objects.language import PodcastLanguage
from src.domain.podcast.value_objects.podcast_script import PodcastScript
from src.infrastructure.external.cloud_tts.markup_builder import script_to_dict_list
from src.infrastructure.external.cloud_tts.tts_client import CloudTTSClient

logger = logging.getLogger(__name__)


class SynthesizeAudioUseCase:
    """Use case for synthesizing audio from podcast scripts"""

    def __init__(self, tts_client: CloudTTSClient) -> None:
        self.tts_client = tts_client
        self.script_validator = ScriptValidator()
        self.max_chars_per_request = 5000

    async def execute(self, script: PodcastScript, add_japanese_intro: bool = False, language: PodcastLanguage = PodcastLanguage.EN_US) -> bytes:
        """Synthesize audio from a podcast script

        Args:
            script: PodcastScript to synthesize
            add_japanese_intro: Whether to add Japanese introduction
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
            if self.script_validator.should_use_chunking(script, self.max_chars_per_request):
                # Need to split into multiple requests
                logger.info(f"Splitting script into chunks (total: {script.get_total_length()} chars)")
                audio_chunks = await self.tts_client.synthesize_with_chunks(dialogue_turns, self.max_chars_per_request, language.value)
            else:
                # Single request is sufficient
                logger.info("Synthesizing script in single request")
                audio_chunks = [await self.tts_client.synthesize_multi_speaker(dialogue_turns, language.value)]

            # Add Japanese intro if requested
            if add_japanese_intro:
                japanese_intro = await self._create_japanese_intro()
                if japanese_intro:
                    audio_chunks.insert(0, japanese_intro)

            # Return audio chunks for processing
            return audio_chunks[0] if len(audio_chunks) == 1 else b"".join(audio_chunks)

        except Exception as e:
            logger.error(f"Error during audio synthesis: {str(e)}")
            raise PodcastAudioSynthesisError(str(e))

    async def synthesize_in_batches(
        self, script: PodcastScript, batch_size: int = 10, language: PodcastLanguage = PodcastLanguage.EN_US
    ) -> list[bytes]:
        """Synthesize script in batches of turns

        Args:
            script: PodcastScript to synthesize
            batch_size: Number of turns per batch
            language: Language of the script

        Returns:
            List of audio chunks

        """
        audio_chunks = []
        turns = script_to_dict_list(script)

        # Process in batches
        for i in range(0, len(turns), batch_size):
            batch = turns[i : i + batch_size]

            try:
                audio_chunk = await self.tts_client.synthesize_multi_speaker(batch, language.value)
                audio_chunks.append(audio_chunk)
            except Exception as e:
                logger.error(f"Error synthesizing batch {i // batch_size}: {str(e)}")
                # Continue with other batches
                continue

        if not audio_chunks:
            raise PodcastAudioSynthesisError("No audio chunks were successfully synthesized")

        return audio_chunks

    async def _create_japanese_intro(self) -> bytes | None:
        """Create a Japanese introduction for the podcast"""
        try:
            intro_text = "こんにちは！今日のポッドキャストへようこそ。今回は素晴らしい本について英語でお話しします。"
            return await self.tts_client.synthesize_japanese(intro_text)
        except Exception as e:
            logger.warning(f"Failed to create Japanese intro: {str(e)}")
            return None

    def estimate_duration(self, script: PodcastScript) -> float:
        """Estimate the duration of synthesized audio

        Args:
            script: PodcastScript to estimate

        Returns:
            Estimated duration in seconds

        """
        return self.script_validator.estimate_audio_duration(script)
