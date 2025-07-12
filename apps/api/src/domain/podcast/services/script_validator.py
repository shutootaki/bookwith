import logging

from src.domain.podcast.value_objects.podcast_script import PodcastScript

logger = logging.getLogger(__name__)


class ScriptValidator:
    """Domain service for validating podcast scripts"""

    @staticmethod
    def validate_for_tts(script: PodcastScript) -> None:
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

    @staticmethod
    def should_use_chunking(script: PodcastScript, max_chars_per_request: int = 5000) -> bool:
        """Determine if script should be synthesized in chunks

        Args:
            script: PodcastScript to check
            max_chars_per_request: Maximum characters per TTS request

        Returns:
            True if chunking should be used

        """
        return script.get_total_length() > max_chars_per_request

    @staticmethod
    def estimate_audio_duration(script: PodcastScript) -> float:
        """Estimate the duration of synthesized audio

        Args:
            script: PodcastScript to estimate

        Returns:
            Estimated duration in seconds

        """
        # Rough estimation: 150 words per minute average speaking rate
        # Average word length: 5 characters + 1 space
        total_chars = script.get_total_length()
        estimated_words = total_chars / 6
        estimated_minutes = estimated_words / 150

        return estimated_minutes * 60
