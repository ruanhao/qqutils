from qqutils.asyncutils import wait_for_complete
import asyncio
import time


async def sleep(seconds: int) -> str:
    s = time.time()
    await asyncio.sleep(seconds)
    return f"Slept for {time.time() - s} seconds"


async def throw_error():
    raise ValueError("This is a test error")


def test_wait_for_complete():
    s = time.time()
    results = wait_for_complete(
        sleep(1),
        sleep(1),
        sleep(1),
        sleep(1),
        sleep(1),
    )
    e = time.time()
    assert len(results) == 5, f"Expected 5 results, got {len(results)}"
    assert e - s < 2, f"Expected less than 2 seconds, but took {e - s} seconds"
    print(results)


def test_wait_for_complete_case_error():
    results = wait_for_complete(
        sleep(1),
        sleep(2),
        throw_error(),
        sleep(3),
        sleep(4),
        progress=True,
    )
    print(results)
    assert len(results) == 5, f"Expected 5 results, got {len(results)}"
    assert isinstance(results[2], ValueError), "Expected an exception for the third task"


def test_wait_for_complete_case_ignore_error():
    results = wait_for_complete(
        sleep(1),
        sleep(2),
        throw_error(),
        sleep(3),
        sleep(4),
        progress=True,
        ignore_exceptions=True,
    )
    print(results)
    assert len(results) == 4, f"Expected 4 results, got {len(results)}"
    for result in results:
        assert not isinstance(result, Exception), "Expected no exceptions in results"
