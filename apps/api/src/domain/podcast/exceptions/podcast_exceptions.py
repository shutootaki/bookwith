class PodcastException(Exception):  # noqa: N818
    """Base exception for podcast domain"""


class PodcastNotFoundError(PodcastException):
    """Raised when a podcast is not found"""

    def __init__(self, podcast_id: str) -> None:
        super().__init__(f"Podcast with id {podcast_id} not found")
        self.podcast_id = podcast_id


class PodcastAlreadyExistsError(PodcastException):
    """Raised when trying to create a podcast that already exists"""

    def __init__(self, book_id: str, user_id: str) -> None:
        super().__init__(f"Podcast already exists for book {book_id} and user {user_id}")
        self.book_id = book_id
        self.user_id = user_id


class PodcastGenerationError(PodcastException):
    """Raised when podcast generation fails"""

    def __init__(self, message: str) -> None:
        super().__init__(f"Podcast generation failed: {message}")


class PodcastInvalidStatusError(PodcastException):
    """Raised when trying to perform an operation with invalid status"""

    def __init__(self, current_status: str, operation: str) -> None:
        super().__init__(f"Cannot {operation} podcast with status {current_status}")
        self.current_status = current_status
        self.operation = operation


class PodcastScriptGenerationError(PodcastException):
    """Raised when script generation fails"""

    def __init__(self, message: str) -> None:
        super().__init__(f"Script generation failed: {message}")


class PodcastAudioSynthesisError(PodcastException):
    """Raised when audio synthesis fails"""

    def __init__(self, message: str) -> None:
        super().__init__(f"Audio synthesis failed: {message}")


class PodcastStorageError(PodcastException):
    """Raised when storage operation fails"""

    def __init__(self, message: str) -> None:
        super().__init__(f"Storage operation failed: {message}")
