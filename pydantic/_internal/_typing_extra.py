"""Logic for interacting with type annotations, mostly extensions, shims and hacks to wrap python's typing module."""
from __future__ import annotations as _annotations
import dataclasses
import re
import sys
import types
import typing
import warnings
from collections.abc import Callable
from functools import partial
from types import GetSetDescriptorType
from typing import TYPE_CHECKING, Any, Final
from typing_extensions import Annotated, Literal, TypeAliasType, TypeGuard, deprecated, get_args, get_origin
if TYPE_CHECKING:
    from ._dataclasses import StandardDataclass
try:
    from typing import _TypingBase
except ImportError:
    from typing import _Final as _TypingBase
typing_base = _TypingBase
if sys.version_info < (3, 9):
    TypingGenericAlias = ()
else:
    from typing import GenericAlias as TypingGenericAlias
if sys.version_info < (3, 11):
    from typing_extensions import NotRequired, Required
else:
    from typing import NotRequired, Required
if sys.version_info < (3, 10):
    WithArgsTypes = (TypingGenericAlias,)
else:
    WithArgsTypes = (typing._GenericAlias, types.GenericAlias, types.UnionType)
if sys.version_info < (3, 10):
    NoneType = type(None)
    EllipsisType = type(Ellipsis)
else:
    from types import NoneType as NoneType
LITERAL_TYPES: set[Any] = {Literal}
if hasattr(typing, 'Literal'):
    LITERAL_TYPES.add(typing.Literal)
DEPRECATED_TYPES: tuple[Any, ...] = (deprecated,) if isinstance(deprecated, type) else ()
if hasattr(warnings, 'deprecated'):
    DEPRECATED_TYPES = (*DEPRECATED_TYPES, warnings.deprecated)
NONE_TYPES: tuple[Any, ...] = (None, NoneType, *(tp[None] for tp in LITERAL_TYPES))
TypeVarType = Any

def all_literal_values(type_: type[Any]) -> list[Any]:
    """This method is used to retrieve all Literal values as
    Literal can be used recursively (see https://www.python.org/dev/peps/pep-0586)
    e.g. `Literal[Literal[Literal[1, 2, 3], "foo"], 5, None]`.
    """
    pass

def is_namedtuple(type_: type[Any]) -> bool:
    """Check if a given class is a named tuple.
    It can be either a `typing.NamedTuple` or `collections.namedtuple`.
    """
    pass
test_new_type = typing.NewType('test_new_type', str)

def is_new_type(type_: type[Any]) -> bool:
    """Check whether type_ was created using typing.NewType.

    Can't use isinstance because it fails <3.10.
    """
    pass

def _check_finalvar(v: type[Any] | None) -> bool:
    """Check if a given type is a `typing.Final` type."""
    pass

def parent_frame_namespace(*, parent_depth: int=2) -> dict[str, Any] | None:
    """We allow use of items in parent namespace to get around the issue with `get_type_hints` only looking in the
    global module namespace. See https://github.com/pydantic/pydantic/issues/2678#issuecomment-1008139014 -> Scope
    and suggestion at the end of the next comment by @gvanrossum.

    WARNING 1: it matters exactly where this is called. By default, this function will build a namespace from the
    parent of where it is called.

    WARNING 2: this only looks in the parent namespace, not other parents since (AFAIK) there's no way to collect a
    dict of exactly what's in scope. Using `f_back` would work sometimes but would be very wrong and confusing in many
    other cases. See https://discuss.python.org/t/is-there-a-way-to-access-parent-nested-namespaces/20659.
    """
    pass

def get_cls_type_hints_lenient(obj: Any, globalns: dict[str, Any] | None=None) -> dict[str, Any]:
    """Collect annotations from a class, including those from parent classes.

    Unlike `typing.get_type_hints`, this function will not error if a forward reference is not resolvable.
    """
    pass

def eval_type_lenient(value: Any, globalns: dict[str, Any] | None=None, localns: dict[str, Any] | None=None) -> Any:
    """Behaves like typing._eval_type, except it won't raise an error if a forward reference can't be resolved."""
    pass

