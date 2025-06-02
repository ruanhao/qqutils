from qqutils.dbgutils import Timer, debug_timing, simple_timing
import time


@debug_timing
def _sleep(seconds):
    time.sleep(seconds)


def test_timer():
    with Timer("Sleep 1s"):
        time.sleep(1)
    _sleep(1)


def test_simple_timing():

    @simple_timing
    def __sample_function():
        time.sleep(1)
        return "Hello, World!"

    __sample_function()
