import io
import logging
from collections.abc import Iterable
from functools import lru_cache
from pathlib import Path

from pydub import AudioSegment

from src.config.app_config import AppConfig

logger = logging.getLogger(__name__)


# 任意パス IO の窓口になり得るため、AudioSegment で受け付けるパスを allow-list する。
# AUDIO_BGM_DIRS が未設定なら下記のデフォルトに fallback（本番では明示設定推奨）。
_DEFAULT_BGM_DIRS: tuple[str, ...] = (
    "/app/assets/bgm",
    str(Path(__file__).resolve().parents[3] / "assets" / "bgm"),
)
_FFMPEG_PROTOCOL_PREFIXES = ("concat:", "pipe:", "http://", "https://", "rtmp://", "data:")


@lru_cache(maxsize=8)
def _resolve_roots(candidates: tuple[str, ...]) -> tuple[Path, ...]:
    resolved: list[Path] = []
    for c in candidates:
        try:
            resolved.append(Path(c).resolve(strict=False))
        except OSError:
            continue
    return tuple(resolved)


def _path_in_any_root(target: Path, roots: Iterable[Path]) -> bool:
    for root in roots:
        try:
            target.relative_to(root)
            return True
        except ValueError:
            continue
    return False


def _allowed_bgm_paths() -> tuple[Path, ...]:
    candidates = tuple(AppConfig.get_config().audio_bgm_dirs_list) or _DEFAULT_BGM_DIRS
    return _resolve_roots(candidates)


def _is_safe_bgm_path(music_path: str) -> bool:
    """`music_path` が allow-list に含まれる通常ファイルか確認する."""
    if music_path.lower().startswith(_FFMPEG_PROTOCOL_PREFIXES):
        return False
    try:
        resolved = Path(music_path).resolve(strict=True)
    except (OSError, RuntimeError):
        return False
    if not resolved.is_file():
        return False
    return _path_in_any_root(resolved, _allowed_bgm_paths())


def _is_safe_output_path(file_path: str) -> bool:
    """`save_to_file` 用。書き込み先は AUDIO_OUTPUT_DIRS 配下に限定する."""
    candidates = AppConfig.get_config().audio_output_dirs_list
    if not candidates:
        return False
    try:
        resolved = Path(file_path).resolve(strict=False)
    except OSError:
        return False
    return _path_in_any_root(resolved, _resolve_roots(tuple(candidates)))


