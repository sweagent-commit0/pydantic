from __future__ import annotations as _annotations
from typing import TYPE_CHECKING, Any, Hashable, Sequence
from pydantic_core import CoreSchema, core_schema
from ..errors import PydanticUserError
from . import _core_utils
from ._core_utils import CoreSchemaField, collect_definitions
if TYPE_CHECKING:
    from ..types import Discriminator
CORE_SCHEMA_METADATA_DISCRIMINATOR_PLACEHOLDER_KEY = 'pydantic.internal.union_discriminator'

class MissingDefinitionForUnionRef(Exception):
    """Raised when applying a discriminated union discriminator to a schema
    requires a definition that is not yet defined
    """

    def __init__(self, ref: str) -> None:
        self.ref = ref
        super().__init__(f'Missing definition for ref {self.ref!r}')

def apply_discriminator(schema: core_schema.CoreSchema, discriminator: str | Discriminator, definitions: dict[str, core_schema.CoreSchema] | None=None) -> core_schema.CoreSchema:
    """Applies the discriminator and returns a new core schema.

    Args:
        schema: The input schema.
        discriminator: The name of the field which will serve as the discriminator.
        definitions: A mapping of schema ref to schema.

    Returns:
        The new core schema.

    Raises:
        TypeError:
            - If `discriminator` is used with invalid union variant.
            - If `discriminator` is used with `Union` type with one variant.
            - If `discriminator` value mapped to multiple choices.
        MissingDefinitionForUnionRef:
            If the definition for ref is missing.
        PydanticUserError:
            - If a model in union doesn't have a discriminator field.
            - If discriminator field has a non-string alias.
            - If discriminator fields have different aliases.
            - If discriminator field not of type `Literal`.
    """
    pass

class _ApplyInferredDiscriminator:
    """This class is used to convert an input schema containing a union schema into one where that union is
    replaced with a tagged-union, with all the associated debugging and performance benefits.

    This is done by:
    * Validating that the input schema is compatible with the provided discriminator
    * Introspecting the schema to determine which discriminator values should map to which union choices
    * Handling various edge cases such as 'definitions', 'default', 'nullable' schemas, and more

    I have chosen to implement the conversion algorithm in this class, rather than a function,
    to make it easier to maintain state while recursively walking the provided CoreSchema.
    """

    def __init__(self, discriminator: str, definitions: dict[str, core_schema.CoreSchema]):
        self.discriminator = discriminator
        self.definitions = definitions
        self._discriminator_alias: str | None = None
        self._should_be_nullable = False
        self._is_nullable = False
        self._choices_to_handle: list[core_schema.CoreSchema] = []
        self._tagged_union_choices: dict[Hashable, core_schema.CoreSchema] = {}
        self._used = False

    def apply(self, schema: core_schema.CoreSchema) -> core_schema.CoreSchema:
        """Return a new CoreSchema based on `schema` that uses a tagged-union with the discriminator provided
        to this class.

        Args:
            schema: The input schema.

        Returns:
            The new core schema.

        Raises:
            TypeError:
                - If `discriminator` is used with invalid union variant.
                - If `discriminator` is used with `Union` type with one variant.
                - If `discriminator` value mapped to multiple choices.
            ValueError:
                If the definition for ref is missing.
            PydanticUserError:
                - If a model in union doesn't have a discriminator field.
                - If discriminator field has a non-string alias.
                - If discriminator fields have different aliases.
                - If discriminator field not of type `Literal`.
        """
        pass

    def _apply_to_root(self, schema: core_schema.CoreSchema) -> core_schema.CoreSchema:
        """This method handles the outer-most stage of recursion over the input schema:
        unwrapping nullable or definitions schemas, and calling the `_handle_choice`
        method iteratively on the choices extracted (recursively) from the possibly-wrapped union.
        """
        pass

    def _handle_choice(self, choice: core_schema.CoreSchema) -> None:
        """This method handles the "middle" stage of recursion over the input schema.
        Specifically, it is responsible for handling each choice of the outermost union
        (and any "coalesced" choices obtained from inner unions).

        Here, "handling" entails:
        * Coalescing nested unions and compatible tagged-unions
        * Tracking the presence of 'none' and 'nullable' schemas occurring as choices
        * Validating that each allowed discriminator value maps to a unique choice
        * Updating the _tagged_union_choices mapping that will ultimately be used to build the TaggedUnionSchema.
        """
        pass

    def _is_discriminator_shared(self, choice: core_schema.TaggedUnionSchema) -> bool:
        """This method returns a boolean indicating whether the discriminator for the `choice`
        is the same as that being used for the outermost tagged union. This is used to
        determine whether this TaggedUnionSchema choice should be "coalesced" into the top level,
        or whether it should be treated as a separate (nested) choice.
        """
        pass

    def _infer_discriminator_values_for_choice(self, choice: core_schema.CoreSchema, source_name: str | None) -> list[str | int]:
        """This function recurses over `choice`, extracting all discriminator values that should map to this choice.

        `model_name` is accepted for the purpose of producing useful error messages.
        """
        pass

    def _infer_discriminator_values_for_typed_dict_choice(self, choice: core_schema.TypedDictSchema, source_name: str | None=None) -> list[str | int]:
        """This method just extracts the _infer_discriminator_values_for_choice logic specific to TypedDictSchema
        for the sake of readability.
        """
        pass

    def _infer_discriminator_values_for_inner_schema(self, schema: core_schema.CoreSchema, source: str) -> list[str | int]:
        """When inferring discriminator values for a field, we typically extract the expected values from a literal
        schema. This function does that, but also handles nested unions and defaults.
        """
        pass

    def _set_unique_choice_for_values(self, choice: core_schema.CoreSchema, values: Sequence[str | int]) -> None:
        """This method updates `self.tagged_union_choices` so that all provided (discriminator) `values` map to the
        provided `choice`, validating that none of these values already map to another (different) choice.
        """
        pass