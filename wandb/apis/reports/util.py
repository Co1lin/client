from abc import ABC
from dataclasses import field
from typing import List

from wandb.apis.reports.validators import type_validate

UNDEFINED_TYPE = object()
NOT_SETABLE = None
NOT_DELABLE = None


def generate_name(length=12):
    # This implementation roughly based this snippet in core
    # https://github.com/wandb/core/blob/master/lib/js/cg/src/utils/string.ts#L39-L44

    import numpy as np

    rand = np.random.random()
    rand = int(str(rand)[2:])
    rand36 = np.base_repr(rand, 36)
    return rand36.lower()[:length]


def is_none(x):
    if isinstance(x, (list, tuple)):
        return all(v is None for v in x)
    else:
        return x is None or x == {}


class SubclassOnlyABC(ABC):
    def __new__(cls, *args, **kwargs):
        if cls.__bases__ == (SubclassOnlyABC,):
            raise TypeError(f"Abstract class {cls.__name__} cannot be instantiated")

        return super().__new__(cls)


def base_fget(self, instance, default=None):
    return instance.__dict__.get(self.name, default)


def base_fset(self, instance, value):
    instance.__dict__[self.name] = value


class Attr:
    """
    Like property, but with validators and optionally types.
    """

    def __init__(
        self,
        attr_type=UNDEFINED_TYPE,
        default=None,
        fget: callable = base_fget,
        fset: callable = base_fset,
        # fdel: callable = None,
        doc: str = None,
        validators: List[callable] = None,
    ):
        self.attr_type = attr_type
        self.default = default
        self.fget = fget
        self.fset = fset
        # self.fdel = fdel
        if validators is None:
            validators = []
        if not isinstance(validators, list):
            validators = [validators]
        self.validators = validators
        if self.attr_type is not UNDEFINED_TYPE:
            self.validators = [type_validate(attr_type)] + self.validators
        if doc is None and fget is not None:
            doc = fget.__doc__
        self.__doc__ = doc

    def __get__(self, instance, owner):
        if not instance:
            return self
        return self.fget(self, instance, self.default)

    def __set__(self, instance, value):
        if value is self:
            value = self.default
        if self.fset is None:
            raise AttributeError("Unsettable attr")
        self._validate(value)
        self.fset(self, instance, value)

    # def __delete__(self, instance):
    #     if self.fdel is None:
    #         raise AttributeError("Undeletable attr")
    #     return self.fdel(self, instance)

    def __set_name__(self, owner, name):
        self.name = name

    def _validate(self, value):
        for validator in self.validators:
            validator(self, value)


def attr(*args, repr=True, **kwargs):
    return field(default=Attr(*args, **kwargs), repr=repr)


# def sort_layouts(layout):
#     x = layout["x"] + layout["w"]
#     y = layout["y"] + layout["h"]
#     return y, x


# def sort_panels_by_layout(panels):
#     return sorted(panels, key=lambda p: sort_layouts(p.layout))


# class CollapsingList(UserList):
#     def __repr__(self):
#         if len(self) > 2:
#             items = self[:2]
#             ending = ", ..."
#         else:
#             items = self
#             ending = ""
#         return "[{}{}]".format(", ".join(repr(i) for i in items), ending)
