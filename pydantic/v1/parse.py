import json
import pickle
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Union
from pydantic.v1.types import StrBytes

class Protocol(str, Enum):
    json = 'json'
    pickle = 'pickle'