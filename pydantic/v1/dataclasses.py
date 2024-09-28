"""
The main purpose is to enhance stdlib dataclasses by adding validation
A pydantic dataclass can be generated from scratch or from a stdlib one.

Behind the scene, a pydantic dataclass is just like a regular one on which we attach
a `BaseModel` and magic methods to trigger the validation of the data.
`__init__` and `__post_init__` are hence overridden and have extra logic to be
able to validate input data.

When a pydantic dataclass is generated from scratch, it's just a plain dataclass
with validation triggered at initialization

The tricky part if for stdlib dataclasses that are converted after into pydantic ones e.g.

```py
@dataclasses.dataclass
class M:
    x: int

ValidatedM = pydantic.dataclasses.dataclass(M)
```

We indeed still want to support equality, hashing, repr, ... as if it was the stdlib one!

```py
assert isinstance(ValidatedM(x=1), M)
assert ValidatedM(x=1) == M(x=1)
```

This means we **don't want to create a new dataclass that inherits from it**
The trick is to create a wrapper around `M` that will act as a proxy to trigger
validation without altering default `M` behaviour.
"""
import copy
import dataclasses
import sys
from contextlib import contextmanager
from functools import wraps
try:
    from functools import cached_property
except ImportError:
    pass
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Dict, Generator, Optional, Type, TypeVar, Union, overload
from typing_extensions import dataclass_transform
from pydantic.v1.class_validators import gather_all_validators
from pydantic.v1.config import BaseConfig, ConfigDict, Extra, get_config
from pydantic.v1.error_wrappers import ValidationError
from pydantic.v1.errors import DataclassTypeError
from pydantic.v1.fields import Field, FieldInfo, Required, Undefined
from pydantic.v1.main import create_model, validate_model
from pydantic.v1.utils import ClassAttribute
if TYPE_CHECKING:
    from pydantic.v1.main import BaseModel
    from pydantic.v1.typing import CallableGenerator, NoArgAnyCallable
    DataclassT = TypeVar('DataclassT', bound='Dataclass')
    DataclassClassOrWrapper = Union[Type['Dataclass'], 'DataclassProxy']

    class Dataclass:
        __dataclass_fields__: ClassVar[Dict[str, Any]]
        __dataclass_params__: ClassVar[Any]
        __post_init__: ClassVar[Callable[..., None]]
        __pydantic_run_validation__: ClassVar[bool]
        __post_init_post_parse__: ClassVar[Callable[..., None]]
        __pydantic_initialised__: ClassVar[bool]
        __pydantic_model__: ClassVar[Type[BaseModel]]
        __pydantic_validate_values__: ClassVar[Callable[['Dataclass'], None]]
        __pydantic_has_field_info_default__: ClassVar[bool]

        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        @classmethod
        def __get_validators__(cls: Type['Dataclass']) -> 'CallableGenerator':
            pass

        @classmethod
        def __validate__(cls: Type['DataclassT'], v: Any) -> 'DataclassT':
            pass
__all__ = ['dataclass', 'set_validation', 'create_pydantic_model_from_dataclass', 'is_builtin_dataclass', 'make_dataclass_validator']
_T = TypeVar('_T')
if sys.version_info >= (3, 10):

@dataclass_transform(field_specifiers=(dataclasses.field, Field))
def dataclass(_cls: Optional[Type[_T]]=None, *, init: bool=True, repr: bool=True, eq: bool=True, order: bool=False, unsafe_hash: bool=False, frozen: bool=False, config: Union[ConfigDict, Type[object], None]=None, validate_on_init: Optional[bool]=None, use_proxy: Optional[bool]=None, kw_only: bool=False) -> Union[Callable[[Type[_T]], 'DataclassClassOrWrapper'], 'DataclassClassOrWrapper']:
    """
    Like the python standard lib dataclasses but with type validation.
    The result is either a pydantic dataclass that will validate input data
    or a wrapper that will trigger validation around a stdlib dataclass
    to avoid modifying it directly
    """
    pass

class DataclassProxy:
    __slots__ = '__dataclass__'

    def __init__(self, dc_cls: Type['Dataclass']) -> None:
        object.__setattr__(self, '__dataclass__', dc_cls)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        with set_validation(self.__dataclass__, True):
            return self.__dataclass__(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.__dataclass__, name)

    def __setattr__(self, __name: str, __value: Any) -> None:
        return setattr(self.__dataclass__, __name, __value)

    def __instancecheck__(self, instance: Any) -> bool:
        return isinstance(instance, self.__dataclass__)

    def __copy__(self) -> 'DataclassProxy':
        return DataclassProxy(copy.copy(self.__dataclass__))

    def __deepcopy__(self, memo: Any) -> 'DataclassProxy':
        return DataclassProxy(copy.deepcopy(self.__dataclass__, memo))

def _add_pydantic_validation_attributes(dc_cls: Type['Dataclass'], config: Type[BaseConfig], validate_on_init: bool, dc_cls_doc: str) -> None:
    """
    We need to replace the right method. If no `__post_init__` has been set in the stdlib dataclass
    it won't even exist (code is generated on the fly by `dataclasses`)
    By default, we run validation after `__init__` or `__post_init__` if defined
    """
    pass
if sys.version_info >= (3, 8):

def is_builtin_dataclass(_cls: Type[Any]) -> bool:
    """
    Whether a class is a stdlib dataclass
    (useful to discriminated a pydantic dataclass that is actually a wrapper around a stdlib dataclass)

    we check that
    - `_cls` is a dataclass
    - `_cls` is not a processed pydantic dataclass (with a basemodel attached)
    - `_cls` is not a pydantic dataclass inheriting directly from a stdlib dataclass
    e.g.
    ```
    @dataclasses.dataclass
    class A:
        x: int

    @pydantic.dataclasses.dataclass
    class B(A):
        y: int
    ```
    In this case, when we first check `B`, we make an extra check and look at the annotations ('y'),
    which won't be a superset of all the dataclass fields (only the stdlib fields i.e. 'x')
    """
    pass

def make_dataclass_validator(dc_cls: Type['Dataclass'], config: Type[BaseConfig]) -> 'CallableGenerator':
    """
    Create a pydantic.dataclass from a builtin dataclass to add type validation
    and yield the validators
    It retrieves the parameters of the dataclass and forwards them to the newly created dataclass
    """
    pass