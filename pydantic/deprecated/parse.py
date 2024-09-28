from __future__ import annotations
import json
import pickle
import warnings
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable
from typing_extensions import deprecated
from ..warnings import PydanticDeprecatedSince20
if not TYPE_CHECKING:
    DeprecationWarning = PydanticDeprecatedSince20

class Protocol(str, Enum):
    json = 'json'
    pickle = 'pickle'