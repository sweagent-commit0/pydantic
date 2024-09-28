from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Mapping, Optional, Tuple, Type, TypeVar, Union, overload
from pydantic.v1 import validator
from pydantic.v1.config import Extra
from pydantic.v1.errors import ConfigError
from pydantic.v1.main import BaseModel, create_model
from pydantic.v1.typing import get_all_type_hints
from pydantic.v1.utils import to_camel
__all__ = ('validate_arguments',)
if TYPE_CHECKING:
    from pydantic.v1.typing import AnyCallable
    AnyCallableT = TypeVar('AnyCallableT', bound=AnyCallable)
    ConfigType = Union[None, Type[Any], Dict[str, Any]]

def validate_arguments(func: Optional['AnyCallableT']=None, *, config: 'ConfigType'=None) -> Any:
    """
    Decorator to validate the arguments passed to a function.
    """
    pass
ALT_V_ARGS = 'v__args'
ALT_V_KWARGS = 'v__kwargs'
V_POSITIONAL_ONLY_NAME = 'v__positional_only'
V_DUPLICATE_KWARGS = 'v__duplicate_kwargs'

class ValidatedFunction:

    def __init__(self, function: 'AnyCallableT', config: 'ConfigType'):
        from inspect import Parameter, signature
        parameters: Mapping[str, Parameter] = signature(function).parameters
        if parameters.keys() & {ALT_V_ARGS, ALT_V_KWARGS, V_POSITIONAL_ONLY_NAME, V_DUPLICATE_KWARGS}:
            raise ConfigError(f'"{ALT_V_ARGS}", "{ALT_V_KWARGS}", "{V_POSITIONAL_ONLY_NAME}" and "{V_DUPLICATE_KWARGS}" are not permitted as argument names when using the "{validate_arguments.__name__}" decorator')
        self.raw_function = function
        self.arg_mapping: Dict[int, str] = {}
        self.positional_only_args = set()
        self.v_args_name = 'args'
        self.v_kwargs_name = 'kwargs'
        type_hints = get_all_type_hints(function)
        takes_args = False
        takes_kwargs = False
        fields: Dict[str, Tuple[Any, Any]] = {}
        for i, (name, p) in enumerate(parameters.items()):
            if p.annotation is p.empty:
                annotation = Any
            else:
                annotation = type_hints[name]
            default = ... if p.default is p.empty else p.default
            if p.kind == Parameter.POSITIONAL_ONLY:
                self.arg_mapping[i] = name
                fields[name] = (annotation, default)
                fields[V_POSITIONAL_ONLY_NAME] = (List[str], None)
                self.positional_only_args.add(name)
            elif p.kind == Parameter.POSITIONAL_OR_KEYWORD:
                self.arg_mapping[i] = name
                fields[name] = (annotation, default)
                fields[V_DUPLICATE_KWARGS] = (List[str], None)
            elif p.kind == Parameter.KEYWORD_ONLY:
                fields[name] = (annotation, default)
            elif p.kind == Parameter.VAR_POSITIONAL:
                self.v_args_name = name
                fields[name] = (Tuple[annotation, ...], None)
                takes_args = True
            else:
                assert p.kind == Parameter.VAR_KEYWORD, p.kind
                self.v_kwargs_name = name
                fields[name] = (Dict[str, annotation], None)
                takes_kwargs = True
        if not takes_args and self.v_args_name in fields:
            self.v_args_name = ALT_V_ARGS
        if not takes_kwargs and self.v_kwargs_name in fields:
            self.v_kwargs_name = ALT_V_KWARGS
        if not takes_args:
            fields[self.v_args_name] = (List[Any], None)
        if not takes_kwargs:
            fields[self.v_kwargs_name] = (Dict[Any, Any], None)
        self.create_model(fields, takes_args, takes_kwargs, config)