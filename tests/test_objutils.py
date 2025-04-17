import wrapt
import time
from attrs import define, field
from typing import Any
from functools import wraps
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


@define(kw_only=True, order=True)
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


class ObjectWrapper(wrapt.ObjectProxy):

    def __init__(self, wrapped):
        super(ObjectWrapper, self).__init__(wrapped)

    def __setattr__(self, name, value):
        if name == '__wrapped__':
            return super().__setattr__(name, value)

        super().__getattribute__('on_setattr')(name, value)
        wrapped = super().__getattribute__('__wrapped__')
        setattr(wrapped, name, value)
        super().__getattribute__('post_setattr')(name, value)

    def __getattribute__(self, name):
        if name == '__wrapped__':
            return super().__getattribute__(name)

        super().__getattribute__('on_getattr')(name)
        wrapped = super().__getattribute__('__wrapped__')
        try:
            v = getattr(wrapped, name)
            return super().__getattribute__('post_getattr')(name, v)
        except AttributeError as e:
            super().__getattribute__('on_getattr_error')(name, e)
            raise e

    def on_getattr(self, name: str) -> None:
        print(f"Accessing attribute: {name}")

    def on_getattr_error(self, name: str, error: AttributeError) -> None:
        print(f"Error accessing attribute '{name}': {error}")

    def post_getattr(self, name: str, value: Any) -> Any:
        print(f"Post-get attribute '{name}' with value: {value}")
        return value

    def on_setattr(self, name: str, value: Any) -> None:
        print(f"Setting attribute '{name}' to value: {value}")

    def post_setattr(self, name: str, value: Any) -> None:
        print(f"Post-set attribute '{name}' with value: {value}")


def test_object_wrapper():

    class MyObject:
        def __init__(self, name):
            self.name = name

        def __str__(self):
            return f"MyObject(name={self.name})"

    raw_obj = MyObject(name='Ross')
    obj = ObjectWrapper(raw_obj)
    obj.a = 1
    obj.a
    try:
        obj.b
    except AttributeError:
        pass

    obj.__wrapped__ = MyObject(name='Rachel')
    assert obj.name == 'Rachel'


# this version is more simple then ObjectWrapper
class MonitoringProxy(wrapt.ObjectProxy):

    def __init__(self, wrapped):
        super().__init__(wrapped)
        self._self_value = "anything you want"  # attr for Proxy itself, not for wrapped

    def __getattr__(self, name):
        attr = super().__getattr__(name)

        if callable(attr):
            @wraps(attr)
            def wrapper(*args, **kwargs):
                start = time.time()
                print(f"[LOG] Calling {name} with args={args}, kwargs={kwargs}")
                try:
                    result = attr(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start
                    print(f"[LOG] {name} took {duration:.4f} seconds")
            return wrapper
        else:
            return attr


def test_monitoring_proxy():

    class MyObject:
        def __init__(self, name):
            self.name = name

        def __str__(self):
            return f"MyObject(name={self.name})"

        def say_hello(self):
            print(f"Hello, my name is {self.name}!")

    raw_obj = MyObject(name='Ross')
    obj = MonitoringProxy(raw_obj)
    obj.a = 1
    obj.a
    try:
        obj.b
    except AttributeError:
        pass

    obj.__wrapped__ = MyObject(name='Rachel')
    assert obj.name == 'Rachel'
    print("func name:", obj.say_hello.__name__)
    obj.say_hello()
