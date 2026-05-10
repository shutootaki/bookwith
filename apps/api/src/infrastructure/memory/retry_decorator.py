"""再試行デコレータユーティリティ.

H-09 補強:
- 副作用を持つ処理（OpenAI Embeddings 課金、Weaviate insert）に retry を付けると
  再課金 / 重複 insert の元になる。`idempotent` フラグを False にした処理は再試行しない。
- `non_retryable_exceptions` を渡せる形にして、認可エラー等は再試行しない。
"""

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


def retry_on_error(
    max_retries: int = 3,
    initial_delay: int = 1,
    backoff_factor: int = 2,
    *,
    idempotent: bool = True,
    non_retryable_exceptions: tuple[type[BaseException], ...] = (),
) -> Callable:
    """エラー発生時に再試行するデコレータ.

    Args:
        max_retries: 最大再試行回数
        initial_delay: 初回遅延秒数
        backoff_factor: 指数バックオフの倍率
        idempotent: False の場合、副作用を伴う処理として再試行しない
        non_retryable_exceptions: これらの例外は即座に伝播させる

    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            if not idempotent:
                # H-09: 冪等でない処理は retry しない。失敗時にそのまま伝播。
                return func(*args, **kwargs)

            retries = 0
            delay = initial_delay
            while True:
                try:
                    return func(*args, **kwargs)
                except non_retryable_exceptions:
                    raise
                except Exception as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"最大再試行回数 ({max_retries}) に達しました: {str(e)}")
                        raise
                    logger.warning(f"操作失敗、{delay}秒後に再試行 ({retries}/{max_retries}): {str(e)}")
                    time.sleep(delay)
                    delay *= backoff_factor

        return wrapper

    return decorator