def eval_type_backport(value: Any, globalns: dict[str, Any] | None=None, localns: dict[str, Any] | None=None, type_params: tuple[Any] | None=None) -> Any:
    """Like `typing._eval_type`, but falls back to the `eval_type_backport` package if it's
    installed to let older Python versions use newer typing features.
    Specifically, this transforms `X | Y` into `typing.Union[X, Y]`
    and `list[X]` into `typing.List[X]` etc. (for all the types made generic in PEP 585)
    if the original syntax is not supported in the current Python version.
    """
    pass

def get_function_type_hints(function: Callable[..., Any], *, include_keys: set[str] | None=None, types_namespace: dict[str, Any] | None=None) -> dict[str, Any]:
    """Like `typing.get_type_hints`, but doesn't convert `X` to `Optional[X]` if the default value is `None`, also
    copes with `partial`.
    """
    pass
if sys.version_info < (3, 9, 8) or (3, 10) <= sys.version_info < (3, 10, 1):

    def _make_forward_ref(arg: Any, is_argument: bool=True, *, is_class: bool=False) -> typing.ForwardRef:
        """Wrapper for ForwardRef that accounts for the `is_class` argument missing in older versions.
        The `module` argument is omitted as it breaks <3.9.8, =3.10.0 and isn't used in the calls below.

        See https://github.com/python/cpython/pull/28560 for some background.
        The backport happened on 3.9.8, see:
        https://github.com/pydantic/pydantic/discussions/6244#discussioncomment-6275458,
        and on 3.10.1 for the 3.10 branch, see:
        https://github.com/pydantic/pydantic/issues/6912

        Implemented as EAFP with memory.
        """
        pass
else:
    _make_forward_ref = typing.ForwardRef
if sys.version_info >= (3, 10):
    get_type_hints = typing.get_type_hints
else:
    '\n    For older versions of python, we have a custom implementation of `get_type_hints` which is a close as possible to\n    the implementation in CPython 3.10.8.\n    '

    @typing.no_type_check
    def get_type_hints(obj: Any, globalns: dict[str, Any] | None=None, localns: dict[str, Any] | None=None, include_extras: bool=False) -> dict[str, Any]:
        """Taken verbatim from python 3.10.8 unchanged, except:
        * type annotations of the function definition above.
        * prefixing `typing.` where appropriate
        * Use `_make_forward_ref` instead of `typing.ForwardRef` to handle the `is_class` argument.

        https://github.com/python/cpython/blob/aaaf5174241496afca7ce4d4584570190ff972fe/Lib/typing.py#L1773-L1875

        DO NOT CHANGE THIS METHOD UNLESS ABSOLUTELY NECESSARY.
        ======================================================

        Return type hints for an object.

        This is often the same as obj.__annotations__, but it handles
        forward references encoded as string literals, adds Optional[t] if a
        default value equal to None is set and recursively replaces all
        'Annotated[T, ...]' with 'T' (unless 'include_extras=True').

        The argument may be a module, class, method, or function. The annotations
        are returned as a dictionary. For classes, annotations include also
        inherited members.

        TypeError is raised if the argument is not of a type that can contain
        annotations, and an empty dictionary is returned if no annotations are
        present.

        BEWARE -- the behavior of globalns and localns is counterintuitive
        (unless you are familiar with how eval() and exec() work).  The
        search order is locals first, then globals.

        - If no dict arguments are passed, an attempt is made to use the
          globals from obj (or the respective module's globals for classes),
          and these are also used as the locals.  If the object does not appear
          to have globals, an empty dictionary is used.  For classes, the search
          order is globals first then locals.

        - If one dict argument is passed, it is used for both globals and
          locals.

        - If two dict arguments are passed, they specify globals and
          locals, respectively.
        """
        pass
if sys.version_info >= (3, 10):

def is_self_type(tp: Any) -> bool:
    """Check if a given class is a Self type (from `typing` or `typing_extensions`)"""
    pass