import inspect
from typing import List
from attrs import define, field, validators, setters, asdict, astuple


def get_source(obj) -> str:
    return inspect.getsource(obj)


@define(slots=True, kw_only=True, order=True)
class __User:
    """
Order of Execution
    1. __attrs_pre_init__ (if present on current class)
    2. For each attribute, in the order it was declared:
      2.1 default factory
      2.2 converter
    3. all validators
    4. __attrs_post_init__ (if present on current class)
    """
    # id: int = field(validator=lambda x: x > 0)
    id: int = field(
        default=-1,
        validator=validators.instance_of(int),
        on_setattr=setters.frozen,
        order=False
    )
    name: str = field(converter=str.lower, order=False)
    email: str = field(converter=str.lower, default='', order=False)
    age: int = field(default=0, validator=validators.instance_of(int), order=int)
    password: str = field(default='', validator=validators.instance_of(str), order=False, repr=lambda value: '*' * len(value))
    comments: List[str] = field(factory=list, order=False, hash=False)

    def __attrs_post_init__(self):
        """https://www.attrs.org/en/stable/init.html#hooking-yourself-into-initialization"""
        print(f"Post init: user id={self.id} created")


def __test():
    for fname, fn in inspect.getmembers(__User, inspect.isfunction):
        source = inspect.getsource(fn)
        first_line = source.splitlines()[0]
        prefix_whitespace_len = len(first_line) - len(first_line.lstrip())
        print('\n'.join([line[prefix_whitespace_len:] for line in source.splitlines()]))
        print()

    try:
        __User(id="1")
        assert False, "Should have raised TypeError"
    except TypeError:
        pass
    assert __User(name="John").id == -1, "Should have defaulted id to -1"
    assert __User(name="John").name == "john", "Should have converted name to lower case"
    try:
        __User(name="John").id = 1
        assert False, "Should have raised AttributeError"
    except AttributeError:
        pass
    assert '***' in str(__User(id=1, name="John", email="abc@test.com", password='123')), "Should have excluded email from repr"
    print(__User(id=1, name="John", email="abc@test.com", password='123'))

    assert __User(id=1, name="John", email="", age=20) > __User(id=2, name="Mary", email="", age=15), "Should have compared by age"
    print(astuple(__User(id=1, name="John", email="", age=20, password="123456")))
    print(asdict(__User(id=1, name="John", email="", age=20, password="123456")))


if __name__ == '__main__':
    __test()
