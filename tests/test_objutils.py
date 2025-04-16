import wrapt
from attrs import define, field
from qqutils.objutils import singleton
from qqutils.threadutils import submit_thread, wait_forever


class Wrapper(wrapt.ObjectProxy):

    def __getattribute__(self, name):
        if name == '__wrapped__':
            return super().__getattribute__(name)

        print(f"Accessing attribute: {name}")

        wrapped = super().__getattribute__('__wrapped__')
        return getattr(wrapped, name)

    def __str__(self):
        return f"Wrapped object: {self.__wrapped__}"


@define(slots=True, kw_only=True, order=True)
class MyObject:
    name: str = field(converter=str.lower, order=False)

    def say_hello(self):
        print(f"Hello, {self.name}!")


@singleton
class MySingletonObject:

    def __init__(self):
        self.name = "Jack"

    def say_hello(self):
        print(f"Hello, {self.name}!")


def test_singleton():
    objects = set()

    def __create_singleton():
        try:
            obj = MySingletonObject.instance()
            objects.add(obj)
            print(f"Created singleton object: {obj}")
        except Exception as e:
            print(f"Error creating singleton object: {e}")

    for i in range(32):
        submit_thread(__create_singleton)

    wait_forever()

    assert len(objects) == 1


def test_obj_proxy():
    my_obj = MyObject(name="Jack")
    wrapperd_obj = Wrapper(my_obj)
    print("Wrapped object:", wrapperd_obj)

    assert wrapperd_obj.name == "jack"
    wrapperd_obj.say_hello()

    my_obj2 = MyObject(name="Jill")
    wrapperd_obj.__wrapped__ = my_obj2

    assert wrapperd_obj.name == "jill"
    wrapperd_obj.say_hello()
