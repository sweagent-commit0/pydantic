import json
from typing import TYPE_CHECKING, Any, Dict, Generator, List, Optional, Sequence, Tuple, Type, Union
from pydantic.v1.json import pydantic_encoder
from pydantic.v1.utils import Representation
if TYPE_CHECKING:
    from typing_extensions import TypedDict
    from pydantic.v1.config import BaseConfig
    from pydantic.v1.types import ModelOrDc
    from pydantic.v1.typing import ReprArgs
    Loc = Tuple[Union[int, str], ...]

    class _ErrorDictRequired(TypedDict):
        loc: Loc
        msg: str
        type: str

    class ErrorDict(_ErrorDictRequired, total=False):
        ctx: Dict[str, Any]
__all__ = ('ErrorWrapper', 'ValidationError')

class ErrorWrapper(Representation):
    __slots__ = ('exc', '_loc')

    def __init__(self, exc: Exception, loc: Union[str, 'Loc']) -> None:
        self.exc = exc
        self._loc = loc

    def __repr_args__(self) -> 'ReprArgs':
        return [('exc', self.exc), ('loc', self.loc_tuple())]
ErrorList = Union[Sequence[Any], ErrorWrapper]

class ValidationError(Representation, ValueError):
    __slots__ = ('raw_errors', 'model', '_error_cache')

    def __init__(self, errors: Sequence[ErrorList], model: 'ModelOrDc') -> None:
        self.raw_errors = errors
        self.model = model
        self._error_cache: Optional[List['ErrorDict']] = None

    def __str__(self) -> str:
        errors = self.errors()
        no_errors = len(errors)
        return f'{no_errors} validation error{('' if no_errors == 1 else 's')} for {self.model.__name__}\n{display_errors(errors)}'

    def __repr_args__(self) -> 'ReprArgs':
        return [('model', self.model.__name__), ('errors', self.errors())]
_EXC_TYPE_CACHE: Dict[Type[Exception], str] = {}