"""Logic for generating pydantic-core schemas for standard library types.

Import of this module is deferred since it contains imports of many standard library modules.
"""
from __future__ import annotations as _annotations
import collections
import collections.abc
import dataclasses
import decimal
import inspect
import os
import typing
from enum import Enum
from functools import partial
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from operator import attrgetter
from typing import Any, Callable, Iterable, Literal, Tuple, TypeVar
import typing_extensions
from pydantic_core import CoreSchema, MultiHostUrl, PydanticCustomError, PydanticOmit, Url, core_schema
from typing_extensions import get_args, get_origin
from pydantic.errors import PydanticSchemaGenerationError
from pydantic.fields import FieldInfo
from pydantic.types import Strict
from ..config import ConfigDict
from ..json_schema import JsonSchemaValue
from . import _known_annotated_metadata, _typing_extra, _validators
from ._core_utils import get_type_ref
from ._internal_dataclass import slots_true
from ._schema_generation_shared import GetCoreSchemaHandler, GetJsonSchemaHandler
if typing.TYPE_CHECKING:
    from ._generate_schema import GenerateSchema
    StdSchemaFunction = Callable[[GenerateSchema, type[Any]], core_schema.CoreSchema]

@dataclasses.dataclass(**slots_true)
class SchemaTransformer:
    get_core_schema: Callable[[Any, GetCoreSchemaHandler], CoreSchema]
    get_json_schema: Callable[[CoreSchema, GetJsonSchemaHandler], JsonSchemaValue]

    def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        return self.get_core_schema(source_type, handler)

    def __get_pydantic_json_schema__(self, schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        return self.get_json_schema(schema, handler)

@dataclasses.dataclass(**slots_true)
class InnerSchemaValidator:
    """Use a fixed CoreSchema, avoiding interference from outward annotations."""
    core_schema: CoreSchema
    js_schema: JsonSchemaValue | None = None
    js_core_schema: CoreSchema | None = None
    js_schema_update: JsonSchemaValue | None = None

    def __get_pydantic_json_schema__(self, _schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        if self.js_schema is not None:
            return self.js_schema
        js_schema = handler(self.js_core_schema or self.core_schema)
        if self.js_schema_update is not None:
            js_schema.update(self.js_schema_update)
        return js_schema

    def __get_pydantic_core_schema__(self, _source_type: Any, _handler: GetCoreSchemaHandler) -> CoreSchema:
        return self.core_schema

@dataclasses.dataclass(**slots_true)
class SequenceValidator:
    mapped_origin: type[Any]
    item_source_type: type[Any]
    min_length: int | None = None
    max_length: int | None = None
    strict: bool | None = None
    fail_fast: bool | None = None

    def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        if self.item_source_type is Any:
            items_schema = None
        else:
            items_schema = handler.generate_schema(self.item_source_type)
        metadata = {'min_length': self.min_length, 'max_length': self.max_length, 'strict': self.strict, 'fail_fast': self.fail_fast}
        if self.mapped_origin in (list, set, frozenset):
            if self.mapped_origin is list:
                constrained_schema = core_schema.list_schema(items_schema, **metadata)
            elif self.mapped_origin is set:
                constrained_schema = core_schema.set_schema(items_schema, **metadata)
            else:
                assert self.mapped_origin is frozenset
                constrained_schema = core_schema.frozenset_schema(items_schema, **metadata)
            schema = constrained_schema
        else:
            assert self.mapped_origin in (collections.deque, collections.Counter)
            if self.mapped_origin is collections.deque:
                coerce_instance_wrap = partial(core_schema.no_info_wrap_validator_function, partial(dequeue_validator, maxlen=metadata.get('max_length', None)))
            else:
                coerce_instance_wrap = partial(core_schema.no_info_after_validator_function, self.mapped_origin)
            metadata_with_strict_override = {**metadata, 'strict': False}
            constrained_schema = core_schema.list_schema(items_schema, **metadata_with_strict_override)
            check_instance = core_schema.json_or_python_schema(json_schema=core_schema.list_schema(), python_schema=core_schema.is_instance_schema(self.mapped_origin))
            serialization = core_schema.wrap_serializer_function_ser_schema(serialize_sequence_via_list, schema=items_schema or core_schema.any_schema(), info_arg=True)
            strict = core_schema.chain_schema([check_instance, coerce_instance_wrap(constrained_schema)])
            if metadata.get('strict', False):
                schema = strict
            else:
                lax = coerce_instance_wrap(constrained_schema)
                schema = core_schema.lax_or_strict_schema(lax_schema=lax, strict_schema=strict)
            schema['serialization'] = serialization
        return schema
SEQUENCE_ORIGIN_MAP: dict[Any, Any] = {typing.Deque: collections.deque, collections.deque: collections.deque, list: list, typing.List: list, set: set, typing.AbstractSet: set, typing.Set: set, frozenset: frozenset, typing.FrozenSet: frozenset, typing.Sequence: list, typing.MutableSequence: list, typing.MutableSet: set, collections.abc.MutableSet: set, collections.abc.Set: frozenset}
MAPPING_ORIGIN_MAP: dict[Any, Any] = {typing.DefaultDict: collections.defaultdict, collections.defaultdict: collections.defaultdict, collections.OrderedDict: collections.OrderedDict, typing_extensions.OrderedDict: collections.OrderedDict, dict: dict, typing.Dict: dict, collections.Counter: collections.Counter, typing.Counter: collections.Counter, typing.Mapping: dict, typing.MutableMapping: dict, collections.abc.MutableMapping: dict, collections.abc.Mapping: dict}

@dataclasses.dataclass(**slots_true)
class MappingValidator:
    mapped_origin: type[Any]
    keys_source_type: type[Any]
    values_source_type: type[Any]
    min_length: int | None = None
    max_length: int | None = None
    strict: bool = False

    def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        if self.keys_source_type is Any:
            keys_schema = None
        else:
            keys_schema = handler.generate_schema(self.keys_source_type)
        if self.values_source_type is Any:
            values_schema = None
        else:
            values_schema = handler.generate_schema(self.values_source_type)
        metadata = {'min_length': self.min_length, 'max_length': self.max_length, 'strict': self.strict}
        if self.mapped_origin is dict:
            schema = core_schema.dict_schema(keys_schema, values_schema, **metadata)
        else:
            constrained_schema = core_schema.dict_schema(keys_schema, values_schema, **metadata)
            check_instance = core_schema.json_or_python_schema(json_schema=core_schema.dict_schema(), python_schema=core_schema.is_instance_schema(self.mapped_origin))
            if self.mapped_origin is collections.defaultdict:
                default_default_factory = get_defaultdict_default_default_factory(self.values_source_type)
                coerce_instance_wrap = partial(core_schema.no_info_wrap_validator_function, partial(defaultdict_validator, default_default_factory=default_default_factory))
            else:
                coerce_instance_wrap = partial(core_schema.no_info_after_validator_function, self.mapped_origin)
            serialization = core_schema.wrap_serializer_function_ser_schema(self.serialize_mapping_via_dict, schema=core_schema.dict_schema(keys_schema or core_schema.any_schema(), values_schema or core_schema.any_schema()), info_arg=False)
            strict = core_schema.chain_schema([check_instance, coerce_instance_wrap(constrained_schema)])
            if metadata.get('strict', False):
                schema = strict
            else:
                lax = coerce_instance_wrap(constrained_schema)
                schema = core_schema.lax_or_strict_schema(lax_schema=lax, strict_schema=strict)
                schema['serialization'] = serialization
        return schema
PREPARE_METHODS: tuple[Callable[[Any, Iterable[Any], ConfigDict], tuple[Any, list[Any]] | None], ...] = (decimal_prepare_pydantic_annotations, sequence_like_prepare_pydantic_annotations, datetime_prepare_pydantic_annotations, uuid_prepare_pydantic_annotations, path_schema_prepare_pydantic_annotations, mapping_like_prepare_pydantic_annotations, ip_prepare_pydantic_annotations, url_prepare_pydantic_annotations)