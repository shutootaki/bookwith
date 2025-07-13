import logging

from google.cloud import texttospeech_v1beta1 as tts

from src.config.app_config import AppConfig
from src.domain.podcast.exceptions import PodcastAudioSynthesisError

logger = logging.getLogger(__name__)


class CloudTTSClient:
    """Google Cloud Text-to-Speech client for audio synthesis"""

    def __init__(self) -> None:
        self.config = AppConfig.get_config()
        self.client = tts.TextToSpeechClient()
        # Configure voice settings by language
        self.voices = {
            "en-US": {
                "HOST": tts.VoiceSelectionParams(
                    language_code="en-US",
                    name="en-US-Standard-B",
                ),
                "GUEST": tts.VoiceSelectionParams(
                    language_code="en-US",
                    name="en-US-Standard-F",
                ),
            },
            "ja-JP": {
                "HOST": tts.VoiceSelectionParams(
                    language_code="ja-JP",
                    name="ja-JP-Standard-B",
                ),
                "GUEST": tts.VoiceSelectionParams(
                    language_code="ja-JP",
                    name="ja-JP-Standard-D",
                ),
            },
            "cmn-CN": {
                "HOST": tts.VoiceSelectionParams(
                    language_code="cmn-CN",
                    name="cmn-CN-Standard-C",
                ),
                "GUEST": tts.VoiceSelectionParams(
                    language_code="cmn-CN",
                    name="cmn-CN-Standard-A",
                ),
            },
        }
        # Configure audio settings
        self.audio_config = tts.AudioConfig(
            audio_encoding=tts.AudioEncoding.MP3,
            sample_rate_hertz=24000,  # 24kHz for synthesis
        )

    async def synthesize_multi_speaker(self, turns: list[dict], language: str = "en-US") -> bytes:
        """Synthesize multi-speaker dialogue using Studio MultiSpeaker voice

        Args:
            turns: List of dialogue turns with 'speaker' and 'text' keys
            language: Language of the script
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

            # Get language-specific voices, fallback to English if not found
            language_voices = self.voices.get(language, self.voices["en-US"])

            for turn in turns:
                synthesis_input = tts.SynthesisInput(text=turn["text"])
                # Select voice based on speaker
                voice_params = language_voices.get(turn["speaker"], language_voices["HOST"])
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

    async def synthesize_with_chunks(self, turns: list[dict], max_chars_per_request: int = 5000, language: str = "en-US") -> list[bytes]:
        """Synthesize dialogue in chunks if it exceeds the character limit

        Args:
            turns: List of dialogue turns
            max_chars_per_request: Maximum characters per synthesis request
            language: Language of the script

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
                audio_chunk = await self.synthesize_multi_speaker(current_chunk, language)
                chunks.append(audio_chunk)
                current_chunk = []
                current_length = 0

            # Add turn to current chunk
            current_chunk.append(turn)
            current_length += turn_length

        # Synthesize remaining turns
        if current_chunk:
            audio_chunk = await self.synthesize_multi_speaker(current_chunk, language)
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
