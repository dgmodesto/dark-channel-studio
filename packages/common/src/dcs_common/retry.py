import asyncio
from collections.abc import Awaitable, Callable


async def retry_async[T](
    fn: Callable[[], Awaitable[T]],
    *,
    attempts: int = 10,
    base_delay: float = 0.5,
    max_delay: float = 5.0,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> T:
    """Call fn until it succeeds, with exponential backoff; re-raise after the last attempt."""
    for attempt in range(1, attempts + 1):
        try:
            return await fn()
        except exceptions:
            if attempt == attempts:
                raise
            await asyncio.sleep(min(base_delay * 2 ** (attempt - 1), max_delay))
    raise RuntimeError("unreachable")
