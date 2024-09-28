"""Private logic related to fields (the `Field()` function and `FieldInfo` class), and arguments to `Annotated`."""
from __future__ import annotations as _annotations
import dataclasses
import sys
import warnings
from copy import copy
from functools import lru_cache
from typing import TYPE_CHECKING, Any
from pydantic_core import PydanticUndefined
from pydantic.errors import PydanticUserError
from . import _typing_extra
from ._config import ConfigWrapper
from ._docs_extraction import extract_docstrings_from_cls
from ._repr import Representation
from ._typing_extra import get_cls_type_hints_lenient, get_type_hints, is_classvar, is_finalvar
if TYPE_CHECKING:
    from annotated_types import BaseMetadata
    from ..fields import FieldInfo
    from ..main import BaseModel
    from ._dataclasses import StandardDataclass
    from ._decorators import DecoratorInfos

def get_type_hints_infer_globalns(obj: Any, localns: dict[str, Any] | None=None, include_extras: bool=False) -> dict[str, Any]:
    """Gets type hints for an object by inferring the global namespace.

    It uses the `typing.get_type_hints`, The only thing that we do here is fetching
    global namespace from `obj.__module__` if it is not `None`.

    Args:
        obj: The object to get its type hints.
        localns: The local namespaces.
        include_extras: Whether to recursively include annotation metadata.

    Returns:
        The object type hints.
    """
    pass

class PydanticMetadata(Representation):
    """Base class for annotation markers like `Strict`."""
    __slots__ = ()

def pydantic_general_metadata(**metadata: Any) -> BaseMetadata:
    """Create a new `_PydanticGeneralMetadata` class with the given metadata.

    Args:
        **metadata: The metadata to add.

    Returns:
        The new `_PydanticGeneralMetadata` class.
    """
    pass

@lru_cache(maxsize=None)
def _general_metadata_cls() -> type[BaseMetadata]:
    """Do it this way to avoid importing `annotated_types` at import time."""
    pass

def collect_model_fields(cls: type[BaseModel], bases: tuple[type[Any], ...], config_wrapper: ConfigWrapper, types_namespace: dict[str, Any] | None, *, typevars_map: dict[Any, Any] | None=None) -> tuple[dict[str, FieldInfo], set[str]]:
    """Collect the fields of a nascent pydantic model.

    Also collect the names of any ClassVars present in the type hints.

    The returned value is a tuple of two items: the fields dict, and the set of ClassVar names.

    Args:
        cls: BaseModel or dataclass.
        bases: Parents of the class, generally `cls.__bases__`.
        config_wrapper: The config wrapper instance.
        types_namespace: Optional extra namespace to look for types in.
        typevars_map: A dictionary mapping type variables to their concrete types.

    Returns:
        A tuple contains fields and class variables.

    Raises:
        NameError:
            - If there is a conflict between a field name and protected namespaces.
            - If there is a field other than `root` in `RootModel`.
            - If a field shadows an attribute in the parent model.
    """
    pass

def collect_dataclass_fields(cls: type[StandardDataclass], types_namespace: dict[str, Any] | None, *, typevars_map: dict[Any, Any] | None=None, config_wrapper: ConfigWrapper | None=None) -> dict[str, FieldInfo]:
    """Collect the fields of a dataclass.

    Args:
        cls: dataclass.
        types_namespace: Optional extra namespace to look for types in.
        typevars_map: A dictionary mapping type variables to their concrete types.
        config_wrapper: The config wrapper instance.

    Returns:
        The dataclass fields.
    """
    pass