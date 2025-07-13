"""Configuration for podcast use cases"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PodcastConfig:
    """Configuration settings for podcast generation"""

    # Chapter extraction settings
    max_chapters: int = 15

    # Script generation settings
    target_words: int = 1000
    min_script_turns: int = 6
    max_script_turns: int = 30
    max_retries_script_generation: int = 3
    initial_temperature: float = 0.7
    temperature_increment: float = 0.1
    max_text_length_per_turn: int = 500

    # Summarization settings
    max_concurrent_summarization_requests: int = 2
    chapter_summary_chunk_size: int = 5
    chapter_content_clip_lengths: tuple[int, ...] = (6000, 4000, 2000)
    chapter_summary_max_tokens: tuple[int, ...] = (400, 350, 300)
    partial_summary_max_tokens: int = 800
    final_summary_max_tokens: int = 1200
    summarization_temperature: float = 0.3

    # Audio synthesis settings
    max_chars_per_tts_request: int = 5000
    audio_synthesis_batch_size: int = 10

    # General settings
    min_speaker_participation: float = 0.2  # Each speaker should have at least 20% of turns
