import asyncio
from typing import Any, Awaitable, Annotated
import logging


__all__ = "wait_for_complete",

logger = logging.getLogger(__name__)


class _DummyTqdm:

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def update(self, *args, **kwargs):
        pass


def wait_for_complete(
        *coroutines: Awaitable[Any],
        progress: bool = False,
        ignore_exceptions: bool = False,
        description="Running coroutines",
        timeout_seconds: int = -1,
        fast_first: Annotated[bool, "Results are sorted by completion time"] = False,
) -> list[Any | Exception]:
    from tqdm import tqdm
    _tqdm = _DummyTqdm if not progress else tqdm

    async def __wrapper(coroutine: Awaitable[Any], pbar: tqdm) -> Any:
        try:
            return await coroutine
        except Exception as e:
            if logger.isEnabledFor(logging.DEBUG):
                logger.exception(f"Exception in coroutine: [{e}]")
            raise
        finally:
            pbar.update(1)

    async def __wait_for_tasks() -> list[Any]:
        with _tqdm(total=len(coroutines), desc=description) as pbar:
            coroutines_ = [__wrapper(coroutine, pbar) for coroutine in coroutines]
            if fast_first:
                result = []
                for c in asyncio.as_completed(coroutines_):
                    try:
                        result.append(await c)
                    except Exception as e:
                        result.append(e)
            else:
                result = await asyncio.gather(*coroutines_, return_exceptions=True)

            if ignore_exceptions:
                return [r for r in result if not isinstance(r, Exception)]
            return result

    loop = asyncio.get_event_loop()
    if timeout_seconds < 0:
        return loop.run_until_complete(__wait_for_tasks())
    else:
        return loop.run_until_complete(asyncio.wait_for(__wait_for_tasks(), timeout=timeout_seconds))
