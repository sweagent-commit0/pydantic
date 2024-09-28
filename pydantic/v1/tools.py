import json
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional, Type, TypeVar, Union
from pydantic.v1.parse import Protocol, load_file, load_str_bytes
from pydantic.v1.types import StrBytes
from pydantic.v1.typing import display_as_type
__all__ = ('parse_file_as', 'parse_obj_as', 'parse_raw_as', 'schema_of', 'schema_json_of')
NameFactory = Union[str, Callable[[Type[Any]], str]]
if TYPE_CHECKING:
    from pydantic.v1.typing import DictStrAny
T = TypeVar('T')

def schema_of(type_: Any, *, title: Optional[NameFactory]=None, **schema_kwargs: Any) -> 'DictStrAny':
    """Generate a JSON schema (as dict) for the passed model or dynamically generated one"""
    pass

def schema_json_of(type_: Any, *, title: Optional[NameFactory]=None, **schema_json_kwargs: Any) -> str:
    """Generate a JSON schema (as JSON) for the passed model or dynamically generated one"""
    pass