import functools
import logging
from collections.abc import Callable
from typing import Any, TypeVar

from src.domain.podcast.exceptions import PodcastException

F = TypeVar("F", bound=Callable[..., Any])

logger = logging.getLogger(__name__)


def handle_podcast_errors(error_message: str | None = None) -> Callable[[F], F]:
    """Decorator to handle common podcast use case errors

    Args:
        error_message: Custom error message prefix

    Returns:
        Decorated function with error handling

    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            try:
                return await func(*args, **kwargs)
            except PodcastException:
                # Re-raise domain exceptions as-is
                raise
            except Exception as e:
                # Log unexpected errors and re-raise
                prefix = error_message or f"Error in {func.__name__}"
                logger.error(f"{prefix}: {str(e)}")
                raise

        return wrapper  # type: ignore

    return decorator


def log_use_case_execution[F: Callable[..., Any]](func: F) -> F:
    """Decorator to log use case execution

    Args:
        func: Function to decorate

    Returns:
        Decorated function with logging

    """

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
        logger.info(f"Executing {func.__name__}")
        try:
            result = await func(*args, **kwargs)
            logger.info(f"Successfully completed {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Failed to execute {func.__name__}: {str(e)}")
            raise

    return wrapper  # type: ignore
