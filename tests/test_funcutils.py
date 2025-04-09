from qqutils.funcutils import synchronized
from qqutils.threadutils import submit_thread, wait_forever
import threading

SUM = 0


@synchronized
def increment():
    global SUM
    print(threading.current_thread().name, "incrementing ...")
    SUM += 1
    return SUM


class Adder:

    def __init__(self):
        self.added = False
        self.value = 0

    # @synchronized
    def increment(self):

        if self.added:
            return self.value

        print(threading.current_thread().name, "incrementing ...")
        self.value += 1
        self.added = True
        return self.value

    @synchronized
    def add(self, x):
        if self.added:
            return self.value

        print(threading.current_thread().name, "adding ...")
        self.value += x
        self.added = True
        return self.value


def test_synchronized_func():
    count = 100
    for i in range(count):
        submit_thread(increment)

    wait_forever()
    print("[synchronized] result:", SUM)  # == 1
    assert SUM == count, "synchronized failed"


def test_synchronized_class():
    adder = Adder()
    count = 100
    for i in range(count):
        submit_thread(adder.increment)

    wait_forever()
    print("[non synchronized] result:", adder.value)  # != 1

    adder = Adder()
    for i in range(count):
        submit_thread(adder.add, 1)

    wait_forever()
    print("[synchronized] result:", adder.value)  # == 1
    assert adder.value == 1, "synchronized failed"
