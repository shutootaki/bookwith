"""Helper functions for building MultiSpeakerMarkup"""

from google.cloud import texttospeech_v1beta1 as tts

from src.domain.podcast.value_objects.podcast_script import PodcastScript, ScriptTurn


def build_multi_speaker_markup(script: PodcastScript) -> tts.MultiSpeakerMarkup:
    """Build MultiSpeakerMarkup from PodcastScript domain object

    Args:
        script: PodcastScript containing dialogue turns

    Returns:
        MultiSpeakerMarkup object for TTS synthesis

    """
    turns = []

    for turn in script.turns:
        markup_turn = tts.MultiSpeakerMarkup.Turn(text=turn.text, speaker=str(turn.speaker))
        turns.append(markup_turn)

    return tts.MultiSpeakerMarkup(turns=turns)


def script_to_dict_list(script: PodcastScript) -> list[dict[str, str]]:
    """Convert PodcastScript to list of dictionaries for TTS processing

    Args:
        script: PodcastScript domain object

    Returns:
        List of dictionaries with 'speaker' and 'text' keys

    """
    return [{"speaker": str(turn.speaker), "text": turn.text} for turn in script.turns]


def validate_script_for_tts(script: PodcastScript) -> bool:
    """Validate that a PodcastScript is suitable for TTS synthesis

    Args:
        script: PodcastScript to validate

    Returns:
        True if valid

    Raises:
        ValueError: If script is invalid for TTS

    """
    if not script.turns:
        raise ValueError("Script has no dialogue turns")

    # Check that we only have two speakers (R and S)
    speakers = {str(turn.speaker) for turn in script.turns}
    if speakers != {"R", "S"}:
        raise ValueError(f"Script must contain exactly speakers R and S, found: {speakers}")

    # Check character limits
    total_chars = script.get_total_length()
    if total_chars == 0:
        raise ValueError("Script has no text content")

    # Check individual turn lengths
    for i, turn in enumerate(script.turns):
        if len(turn.text) > 5000:
            raise ValueError(f"Turn {i} exceeds 5000 character limit")
        if not turn.text.strip():
            raise ValueError(f"Turn {i} has empty text")

    return True


def split_script_for_synthesis(script: PodcastScript, max_chars: int = 5000) -> list[list[ScriptTurn]]:
    """Split a script into chunks that fit within TTS character limits

    Args:
        script: PodcastScript to split
        max_chars: Maximum characters per chunk

    Returns:
        List of script turn chunks

    """
    chunks = []
    current_chunk: list[ScriptTurn] = []
    current_length = 0

    for turn in script.turns:
        turn_length = len(turn.text)

        # If a single turn is too long, we need to handle it specially
        if turn_length > max_chars:
            # Save current chunk if it has content
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                current_length = 0

            # Split the long turn (this is a simplified approach)
            # In production, you'd want smarter text splitting
            text_chunks = [turn.text[i : i + max_chars] for i in range(0, turn_length, max_chars)]

            for text_chunk in text_chunks:
                chunk_turn = ScriptTurn(speaker=turn.speaker, text=text_chunk)
                chunks.append([chunk_turn])
        else:
            # Normal case: add turn to current chunk
            if current_length + turn_length > max_chars and current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                current_length = 0

            current_chunk.append(turn)
            current_length += turn_length

    # Don't forget the last chunk
    if current_chunk:
        chunks.append(current_chunk)

    return chunks
