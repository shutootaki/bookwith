import logging

from google.cloud import texttospeech_v1beta1 as tts

from src.config.app_config import AppConfig
from src.domain.podcast.exceptions import PodcastAudioSynthesisError

logger = logging.getLogger(__name__)


class CloudTTSClient:
    """Google Cloud Text-to-Speech client for audio synthesis"""

    def __init__(self) -> None:
        self.config = AppConfig.get_config()

        # Use default credentials (ADC). If gcloud auth application-default login has been run,
        # ~/.config/gcloud/application_default_credentials.json will be used.
        self.client = tts.TextToSpeechClient()

        # Configure voice settings (Multi-speaker voice requires allowlist)
        # self.multi_speaker_voice = tts.VoiceSelectionParams(
        #     language_code="en-US",
        #     name="en-US-Studio-MultiSpeaker",
        # )

        # Fallback single-speaker voices (speaker HOST / speaker GUEST)
        self.voice_R = tts.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Studio-O",
        )
        self.voice_S = tts.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Studio-Q",
        )

        self.japanese_voice = tts.VoiceSelectionParams(
            language_code="ja-JP",
            name="ja-JP-Neural2-B",  # Male voice for consistency
        )

        # Configure audio settings
        self.audio_config = tts.AudioConfig(
            audio_encoding=tts.AudioEncoding.MP3,
            sample_rate_hertz=24000,  # 24kHz for synthesis
        )

    async def synthesize_multi_speaker(self, turns: list[dict]) -> bytes:
        """Synthesize multi-speaker dialogue using Studio MultiSpeaker voice

        Args:
            turns: List of dialogue turns with 'speaker' and 'text' keys

        Returns:
            Audio data in MP3 format

        """
        try:
            # --- Original multi-speaker implementation (requires allowlist) ---
            # Build MultiSpeakerMarkup
            # markup_turns = [
            #     tts.MultiSpeakerMarkup.Turn(text=turn["text"], speaker=turn["speaker"])
            #     for turn in turns
            # ]
            # multi_speaker_markup = tts.MultiSpeakerMarkup(turns=markup_turns)
            # synthesis_input = tts.SynthesisInput(multi_speaker_markup=multi_speaker_markup)
            # response = self.client.synthesize_speech(
            #     input=synthesis_input,
            #     voice=self.multi_speaker_voice,
            #     audio_config=self.audio_config,
            # )
            # return response.audio_content

            # --- Fallback implementation using two single-speaker voices ---
            audio_contents: list[bytes] = []
            for turn in turns:
                synthesis_input = tts.SynthesisInput(text=turn["text"])
                voice_params = self.voice_R if turn["speaker"] == "HOST" else self.voice_S
                response = self.client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice_params,
                    audio_config=self.audio_config,
                )
                audio_contents.append(response.audio_content)

            return b"".join(audio_contents)

        except Exception as e:
            logger.error(f"Error synthesizing multi-speaker audio: {str(e)}")
            raise PodcastAudioSynthesisError(f"Multi-speaker synthesis failed: {str(e)}")

    async def synthesize_japanese(self, text: str) -> bytes:
        """Synthesize Japanese text using Neural2 voice

        Args:
            text: Japanese text to synthesize

        Returns:
            Audio data in MP3 format

        """
        try:
            synthesis_input = tts.SynthesisInput(text=text)

            response = self.client.synthesize_speech(input=synthesis_input, voice=self.japanese_voice, audio_config=self.audio_config)

            return response.audio_content

        except Exception as e:
            logger.error(f"Error synthesizing Japanese audio: {str(e)}")
            raise PodcastAudioSynthesisError(f"Japanese synthesis failed: {str(e)}")

    async def synthesize_with_chunks(self, turns: list[dict], max_chars_per_request: int = 5000) -> list[bytes]:
        """Synthesize dialogue in chunks if it exceeds the character limit

        Args:
            turns: List of dialogue turns
            max_chars_per_request: Maximum characters per synthesis request

        Returns:
            List of audio chunks in MP3 format

        """
        chunks: list[bytes] = []
        current_chunk: list[dict] = []
        current_length = 0

        for turn in turns:
            turn_length = len(turn["text"])

            # If adding this turn exceeds the limit, synthesize current chunk
            if current_length + turn_length > max_chars_per_request and current_chunk:
                audio_chunk = await self.synthesize_multi_speaker(current_chunk)
                chunks.append(audio_chunk)
                current_chunk = []
                current_length = 0

            # Add turn to current chunk
            current_chunk.append(turn)
            current_length += turn_length

        # Synthesize remaining turns
        if current_chunk:
            audio_chunk = await self.synthesize_multi_speaker(current_chunk)
            chunks.append(audio_chunk)

        return chunks

    def validate_dialogue_turns(self, turns: list[dict]) -> bool:
        """Validate dialogue turns format and content

        Args:
            turns: List of dialogue turns to validate

        Returns:
            True if valid, raises exception otherwise

        """
        if not turns:
            raise ValueError("Dialogue turns cannot be empty")

        valid_speakers = {"HOST", "GUEST"}

        for i, turn in enumerate(turns):
            if not isinstance(turn, dict):
                raise ValueError(f"Turn {i} must be a dictionary")

            if "speaker" not in turn or "text" not in turn:
                raise ValueError(f"Turn {i} must have 'speaker' and 'text' keys")

            if turn["speaker"] not in valid_speakers:
                raise ValueError(f"Turn {i} has invalid speaker: {turn['speaker']}")

            if not turn["text"] or not isinstance(turn["text"], str):
                raise ValueError(f"Turn {i} has invalid text")

        return True
