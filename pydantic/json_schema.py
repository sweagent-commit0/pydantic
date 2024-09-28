"""
Usage docs: https://docs.pydantic.dev/2.5/concepts/json_schema/

The `json_schema` module contains classes and functions to allow the way [JSON Schema](https://json-schema.org/)
is generated to be customized.

In general you shouldn't need to use this module directly; instead, you can use
[`BaseModel.model_json_schema`][pydantic.BaseModel.model_json_schema] and
[`TypeAdapter.json_schema`][pydantic.TypeAdapter.json_schema].
"""
from __future__ import annotations as _annotations
import dataclasses
import inspect
import math
import re
import warnings
from collections import defaultdict
from copy import deepcopy
from dataclasses import is_dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Counter, Dict, Hashable, Iterable, NewType, Pattern, Sequence, Tuple, TypeVar, Union, cast
import pydantic_core
from pydantic_core import CoreSchema, PydanticOmit, core_schema, to_jsonable_python
from pydantic_core.core_schema import ComputedField
from typing_extensions import Annotated, Literal, TypeAlias, assert_never, deprecated, final
from pydantic.warnings import PydanticDeprecatedSince26
from ._internal import _config, _core_metadata, _core_utils, _decorators, _internal_dataclass, _mock_val_ser, _schema_generation_shared, _typing_extra
from .annotated_handlers import GetJsonSchemaHandler
from .config import JsonDict, JsonSchemaExtraCallable, JsonValue
from .errors import PydanticInvalidForJsonSchema, PydanticSchemaGenerationError, PydanticUserError
if TYPE_CHECKING:
    from . import ConfigDict
    from ._internal._core_utils import CoreSchemaField, CoreSchemaOrField
    from ._internal._dataclasses import PydanticDataclass
    from ._internal._schema_generation_shared import GetJsonSchemaFunction
    from .main import BaseModel
CoreSchemaOrFieldType = Literal[core_schema.CoreSchemaType, core_schema.CoreSchemaFieldType]
'\nA type alias for defined schema types that represents a union of\n`core_schema.CoreSchemaType` and\n`core_schema.CoreSchemaFieldType`.\n'
JsonSchemaValue = Dict[str, Any]
'\nA type alias for a JSON schema value. This is a dictionary of string keys to arbitrary JSON values.\n'
JsonSchemaMode = Literal['validation', 'serialization']
"\nA type alias that represents the mode of a JSON schema; either 'validation' or 'serialization'.\n\nFor some types, the inputs to validation differ from the outputs of serialization. For example,\ncomputed fields will only be present when serializing, and should not be provided when\nvalidating. This flag provides a way to indicate whether you want the JSON schema required\nfor validation inputs, or that will be matched by serialization outputs.\n"
_MODE_TITLE_MAPPING: dict[JsonSchemaMode, str] = {'validation': 'Input', 'serialization': 'Output'}

@deprecated('`update_json_schema` is deprecated, use a simple `my_dict.update(update_dict)` call instead.', category=None)
def update_json_schema(schema: JsonSchemaValue, updates: dict[str, Any]) -> JsonSchemaValue:
    """Update a JSON schema in-place by providing a dictionary of updates.

    This function sets the provided key-value pairs in the schema and returns the updated schema.

    Args:
        schema: The JSON schema to update.
        updates: A dictionary of key-value pairs to set in the schema.

    Returns:
        The updated JSON schema.
    """
    pass
JsonSchemaWarningKind = Literal['skipped-choice', 'non-serializable-default']
'\nA type alias representing the kinds of warnings that can be emitted during JSON schema generation.\n\nSee [`GenerateJsonSchema.render_warning_message`][pydantic.json_schema.GenerateJsonSchema.render_warning_message]\nfor more details.\n'

class PydanticJsonSchemaWarning(UserWarning):
    """This class is used to emit warnings produced during JSON schema generation.
    See the [`GenerateJsonSchema.emit_warning`][pydantic.json_schema.GenerateJsonSchema.emit_warning] and
    [`GenerateJsonSchema.render_warning_message`][pydantic.json_schema.GenerateJsonSchema.render_warning_message]
    methods for more details; these can be overridden to control warning behavior.
    """
