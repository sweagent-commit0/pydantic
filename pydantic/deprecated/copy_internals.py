from __future__ import annotations as _annotations
import typing
from copy import deepcopy
from enum import Enum
from typing import Any, Tuple
import typing_extensions
from .._internal import _model_construction, _typing_extra, _utils
if typing.TYPE_CHECKING:
    from .. import BaseModel
    from .._internal._utils import AbstractSetIntStr, MappingIntStrAny
    AnyClassMethod = classmethod[Any, Any, Any]
    TupleGenerator = typing.Generator[Tuple[str, Any], None, None]
    Model = typing.TypeVar('Model', bound='BaseModel')
    IncEx: typing_extensions.TypeAlias = 'set[int] | set[str] | dict[int, Any] | dict[str, Any] | None'
_object_setattr = _model_construction.object_setattr