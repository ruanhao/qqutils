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


def wait_for_complete(*coroutines: Awaitable[Any], progress: bool = False) -> list[Any | Exception]:
    _tqdm = _DummyTqdm if not progress else tqdm

    async def __wait_for_tasks() -> list[Any]:
        result = []
        with _tqdm(total=len(coroutines), desc="Running coroutines") as pbar:
            for future in asyncio.as_completed(coroutines):
                try:
                    result.append(await future)
                except Exception as e:
                    result.append(e)
                pbar.update(1)
        return result

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(__wait_for_tasks())
