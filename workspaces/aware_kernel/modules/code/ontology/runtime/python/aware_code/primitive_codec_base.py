"""Enhanced type system for representing complex primitive types."""

from abc import ABC, abstractmethod

# Kernel Graph Ontology
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_code_ontology.primitive.code_primitive_type_element_type import (
    CodePrimitiveTypeElementType,
)
from aware_code_ontology.primitive.code_primitive_type_union_type import (
    CodePrimitiveTypeUnionType,
)

# Code Runtime
from aware_code.primitive_signature import build_code_primitive_signature
from aware_code.stable_ids import (
    stable_code_primitive_type_element_type_id,
    stable_code_primitive_type_id,
    stable_code_primitive_type_union_type_id,
)
from aware_code.types import JsonObject


def build_code_primitive_type(
    *,
    base_type: CodePrimitiveBaseType,
    item_type: CodePrimitiveType | None = None,
    key_type: CodePrimitiveType | None = None,
    value_type: CodePrimitiveType | None = None,
    element_types: tuple[CodePrimitiveType, ...] = (),
    union_types: tuple[CodePrimitiveType, ...] = (),
    constraints: JsonObject | None = None,
) -> CodePrimitiveType:
    resolved_item_type = item_type
    resolved_key_type = key_type
    resolved_value_type = value_type

    if base_type in {CodePrimitiveBaseType.array, CodePrimitiveBaseType.set} and resolved_item_type is None:
        resolved_item_type = build_code_primitive_type(base_type=CodePrimitiveBaseType.any)
    if base_type == CodePrimitiveBaseType.dict:
        if resolved_key_type is None:
            resolved_key_type = build_code_primitive_type(base_type=CodePrimitiveBaseType.any)
        if resolved_value_type is None:
            resolved_value_type = build_code_primitive_type(base_type=CodePrimitiveBaseType.any)

    signature = build_code_primitive_signature(
        base_type=base_type,
        item_type=resolved_item_type,
        key_type=resolved_key_type,
        value_type=resolved_value_type,
        element_types=element_types,
        union_types=union_types,
        constraints=constraints,
    )
    prim = CodePrimitiveType(
        id=stable_code_primitive_type_id(signature=signature),
        signature=signature,
        base_type=base_type,
        item_type=resolved_item_type,
        key_type=resolved_key_type,
        value_type=resolved_value_type,
        constraints=constraints,
    )
    if element_types:
        prim.code_primitive_type_element_types = [
            CodePrimitiveTypeElementType(
                id=stable_code_primitive_type_element_type_id(
                    code_primitive_type_id=prim.id,
                    position=i,
                ),
                code_primitive_type_id=prim.id,
                position=i,
                element_type=element,
            )
            for i, element in enumerate(element_types)
        ]
    if union_types:
        prim.code_primitive_type_union_types = [
            CodePrimitiveTypeUnionType(
                id=stable_code_primitive_type_union_type_id(
                    code_primitive_type_id=prim.id,
                    position=i,
                ),
                code_primitive_type_id=prim.id,
                position=i,
                union_type=member,
            )
            for i, member in enumerate(union_types)
        ]
    return prim


