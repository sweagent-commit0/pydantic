import warnings
from collections import ChainMap
from functools import partial, partialmethod, wraps
from itertools import chain
from types import FunctionType
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, List, Optional, Set, Tuple, Type, Union, overload
from pydantic.v1.errors import ConfigError
from pydantic.v1.typing import AnyCallable
from pydantic.v1.utils import ROOT_KEY, in_ipython
if TYPE_CHECKING:
    from pydantic.v1.typing import AnyClassMethod

class Validator:
    __slots__ = ('func', 'pre', 'each_item', 'always', 'check_fields', 'skip_on_failure')

    def __init__(self, func: AnyCallable, pre: bool=False, each_item: bool=False, always: bool=False, check_fields: bool=False, skip_on_failure: bool=False):
        self.func = func
        self.pre = pre
        self.each_item = each_item
        self.always = always
        self.check_fields = check_fields
        self.skip_on_failure = skip_on_failure
if TYPE_CHECKING:
    from inspect import Signature
    from pydantic.v1.config import BaseConfig
    from pydantic.v1.fields import ModelField
    from pydantic.v1.types import ModelOrDc
    ValidatorCallable = Callable[[Optional[ModelOrDc], Any, Dict[str, Any], ModelField, Type[BaseConfig]], Any]
    ValidatorsList = List[ValidatorCallable]
    ValidatorListDict = Dict[str, List[Validator]]
_FUNCS: Set[str] = set()
VALIDATOR_CONFIG_KEY = '__validator_config__'
ROOT_VALIDATOR_CONFIG_KEY = '__root_validator_config__'

def validator(*fields: str, pre: bool=False, each_item: bool=False, always: bool=False, check_fields: bool=True, whole: Optional[bool]=None, allow_reuse: bool=False) -> Callable[[AnyCallable], 'AnyClassMethod']:
    """
    Decorate methods on the class indicating that they should be used to validate fields
    :param fields: which field(s) the method should be called on
    :param pre: whether or not this validator should be called before the standard validators (else after)
    :param each_item: for complex objects (sets, lists etc.) whether to validate individual elements rather than the
      whole object
    :param always: whether this method and other validators should be called even if the value is missing
    :param check_fields: whether to check that the fields actually exist on the model
    :param allow_reuse: whether to track and raise an error if another validator refers to the decorated function
    """
    pass

def root_validator(_func: Optional[AnyCallable]=None, *, pre: bool=False, allow_reuse: bool=False, skip_on_failure: bool=False) -> Union['AnyClassMethod', Callable[[AnyCallable], 'AnyClassMethod']]:
    """
    Decorate methods on a model indicating that they should be used to validate (and perhaps modify) data either
    before or after standard model parsing/validation is performed.
    """
    pass

def _prepare_validator(function: AnyCallable, allow_reuse: bool) -> 'AnyClassMethod':
    """
    Avoid validators with duplicated names since without this, validators can be overwritten silently
    which generally isn't the intended behaviour, don't run in ipython (see #312) or if allow_reuse is False.
    """
    pass

class ValidatorGroup:

    def __init__(self, validators: 'ValidatorListDict') -> None:
        self.validators = validators
        self.used_validators = {'*'}

def make_generic_validator(validator: AnyCallable) -> 'ValidatorCallable':
    """
    Make a generic function which calls a validator with the right arguments.

    Unfortunately other approaches (eg. return a partial of a function that builds the arguments) is slow,
    hence this laborious way of doing things.

    It's done like this so validators don't all need **kwargs in their signature, eg. any combination of
    the arguments "values", "fields" and/or "config" are permitted.
    """
    pass
all_kwargs = {'values', 'field', 'config'}