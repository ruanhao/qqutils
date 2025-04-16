from qqutils.dbgutils import Timer, debug_timing
import time


@debug_timing
def _sleep(seconds):
    time.sleep(seconds)


def test_timer():
    with Timer("Sleep 1s"):
        time.sleep(1)
    _sleep(1)
