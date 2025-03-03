"""Bucket of reusable internal utilities.

This should be reduced as much as possible with functions only used in one place, moved to that place.
"""
from __future__ import annotations as _annotations
import dataclasses
import keyword
import typing
import weakref
from collections import OrderedDict, defaultdict, deque
from copy import deepcopy
from itertools import zip_longest
from types import BuiltinFunctionType, CodeType, FunctionType, GeneratorType, LambdaType, ModuleType
from typing import Any, Mapping, TypeVar
from typing_extensions import TypeAlias, TypeGuard
from . import _repr, _typing_extra
if typing.TYPE_CHECKING:
    MappingIntStrAny: TypeAlias = 'typing.Mapping[int, Any] | typing.Mapping[str, Any]'
    AbstractSetIntStr: TypeAlias = 'typing.AbstractSet[int] | typing.AbstractSet[str]'
    from ..main import BaseModel
IMMUTABLE_NON_COLLECTIONS_TYPES: set[type[Any]] = {int, float, complex, str, bool, bytes, type, _typing_extra.NoneType, FunctionType, BuiltinFunctionType, LambdaType, weakref.ref, CodeType, ModuleType, NotImplemented.__class__, Ellipsis.__class__}
BUILTIN_COLLECTIONS: set[type[Any]] = {list, set, tuple, frozenset, dict, OrderedDict, defaultdict, deque}

def is_model_class(cls: Any) -> TypeGuard[type[BaseModel]]:
    """Returns true if cls is a _proper_ subclass of BaseModel, and provides proper type-checking,
    unlike raw calls to lenient_issubclass.
    """
    pass

def is_valid_identifier(identifier: str) -> bool:
    """Checks that a string is a valid identifier and not a Python keyword.
    :param identifier: The identifier to test.
    :return: True if the identifier is valid.
    """
    pass
KeyType = TypeVar('KeyType')
T = TypeVar('T')

def unique_list(input_list: list[T] | tuple[T, ...], *, name_factory: typing.Callable[[T], str]=str) -> list[T]:
    """Make a list unique while maintaining order.
    We update the list if another one with the same name is set
    (e.g. model validator overridden in subclass).
    """
    pass

class ValueItems(_repr.Representation):
    """Class for more convenient calculation of excluded or included fields on values."""
    __slots__ = ('_items', '_type')

    def __init__(self, value: Any, items: AbstractSetIntStr | MappingIntStrAny) -> None:
        items = self._coerce_items(items)
        if isinstance(value, (list, tuple)):
            items = self._normalize_indexes(items, len(value))
        self._items: MappingIntStrAny = items

    def is_excluded(self, item: Any) -> bool:
        """Check if item is fully excluded.

        :param item: key or index of a value
        """
        pass

    def is_included(self, item: Any) -> bool:
        """Check if value is contained in self._items.

        :param item: key or index of value
        """
        pass

    def for_element(self, e: int | str) -> AbstractSetIntStr | MappingIntStrAny | None:
        """:param e: key or index of element on value
        :return: raw values for element if self._items is dict and contain needed element
        """
        pass

    def _normalize_indexes(self, items: MappingIntStrAny, v_length: int) -> dict[int | str, Any]:
        """:param items: dict or set of indexes which will be normalized
        :param v_length: length of sequence indexes of which will be

        >>> self._normalize_indexes({0: True, -2: True, -1: True}, 4)
        {0: True, 2: True, 3: True}
        >>> self._normalize_indexes({'__all__': True}, 4)
        {0: True, 1: True, 2: True, 3: True}
        """
        pass

    @classmethod
    def merge(cls, base: Any, override: Any, intersect: bool=False) -> Any:
        """Merge a `base` item with an `override` item.

        Both `base` and `override` are converted to dictionaries if possible.
        Sets are converted to dictionaries with the sets entries as keys and
        Ellipsis as values.

        Each key-value pair existing in `base` is merged with `override`,
        while the rest of the key-value pairs are updated recursively with this function.

        Merging takes place based on the "union" of keys if `intersect` is
        set to `False` (default) and on the intersection of keys if
        `intersect` is set to `True`.
        """
        pass

    def __repr_args__(self) -> _repr.ReprArgs:
        return [(None, self._items)]
if typing.TYPE_CHECKING:
else:

    class ClassAttribute:
        """Hide class attribute from its instances."""
        __slots__ = ('name', 'value')

        def __init__(self, name: str, value: Any) -> None:
            self.name = name
            self.value = value

        def __get__(self, instance: Any, owner: type[Any]) -> None:
            if instance is None:
                return self.value
            raise AttributeError(f'{self.name!r} attribute of {owner.__name__!r} is class-only')
Obj = TypeVar('Obj')

def smart_deepcopy(obj: Obj) -> Obj:
    """Return type as is for immutable built-in types
    Use obj.copy() for built-in empty collections
    Use copy.deepcopy() for non-empty collections and unknown objects.
    """
    pass
_SENTINEL = object()

def all_identical(left: typing.Iterable[Any], right: typing.Iterable[Any]) -> bool:
    """Check that the items of `left` are the same objects as those in `right`.

    >>> a, b = object(), object()
    >>> all_identical([a, b, a], [a, b, a])
    True
    >>> all_identical([a, b, [a]], [a, b, [a]])  # new list object, while "equal" is not "identical"
    False
    """
    pass

@dataclasses.dataclass(frozen=True)
class SafeGetItemProxy:
    """Wrapper redirecting `__getitem__` to `get` with a sentinel value as default

    This makes is safe to use in `operator.itemgetter` when some keys may be missing
    """
    __slots__ = ('wrapped',)
    wrapped: Mapping[str, Any]

    def __getitem__(self, key: str, /) -> Any:
        return self.wrapped.get(key, _SENTINEL)
    if typing.TYPE_CHECKING:

        def __contains__(self, key: str, /) -> bool:
            return self.wrapped.__contains__(key)