class CodePrimitiveCodecBase(ABC):
    @abstractmethod
    def parse_exact(self, type_text: str) -> CodePrimitiveType | None: ...

    @abstractmethod
    def parse(self, type_text: str) -> CodePrimitiveType | None: ...

    @abstractmethod
    def render(self, prim: CodePrimitiveType) -> str | None: ...

    @abstractmethod
    def enum_ident(self, type_text: str) -> str: ...

    @abstractmethod
    def get_inner_type(self, type_text: str) -> str: ...

    @abstractmethod
    def is_void(self, type_text: str) -> bool: ...

    @abstractmethod
    def is_list(self, type_text: str) -> bool: ...

    @abstractmethod
    def is_set(self, type_text: str) -> bool: ...

    @abstractmethod
    def parse_literal(self, literal: str) -> object: ...

    @abstractmethod
    def to_literal_string(self, value: object) -> str: ...

    def _primitive(
        self,
        *,
        base_type: CodePrimitiveBaseType,
        item_type: CodePrimitiveType | None = None,
        key_type: CodePrimitiveType | None = None,
        value_type: CodePrimitiveType | None = None,
        element_types: tuple[CodePrimitiveType, ...] = (),
        union_types: tuple[CodePrimitiveType, ...] = (),
        constraints: JsonObject | None = None,
    ) -> CodePrimitiveType:
        return build_code_primitive_type(
            base_type=base_type,
            item_type=item_type,
            key_type=key_type,
            value_type=value_type,
            element_types=element_types,
            union_types=union_types,
            constraints=constraints,
        )

    def any(self) -> CodePrimitiveType:
        """Create an any type."""
        return self._primitive(base_type=CodePrimitiveBaseType.any)

    def integer(self) -> CodePrimitiveType:
        """Create an integer type."""
        return self._primitive(base_type=CodePrimitiveBaseType.integer)

    def float(self) -> CodePrimitiveType:
        """Create a float type."""
        return self._primitive(base_type=CodePrimitiveBaseType.float)

    def string(self) -> CodePrimitiveType:
        """Create a string type."""
        return self._primitive(base_type=CodePrimitiveBaseType.string)

    def boolean(self) -> CodePrimitiveType:
        """Create a boolean type."""
        return self._primitive(base_type=CodePrimitiveBaseType.boolean)

    def datetime(self) -> CodePrimitiveType:
        """Create a datetime type."""
        return self._primitive(base_type=CodePrimitiveBaseType.datetime)

    def uuid(self) -> CodePrimitiveType:
        """Create a UUID type."""
        return self._primitive(base_type=CodePrimitiveBaseType.uuid)

    def json(self) -> CodePrimitiveType:
        """Create a JSON type."""
        return self._primitive(base_type=CodePrimitiveBaseType.json)

    def json_value(self) -> CodePrimitiveType:
        """Create a JSON value type (scalar/object/array)."""
        return self._primitive(
            base_type=CodePrimitiveBaseType.json,
            constraints=JsonObject({"json_kind": "value"}),
        )

    def json_object(self) -> CodePrimitiveType:
        """Create a JSON object type (dict-like)."""
        return self._primitive(
            base_type=CodePrimitiveBaseType.json,
            constraints=JsonObject({"json_kind": "object"}),
        )

    def json_array(self) -> CodePrimitiveType:
        """Create a JSON array type (list-like)."""
        return self._primitive(
            base_type=CodePrimitiveBaseType.json,
            constraints=JsonObject({"json_kind": "array"}),
        )

    def array(self, item_type: CodePrimitiveType) -> CodePrimitiveType:
        """Create an array type with specified item type."""
        return self._primitive(base_type=CodePrimitiveBaseType.array, item_type=item_type)

    def dict(self, key_type: CodePrimitiveType, value_type: CodePrimitiveType) -> CodePrimitiveType:
        """Create a dictionary type with specified key and value types."""
        return self._primitive(
            base_type=CodePrimitiveBaseType.dict,
            key_type=key_type,
            value_type=value_type,
        )

    def tuple(self, *element_types: CodePrimitiveType) -> CodePrimitiveType:
        """Create a tuple type with specified element types."""
        return self._primitive(
            base_type=CodePrimitiveBaseType.tuple,
            element_types=tuple(element_types),
        )

    def set(self, item_type: CodePrimitiveType) -> CodePrimitiveType:
        """Create a set type with specified item type."""
        return self._primitive(base_type=CodePrimitiveBaseType.set, item_type=item_type)

    def union(self, *types: CodePrimitiveType) -> CodePrimitiveType:
        """Create a union type with the specified types."""
        return self._primitive(
            base_type=CodePrimitiveBaseType.union,
            union_types=tuple(types),
        )

    def vector(self, dimension: int | None = None) -> CodePrimitiveType:
        """Create a vector type with specified dimension."""
        if dimension:
            return self._primitive(
                base_type=CodePrimitiveBaseType.vector,
                constraints=JsonObject({"dimension": dimension}),
            )
        else:
            return self._primitive(base_type=CodePrimitiveBaseType.vector)

    def make_nullable(self, prim: CodePrimitiveType) -> CodePrimitiveType:
        """
        Create a new type that is the same as the current type, but with the base type set to NULL.
        """
        if prim.union_types:
            if CodePrimitiveBaseType.null in [t.base_type for t in prim.union_types]:
                # Already nullable, return self
                return prim
        # Make nullable
        null_type = self._primitive(base_type=CodePrimitiveBaseType.null)
        return self.union(prim, null_type)