DEFAULT_REF_TEMPLATE = '#/$defs/{model}'
'The default format string used to generate reference names.'
CoreRef = NewType('CoreRef', str)
DefsRef = NewType('DefsRef', str)
JsonRef = NewType('JsonRef', str)
CoreModeRef = Tuple[CoreRef, JsonSchemaMode]
JsonSchemaKeyT = TypeVar('JsonSchemaKeyT', bound=Hashable)

@dataclasses.dataclass(**_internal_dataclass.slots_true)
class _DefinitionsRemapping:
    defs_remapping: dict[DefsRef, DefsRef]
    json_remapping: dict[JsonRef, JsonRef]

    @staticmethod
    def from_prioritized_choices(prioritized_choices: dict[DefsRef, list[DefsRef]], defs_to_json: dict[DefsRef, JsonRef], definitions: dict[DefsRef, JsonSchemaValue]) -> _DefinitionsRemapping:
        """
        This function should produce a remapping that replaces complex DefsRef with the simpler ones from the
        prioritized_choices such that applying the name remapping would result in an equivalent JSON schema.
        """
        pass

    def remap_json_schema(self, schema: Any) -> Any:
        """
        Recursively update the JSON schema replacing all $refs
        """
        pass

class GenerateJsonSchema:
    """Usage docs: https://docs.pydantic.dev/2.8/concepts/json_schema/#customizing-the-json-schema-generation-process

    A class for generating JSON schemas.

    This class generates JSON schemas based on configured parameters. The default schema dialect
    is [https://json-schema.org/draft/2020-12/schema](https://json-schema.org/draft/2020-12/schema).
    The class uses `by_alias` to configure how fields with
    multiple names are handled and `ref_template` to format reference names.

    Attributes:
        schema_dialect: The JSON schema dialect used to generate the schema. See
            [Declaring a Dialect](https://json-schema.org/understanding-json-schema/reference/schema.html#id4)
            in the JSON Schema documentation for more information about dialects.
        ignored_warning_kinds: Warnings to ignore when generating the schema. `self.render_warning_message` will
            do nothing if its argument `kind` is in `ignored_warning_kinds`;
            this value can be modified on subclasses to easily control which warnings are emitted.
        by_alias: Whether to use field aliases when generating the schema.
        ref_template: The format string used when generating reference names.
        core_to_json_refs: A mapping of core refs to JSON refs.
        core_to_defs_refs: A mapping of core refs to definition refs.
        defs_to_core_refs: A mapping of definition refs to core refs.
        json_to_defs_refs: A mapping of JSON refs to definition refs.
        definitions: Definitions in the schema.

    Args:
        by_alias: Whether to use field aliases in the generated schemas.
        ref_template: The format string to use when generating reference names.

    Raises:
        JsonSchemaError: If the instance of the class is inadvertently re-used after generating a schema.
    """
    schema_dialect = 'https://json-schema.org/draft/2020-12/schema'
    ignored_warning_kinds: set[JsonSchemaWarningKind] = {'skipped-choice'}

    def __init__(self, by_alias: bool=True, ref_template: str=DEFAULT_REF_TEMPLATE):
        self.by_alias = by_alias
        self.ref_template = ref_template
        self.core_to_json_refs: dict[CoreModeRef, JsonRef] = {}
        self.core_to_defs_refs: dict[CoreModeRef, DefsRef] = {}
        self.defs_to_core_refs: dict[DefsRef, CoreModeRef] = {}
        self.json_to_defs_refs: dict[JsonRef, DefsRef] = {}
        self.definitions: dict[DefsRef, JsonSchemaValue] = {}
        self._config_wrapper_stack = _config.ConfigWrapperStack(_config.ConfigWrapper({}))
        self._mode: JsonSchemaMode = 'validation'
        self._prioritized_defsref_choices: dict[DefsRef, list[DefsRef]] = {}
        self._collision_counter: dict[str, int] = defaultdict(int)
        self._collision_index: dict[str, int] = {}
        self._schema_type_to_method = self.build_schema_type_to_method()
        self._core_defs_invalid_for_json_schema: dict[DefsRef, PydanticInvalidForJsonSchema] = {}
        self._used = False

    def build_schema_type_to_method(self) -> dict[CoreSchemaOrFieldType, Callable[[CoreSchemaOrField], JsonSchemaValue]]:
        """Builds a dictionary mapping fields to methods for generating JSON schemas.

        Returns:
            A dictionary containing the mapping of `CoreSchemaOrFieldType` to a handler method.

        Raises:
            TypeError: If no method has been defined for generating a JSON schema for a given pydantic core schema type.
        """
        pass

    def generate_definitions(self, inputs: Sequence[tuple[JsonSchemaKeyT, JsonSchemaMode, core_schema.CoreSchema]]) -> tuple[dict[tuple[JsonSchemaKeyT, JsonSchemaMode], JsonSchemaValue], dict[DefsRef, JsonSchemaValue]]:
        """Generates JSON schema definitions from a list of core schemas, pairing the generated definitions with a
        mapping that links the input keys to the definition references.

        Args:
            inputs: A sequence of tuples, where:

                - The first element is a JSON schema key type.
                - The second element is the JSON mode: either 'validation' or 'serialization'.
                - The third element is a core schema.

        Returns:
            A tuple where:

                - The first element is a dictionary whose keys are tuples of JSON schema key type and JSON mode, and
                    whose values are the JSON schema corresponding to that pair of inputs. (These schemas may have
                    JsonRef references to definitions that are defined in the second returned element.)
                - The second element is a dictionary whose keys are definition references for the JSON schemas
                    from the first returned element, and whose values are the actual JSON schema definitions.

        Raises:
            PydanticUserError: Raised if the JSON schema generator has already been used to generate a JSON schema.
        """
        pass

    def generate(self, schema: CoreSchema, mode: JsonSchemaMode='validation') -> JsonSchemaValue:
        """Generates a JSON schema for a specified schema in a specified mode.

        Args:
            schema: A Pydantic model.
            mode: The mode in which to generate the schema. Defaults to 'validation'.

        Returns:
            A JSON schema representing the specified schema.

        Raises:
            PydanticUserError: If the JSON schema generator has already been used to generate a JSON schema.
        """
        pass

    def generate_inner(self, schema: CoreSchemaOrField) -> JsonSchemaValue:
        """Generates a JSON schema for a given core schema.

        Args:
            schema: The given core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def any_schema(self, schema: core_schema.AnySchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches any value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def none_schema(self, schema: core_schema.NoneSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches `None`.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def bool_schema(self, schema: core_schema.BoolSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a bool value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def int_schema(self, schema: core_schema.IntSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches an int value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def float_schema(self, schema: core_schema.FloatSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a float value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def decimal_schema(self, schema: core_schema.DecimalSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a decimal value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def str_schema(self, schema: core_schema.StringSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a string value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def bytes_schema(self, schema: core_schema.BytesSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a bytes value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def date_schema(self, schema: core_schema.DateSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a date value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def time_schema(self, schema: core_schema.TimeSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a time value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def datetime_schema(self, schema: core_schema.DatetimeSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a datetime value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def timedelta_schema(self, schema: core_schema.TimedeltaSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a timedelta value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def literal_schema(self, schema: core_schema.LiteralSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a literal value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def enum_schema(self, schema: core_schema.EnumSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches an Enum value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def is_instance_schema(self, schema: core_schema.IsInstanceSchema) -> JsonSchemaValue:
        """Handles JSON schema generation for a core schema that checks if a value is an instance of a class.

        Unless overridden in a subclass, this raises an error.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def is_subclass_schema(self, schema: core_schema.IsSubclassSchema) -> JsonSchemaValue:
        """Handles JSON schema generation for a core schema that checks if a value is a subclass of a class.

        For backwards compatibility with v1, this does not raise an error, but can be overridden to change this.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def callable_schema(self, schema: core_schema.CallableSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a callable value.

        Unless overridden in a subclass, this raises an error.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def list_schema(self, schema: core_schema.ListSchema) -> JsonSchemaValue:
        """Returns a schema that matches a list schema.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    @deprecated('`tuple_positional_schema` is deprecated. Use `tuple_schema` instead.', category=None)
    @final
    def tuple_positional_schema(self, schema: core_schema.TupleSchema) -> JsonSchemaValue:
        """Replaced by `tuple_schema`."""
        pass

    @deprecated('`tuple_variable_schema` is deprecated. Use `tuple_schema` instead.', category=None)
    @final
    def tuple_variable_schema(self, schema: core_schema.TupleSchema) -> JsonSchemaValue:
        """Replaced by `tuple_schema`."""
        pass

    def tuple_schema(self, schema: core_schema.TupleSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a tuple schema e.g. `Tuple[int,
        str, bool]` or `Tuple[int, ...]`.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def set_schema(self, schema: core_schema.SetSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a set schema.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def frozenset_schema(self, schema: core_schema.FrozenSetSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a frozenset schema.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def generator_schema(self, schema: core_schema.GeneratorSchema) -> JsonSchemaValue:
        """Returns a JSON schema that represents the provided GeneratorSchema.

        Args:
            schema: The schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def dict_schema(self, schema: core_schema.DictSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a dict schema.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def function_before_schema(self, schema: core_schema.BeforeValidatorFunctionSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a function-before schema.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def function_after_schema(self, schema: core_schema.AfterValidatorFunctionSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a function-after schema.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def function_plain_schema(self, schema: core_schema.PlainValidatorFunctionSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a function-plain schema.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def function_wrap_schema(self, schema: core_schema.WrapValidatorFunctionSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a function-wrap schema.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def default_schema(self, schema: core_schema.WithDefaultSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema with a default value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def nullable_schema(self, schema: core_schema.NullableSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that allows null values.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def union_schema(self, schema: core_schema.UnionSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that allows values matching any of the given schemas.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def tagged_union_schema(self, schema: core_schema.TaggedUnionSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that allows values matching any of the given schemas, where
        the schemas are tagged with a discriminator field that indicates which schema should be used to validate
        the value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def _extract_discriminator(self, schema: core_schema.TaggedUnionSchema, one_of_choices: list[JsonDict]) -> str | None:
        """Extract a compatible OpenAPI discriminator from the schema and one_of choices that end up in the final
        schema."""
        pass

    def chain_schema(self, schema: core_schema.ChainSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a core_schema.ChainSchema.

        When generating a schema for validation, we return the validation JSON schema for the first step in the chain.
        For serialization, we return the serialization JSON schema for the last step in the chain.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def lax_or_strict_schema(self, schema: core_schema.LaxOrStrictSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that allows values matching either the lax schema or the
        strict schema.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def json_or_python_schema(self, schema: core_schema.JsonOrPythonSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that allows values matching either the JSON schema or the
        Python schema.

        The JSON schema is used instead of the Python schema. If you want to use the Python schema, you should override
        this method.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def typed_dict_schema(self, schema: core_schema.TypedDictSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a typed dict.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def typed_dict_field_schema(self, schema: core_schema.TypedDictField) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a typed dict field.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def dataclass_field_schema(self, schema: core_schema.DataclassField) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a dataclass field.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def model_field_schema(self, schema: core_schema.ModelField) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a model field.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def computed_field_schema(self, schema: core_schema.ComputedField) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a computed field.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def model_schema(self, schema: core_schema.ModelSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a model.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def resolve_schema_to_update(self, json_schema: JsonSchemaValue) -> JsonSchemaValue:
        """Resolve a JsonSchemaValue to the non-ref schema if it is a $ref schema.

        Args:
            json_schema: The schema to resolve.

        Returns:
            The resolved schema.
        """
        pass

    def model_fields_schema(self, schema: core_schema.ModelFieldsSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a model's fields.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def field_is_present(self, field: CoreSchemaField) -> bool:
        """Whether the field should be included in the generated JSON schema.

        Args:
            field: The schema for the field itself.

        Returns:
            `True` if the field should be included in the generated JSON schema, `False` otherwise.
        """
        pass

    def field_is_required(self, field: core_schema.ModelField | core_schema.DataclassField | core_schema.TypedDictField, total: bool) -> bool:
        """Whether the field should be marked as required in the generated JSON schema.
        (Note that this is irrelevant if the field is not present in the JSON schema.).

        Args:
            field: The schema for the field itself.
            total: Only applies to `TypedDictField`s.
                Indicates if the `TypedDict` this field belongs to is total, in which case any fields that don't
                explicitly specify `required=False` are required.

        Returns:
            `True` if the field should be marked as required in the generated JSON schema, `False` otherwise.
        """
        pass

    def dataclass_args_schema(self, schema: core_schema.DataclassArgsSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a dataclass's constructor arguments.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def dataclass_schema(self, schema: core_schema.DataclassSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a dataclass.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def arguments_schema(self, schema: core_schema.ArgumentsSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a function's arguments.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def kw_arguments_schema(self, arguments: list[core_schema.ArgumentsParameter], var_kwargs_schema: CoreSchema | None) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a function's keyword arguments.

        Args:
            arguments: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def p_arguments_schema(self, arguments: list[core_schema.ArgumentsParameter], var_args_schema: CoreSchema | None) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a function's positional arguments.

        Args:
            arguments: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def get_argument_name(self, argument: core_schema.ArgumentsParameter) -> str:
        """Retrieves the name of an argument.

        Args:
            argument: The core schema.

        Returns:
            The name of the argument.
        """
        pass

    def call_schema(self, schema: core_schema.CallSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a function call.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def custom_error_schema(self, schema: core_schema.CustomErrorSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a custom error.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def json_schema(self, schema: core_schema.JsonSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a JSON object.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def url_schema(self, schema: core_schema.UrlSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a URL.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def multi_host_url_schema(self, schema: core_schema.MultiHostUrlSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a URL that can be used with multiple hosts.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def uuid_schema(self, schema: core_schema.UuidSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a UUID.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def definitions_schema(self, schema: core_schema.DefinitionsSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that defines a JSON object with definitions.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def definition_ref_schema(self, schema: core_schema.DefinitionReferenceSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that references a definition.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def ser_schema(self, schema: core_schema.SerSchema | core_schema.IncExSeqSerSchema | core_schema.IncExDictSerSchema) -> JsonSchemaValue | None:
        """Generates a JSON schema that matches a schema that defines a serialized object.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        pass

    def get_title_from_name(self, name: str) -> str:
        """Retrieves a title from a name.

        Args:
            name: The name to retrieve a title from.

        Returns:
            The title.
        """
        pass

    def field_title_should_be_set(self, schema: CoreSchemaOrField) -> bool:
        """Returns true if a field with the given schema should have a title set based on the field name.

        Intuitively, we want this to return true for schemas that wouldn't otherwise provide their own title
        (e.g., int, float, str), and false for those that would (e.g., BaseModel subclasses).

        Args:
            schema: The schema to check.

        Returns:
            `True` if the field should have a title set, `False` otherwise.
        """
        pass

    def normalize_name(self, name: str) -> str:
        """Normalizes a name to be used as a key in a dictionary.

        Args:
            name: The name to normalize.

        Returns:
            The normalized name.
        """
        pass

    def get_defs_ref(self, core_mode_ref: CoreModeRef) -> DefsRef:
        """Override this method to change the way that definitions keys are generated from a core reference.

        Args:
            core_mode_ref: The core reference.

        Returns:
            The definitions key.
        """
        pass

    def get_cache_defs_ref_schema(self, core_ref: CoreRef) -> tuple[DefsRef, JsonSchemaValue]:
        """This method wraps the get_defs_ref method with some cache-lookup/population logic,
        and returns both the produced defs_ref and the JSON schema that will refer to the right definition.

        Args:
            core_ref: The core reference to get the definitions reference for.

        Returns:
            A tuple of the definitions reference and the JSON schema that will refer to it.
        """
        pass

    def handle_ref_overrides(self, json_schema: JsonSchemaValue) -> JsonSchemaValue:
        """It is not valid for a schema with a top-level $ref to have sibling keys.

        During our own schema generation, we treat sibling keys as overrides to the referenced schema,
        but this is not how the official JSON schema spec works.

        Because of this, we first remove any sibling keys that are redundant with the referenced schema, then if
        any remain, we transform the schema from a top-level '$ref' to use allOf to move the $ref out of the top level.
        (See bottom of https://swagger.io/docs/specification/using-ref/ for a reference about this behavior)
        """
        pass

    def encode_default(self, dft: Any) -> Any:
        """Encode a default value to a JSON-serializable value.

        This is used to encode default values for fields in the generated JSON schema.

        Args:
            dft: The default value to encode.

        Returns:
            The encoded default value.
        """
        pass

    def update_with_validations(self, json_schema: JsonSchemaValue, core_schema: CoreSchema, mapping: dict[str, str]) -> None:
        """Update the json_schema with the corresponding validations specified in the core_schema,
        using the provided mapping to translate keys in core_schema to the appropriate keys for a JSON schema.

        Args:
            json_schema: The JSON schema to update.
            core_schema: The core schema to get the validations from.
            mapping: A mapping from core_schema attribute names to the corresponding JSON schema attribute names.
        """
        pass

    class ValidationsMapping:
        """This class just contains mappings from core_schema attribute names to the corresponding
        JSON schema attribute names. While I suspect it is unlikely to be necessary, you can in
        principle override this class in a subclass of GenerateJsonSchema (by inheriting from
        GenerateJsonSchema.ValidationsMapping) to change these mappings.
        """
        numeric = {'multiple_of': 'multipleOf', 'le': 'maximum', 'ge': 'minimum', 'lt': 'exclusiveMaximum', 'gt': 'exclusiveMinimum'}
        bytes = {'min_length': 'minLength', 'max_length': 'maxLength'}
        string = {'min_length': 'minLength', 'max_length': 'maxLength', 'pattern': 'pattern'}
        array = {'min_length': 'minItems', 'max_length': 'maxItems'}
        object = {'min_length': 'minProperties', 'max_length': 'maxProperties'}
        date = {'le': 'maximum', 'ge': 'minimum', 'lt': 'exclusiveMaximum', 'gt': 'exclusiveMinimum'}

    def get_json_ref_counts(self, json_schema: JsonSchemaValue) -> dict[JsonRef, int]:
        """Get all values corresponding to the key '$ref' anywhere in the json_schema."""
        pass

    def emit_warning(self, kind: JsonSchemaWarningKind, detail: str) -> None:
        """This method simply emits PydanticJsonSchemaWarnings based on handling in the `warning_message` method."""
        pass

    def render_warning_message(self, kind: JsonSchemaWarningKind, detail: str) -> str | None:
        """This method is responsible for ignoring warnings as desired, and for formatting the warning messages.

        You can override the value of `ignored_warning_kinds` in a subclass of GenerateJsonSchema
        to modify what warnings are generated. If you want more control, you can override this method;
        just return None in situations where you don't want warnings to be emitted.

        Args:
            kind: The kind of warning to render. It can be one of the following:

                - 'skipped-choice': A choice field was skipped because it had no valid choices.
                - 'non-serializable-default': A default value was skipped because it was not JSON-serializable.
            detail: A string with additional details about the warning.

        Returns:
            The formatted warning message, or `None` if no warning should be emitted.
        """
        pass

def model_json_schema(cls: type[BaseModel] | type[PydanticDataclass], by_alias: bool=True, ref_template: str=DEFAULT_REF_TEMPLATE, schema_generator: type[GenerateJsonSchema]=GenerateJsonSchema, mode: JsonSchemaMode='validation') -> dict[str, Any]:
    """Utility function to generate a JSON Schema for a model.

    Args:
        cls: The model class to generate a JSON Schema for.
        by_alias: If `True` (the default), fields will be serialized according to their alias.
            If `False`, fields will be serialized according to their attribute name.
        ref_template: The template to use for generating JSON Schema references.
        schema_generator: The class to use for generating the JSON Schema.
        mode: The mode to use for generating the JSON Schema. It can be one of the following:

            - 'validation': Generate a JSON Schema for validating data.
            - 'serialization': Generate a JSON Schema for serializing data.

    Returns:
        The generated JSON Schema.
    """
    pass

def models_json_schema(models: Sequence[tuple[type[BaseModel] | type[PydanticDataclass], JsonSchemaMode]], *, by_alias: bool=True, title: str | None=None, description: str | None=None, ref_template: str=DEFAULT_REF_TEMPLATE, schema_generator: type[GenerateJsonSchema]=GenerateJsonSchema) -> tuple[dict[tuple[type[BaseModel] | type[PydanticDataclass], JsonSchemaMode], JsonSchemaValue], JsonSchemaValue]:
    """Utility function to generate a JSON Schema for multiple models.

    Args:
        models: A sequence of tuples of the form (model, mode).
        by_alias: Whether field aliases should be used as keys in the generated JSON Schema.
        title: The title of the generated JSON Schema.
        description: The description of the generated JSON Schema.
        ref_template: The reference template to use for generating JSON Schema references.
        schema_generator: The schema generator to use for generating the JSON Schema.

    Returns:
        A tuple where:
            - The first element is a dictionary whose keys are tuples of JSON schema key type and JSON mode, and
                whose values are the JSON schema corresponding to that pair of inputs. (These schemas may have
                JsonRef references to definitions that are defined in the second returned element.)
            - The second element is a JSON schema containing all definitions referenced in the first returned
                    element, along with the optional title and description keys.
    """
    pass
_HashableJsonValue: TypeAlias = Union[int, float, str, bool, None, Tuple['_HashableJsonValue', ...], Tuple[Tuple[str, '_HashableJsonValue'], ...]]

@dataclasses.dataclass(**_internal_dataclass.slots_true)
class WithJsonSchema:
    """Usage docs: https://docs.pydantic.dev/2.8/concepts/json_schema/#withjsonschema-annotation

    Add this as an annotation on a field to override the (base) JSON schema that would be generated for that field.
    This provides a way to set a JSON schema for types that would otherwise raise errors when producing a JSON schema,
    such as Callable, or types that have an is-instance core schema, without needing to go so far as creating a
    custom subclass of pydantic.json_schema.GenerateJsonSchema.
    Note that any _modifications_ to the schema that would normally be made (such as setting the title for model fields)
    will still be performed.

    If `mode` is set this will only apply to that schema generation mode, allowing you
    to set different json schemas for validation and serialization.
    """
    json_schema: JsonSchemaValue | None
    mode: Literal['validation', 'serialization'] | None = None

    def __get_pydantic_json_schema__(self, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        mode = self.mode or handler.mode
        if mode != handler.mode:
            return handler(core_schema)
        if self.json_schema is None:
            raise PydanticOmit
        else:
            return self.json_schema

    def __hash__(self) -> int:
        return hash(type(self.mode))

@dataclasses.dataclass(**_internal_dataclass.slots_true)
class Examples:
    """Add examples to a JSON schema.

    Examples should be a map of example names (strings)
    to example values (any valid JSON).

    If `mode` is set this will only apply to that schema generation mode,
    allowing you to add different examples for validation and serialization.
    """
    examples: dict[str, Any]
    mode: Literal['validation', 'serialization'] | None = None

    def __get_pydantic_json_schema__(self, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        mode = self.mode or handler.mode
        json_schema = handler(core_schema)
        if mode != handler.mode:
            return json_schema
        examples = json_schema.get('examples', {})
        examples.update(to_jsonable_python(self.examples))
        json_schema['examples'] = examples
        return json_schema

    def __hash__(self) -> int:
        return hash(type(self.mode))

def _get_all_json_refs(item: Any) -> set[JsonRef]:
    """Get all the definitions references from a JSON schema."""
    pass
AnyType = TypeVar('AnyType')
if TYPE_CHECKING:
    SkipJsonSchema = Annotated[AnyType, ...]
else:

    @dataclasses.dataclass(**_internal_dataclass.slots_true)
    class SkipJsonSchema:
        """Usage docs: https://docs.pydantic.dev/2.8/concepts/json_schema/#skipjsonschema-annotation

        Add this as an annotation on a field to skip generating a JSON schema for that field.

        Example:
            ```py
            from typing import Union

            from pydantic import BaseModel
            from pydantic.json_schema import SkipJsonSchema

            from pprint import pprint


            class Model(BaseModel):
                a: Union[int, None] = None  # (1)!
                b: Union[int, SkipJsonSchema[None]] = None  # (2)!
                c: SkipJsonSchema[Union[int, None]] = None  # (3)!


            pprint(Model.model_json_schema())
            '''
            {
                'properties': {
                    'a': {
                        'anyOf': [
                            {'type': 'integer'},
                            {'type': 'null'}
                        ],
                        'default': None,
                        'title': 'A'
                    },
                    'b': {
                        'default': None,
                        'title': 'B',
                        'type': 'integer'
                    }
                },
                'title': 'Model',
                'type': 'object'
            }
            '''
            ```

            1. The integer and null types are both included in the schema for `a`.
            2. The integer type is the only type included in the schema for `b`.
            3. The entirety of the `c` field is omitted from the schema.
        """

        def __class_getitem__(cls, item: AnyType) -> AnyType:
            return Annotated[item, cls()]

        def __get_pydantic_json_schema__(self, core_schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
            raise PydanticOmit

        def __hash__(self) -> int:
            return hash(type(self))