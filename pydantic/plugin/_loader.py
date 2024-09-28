from __future__ import annotations
import importlib.metadata as importlib_metadata
import os
import warnings
from typing import TYPE_CHECKING, Final, Iterable
if TYPE_CHECKING:
    from . import PydanticPluginProtocol
PYDANTIC_ENTRY_POINT_GROUP: Final[str] = 'pydantic'
_plugins: dict[str, PydanticPluginProtocol] | None = None
_loading_plugins: bool = False

def get_plugins() -> Iterable[PydanticPluginProtocol]:
    """Load plugins for Pydantic.

    Inspired by: https://github.com/pytest-dev/pluggy/blob/1.3.0/src/pluggy/_manager.py#L376-L402
    """
    pass