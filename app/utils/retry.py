import logging
import time
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger(__name__)


def retry(
    max_attempts: int = 3, backoff: list[int] | None = None
) -> Callable[..., Any]:
    """リトライデコレーター（指数バックオフ）"""
    if backoff is None:
        backoff = [1, 2, 4]

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    sleep_time = backoff[min(attempt, len(backoff) - 1)]
                    logger.warning(
                        "Retry %d/%d after %ds: %s", attempt + 1, max_attempts, sleep_time, e
                    )
                    time.sleep(sleep_time)

        return wrapper

    return decorator
