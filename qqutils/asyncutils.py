import asyncio
from typing import Any, Awaitable
from tqdm import tqdm


__all__ = "wait_for_complete",


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
        description="Running coroutines"
) -> list[Any | Exception]:
    _tqdm = _DummyTqdm if not progress else tqdm

    async def __wrapper(coroutine: Awaitable[Any], pbar: tqdm) -> Any:
        try:
            return await coroutine
        finally:
            pbar.update(1)

    async def __wait_for_tasks() -> list[Any]:
        with _tqdm(total=len(coroutines), desc=description) as pbar:
            coroutines_ = [__wrapper(coroutine, pbar) for coroutine in coroutines]
            result = await asyncio.gather(*coroutines_, return_exceptions=True)
            if ignore_exceptions:
                return [r for r in result if not isinstance(r, Exception)]
            return result

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(__wait_for_tasks())
