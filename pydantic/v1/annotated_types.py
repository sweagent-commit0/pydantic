import sys
from typing import TYPE_CHECKING, Any, Dict, FrozenSet, NamedTuple, Type
from pydantic.v1.fields import Required
from pydantic.v1.main import BaseModel, create_model
from pydantic.v1.typing import is_typeddict, is_typeddict_special
if TYPE_CHECKING:
    from typing_extensions import TypedDict
if sys.version_info < (3, 11):

def create_model_from_typeddict(typeddict_cls: Type['TypedDict'], **kwargs: Any) -> Type['BaseModel']:
    """
    Create a `BaseModel` based on the fields of a `TypedDict`.
    Since `typing.TypedDict` in Python 3.8 does not store runtime information about optional keys,
    we raise an error if this happens (see https://bugs.python.org/issue38834).
    """
    pass

def create_model_from_namedtuple(namedtuple_cls: Type['NamedTuple'], **kwargs: Any) -> Type['BaseModel']:
    """
    Create a `BaseModel` based on the fields of a named tuple.
    A named tuple can be created with `typing.NamedTuple` and declared annotations
    but also with `collections.namedtuple`, in this case we consider all fields
    to have type `Any`.
    """
    pass