class AudioProcessor:
    """Service for processing and combining audio files"""

    def __init__(self) -> None:
        self.config = AppConfig.get_config()
        self.output_sample_rate = 44100
        self.output_bitrate = "192k"

    async def process_audio(self, audio_data: bytes | list[bytes], crossfade_ms: int = 0) -> bytes:
        """Process and combine audio data

        Args:
            audio_data: Single audio bytes or list of audio chunks
            crossfade_ms: Milliseconds of crossfade between segments

        Returns:
            Processed audio in MP3 format

        """
        try:
            # Handle single audio vs multiple chunks
            if isinstance(audio_data, bytes):
                # Single audio file
                audio_segment = AudioSegment.from_mp3(io.BytesIO(audio_data))
                processed_audio = self._process_single_audio(audio_segment)
            else:
                # Multiple audio chunks to combine
                processed_audio = self._combine_audio_chunks(audio_data, crossfade_ms)

            # Export to bytes
            output_buffer = io.BytesIO()
            processed_audio.export(output_buffer, format="mp3", bitrate=self.output_bitrate, parameters=["-ar", str(self.output_sample_rate)])

            return output_buffer.getvalue()

        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            raise

    def _process_single_audio(self, audio: AudioSegment) -> AudioSegment:
        """Process a single audio segment

        Args:
            audio: Audio segment to process

        Returns:
            Processed audio segment

        """
        # Convert sample rate if needed
        if audio.frame_rate != self.output_sample_rate:
            audio = audio.set_frame_rate(self.output_sample_rate)

        # Normalize audio levels
        audio = self._normalize_audio(audio)

        # Add fade in/out for smooth listening
        return audio.fade_in(500).fade_out(500)

    def _combine_audio_chunks(self, audio_chunks: list[bytes], crossfade_ms: int) -> AudioSegment:
        """Combine multiple audio chunks into one

        Args:
            audio_chunks: List of audio data chunks
            crossfade_ms: Crossfade duration between chunks

        Returns:
            Combined audio segment

        """
        if not audio_chunks:
            raise ValueError("No audio chunks to combine")

        # Load first chunk
        combined = AudioSegment.from_mp3(io.BytesIO(audio_chunks[0]))
        combined = self._normalize_audio(combined)

        # Append remaining chunks
        for chunk_data in audio_chunks[1:]:
            chunk = AudioSegment.from_mp3(io.BytesIO(chunk_data))
            chunk = self._normalize_audio(chunk)

            combined = combined.append(chunk, crossfade=crossfade_ms) if crossfade_ms > 0 else combined + chunk

        combined = combined.set_frame_rate(self.output_sample_rate)
        return combined.fade_in(1000).fade_out(1000)

    def _normalize_audio(self, audio: AudioSegment, target_dBFS: float = -20.0) -> AudioSegment:  # noqa: N803
        """Normalize audio levels

        Args:
            audio: Audio segment to normalize
            target_dBFS: Target decibels relative to full scale

        Returns:
            Normalized audio

        """
        change_in_dBFS = target_dBFS - audio.dBFS  # noqa: N806
        return audio.apply_gain(change_in_dBFS)

    async def add_background_music(self, voice_audio: bytes, music_path: str | None = None, music_volume: float = 0.1) -> bytes:
        """Add background music to voice audio

        Args:
            voice_audio: Main voice audio
            music_path: Path to background music file
            music_volume: Volume level for background music (0-1)

        Returns:
            Audio with background music

        """
        if not music_path:
            return voice_audio

        # 信頼境界外から `music_path` が来た場合の ffmpeg 任意ファイル読取・プロトコル悪用を防ぐ allow-list 検証。
        if not _is_safe_bgm_path(music_path):
            logger.warning("Refusing to load background music from disallowed path")
            return voice_audio

        try:
            # Load voice audio
            voice = AudioSegment.from_mp3(io.BytesIO(voice_audio))

            # Load and process background music
            music = AudioSegment.from_file(music_path)

            # Adjust music volume
            music = music - (20 * (1 - music_volume))  # Reduce volume

            # Loop music if shorter than voice
            if len(music) < len(voice):
                music = music * (len(voice) // len(music) + 1)

            # Trim music to match voice length
            music = music[: len(voice)]

            # Overlay music on voice
            combined = voice.overlay(music)

            # Export to bytes
            output_buffer = io.BytesIO()
            combined.export(output_buffer, format="mp3", bitrate=self.output_bitrate)

            return output_buffer.getvalue()

        except Exception as e:
            logger.error(f"Error adding background music: {str(e)}")
            # Return original audio on error
            return voice_audio

    async def save_to_file(self, audio_data: bytes, file_path: str) -> str:
        """Save audio data to a file (出力先は AUDIO_OUTPUT_DIRS 配下に限定)."""
        # 任意パス書き込み防止。AUDIO_OUTPUT_DIRS 配下のみ許可。
        if not _is_safe_output_path(file_path):
            raise PermissionError("Refusing to write outside of AUDIO_OUTPUT_DIRS")

        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "wb") as f:  # noqa: ASYNC230
                f.write(audio_data)

            logger.info(f"Audio saved to {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Error saving audio file: {str(e)}")
            raise

    def get_audio_info(self, audio_data: bytes) -> dict:
        """Get information about audio data

        Args:
            audio_data: Audio data to analyze

        Returns:
            Dictionary with audio information

        """
        try:
            audio = AudioSegment.from_mp3(io.BytesIO(audio_data))

            return {
                "duration_seconds": len(audio) / 1000.0,
                "frame_rate": audio.frame_rate,
                "channels": audio.channels,
                "sample_width": audio.sample_width,
                "max_dBFS": audio.max_dBFS,
                "dBFS": audio.dBFS,
                "rms": audio.rms,
            }
        except Exception as e:
            logger.error(f"Error getting audio info: {str(e)}")
            return {}
