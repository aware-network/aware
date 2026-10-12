from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum

from .encoding import FrozenJson, digest_payload

SCHEMA_CONTRACT = "aware.meta.semantic-type-schema.v1"
SLICE_CONTRACT = "aware.meta.semantic-type-schema-slice.v1"


class TypeKind(StrEnum):
    VALUE_OBJECT = "value_object"
    GRAPH_OBJECT = "graph_object"
    ENUM = "enum"
    UNION = "union"
    SCALAR_ALIAS = "scalar_alias"


class ShapeKind(StrEnum):
    SCALAR = "scalar"
    NAMED = "named"
    LIST = "list"
    MAP = "map"
    UNION = "union"


class ScalarKind(StrEnum):
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    DECIMAL = "decimal"
    DATETIME = "datetime"
    BYTES = "bytes"
    UUID = "uuid"
    JSON = "json"
    NULL = "null"


def _token(value: str, field_name: str) -> str:
    if type(value) is str:
        if not value or value.split() != [value]:
            raise ValueError(f"{field_name} must be a non-empty token")
        return value
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be str")
    if not value or value.strip() != value or any(char.isspace() for char in value):
        raise ValueError(f"{field_name} must be a non-empty token")
    return value


def _tokens(
    values: Iterable[str], field_name: str, *, sort: bool = False
) -> tuple[str, ...]:
    result = tuple(_token(value, field_name) for value in values)
    if len(result) != len(set(result)):
        raise ValueError(f"{field_name} contains duplicates")
    return tuple(sorted(result)) if sort else result


@dataclass(frozen=True, slots=True)
class ValueShape:
    kind: ShapeKind
    scalar_kind: ScalarKind | None = None
    type_ref: str | None = None
    element: ValueShape | None = None
    map_value: ValueShape | None = None
    variants: tuple[ValueShape, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", ShapeKind(self.kind))
        if self.scalar_kind is not None:
            object.__setattr__(self, "scalar_kind", ScalarKind(self.scalar_kind))
        if self.type_ref is not None:
            object.__setattr__(self, "type_ref", _token(self.type_ref, "type_ref"))
        variants = tuple(self.variants)
        if any(not isinstance(value, ValueShape) for value in variants):
            raise TypeError("variants must contain ValueShape")
        object.__setattr__(self, "variants", variants)
        valid = {
            ShapeKind.SCALAR: self.scalar_kind is not None
            and self.type_ref is None
            and self.element is None
            and self.map_value is None
            and not variants,
            ShapeKind.NAMED: self.scalar_kind is None
            and self.type_ref is not None
            and self.element is None
            and self.map_value is None
            and not variants,
            ShapeKind.LIST: self.scalar_kind is None
            and self.type_ref is None
            and isinstance(self.element, ValueShape)
            and self.map_value is None
            and not variants,
            ShapeKind.MAP: self.scalar_kind is None
            and self.type_ref is None
            and self.element is None
            and isinstance(self.map_value, ValueShape)
            and not variants,
            ShapeKind.UNION: self.scalar_kind is None
            and self.type_ref is None
            and self.element is None
            and self.map_value is None
            and len(variants) >= 2
            and len(variants) == len(set(variants)),
        }[self.kind]
        if not valid:
            raise ValueError(f"shape payload does not match {self.kind.value}")

    @classmethod
    def scalar(cls, kind: ScalarKind) -> ValueShape:
        return cls(ShapeKind.SCALAR, scalar_kind=kind)

    @classmethod
    def named(cls, type_ref: str) -> ValueShape:
        return cls(ShapeKind.NAMED, type_ref=type_ref)

    @classmethod
    def list_of(cls, element: ValueShape) -> ValueShape:
        return cls(ShapeKind.LIST, element=element)

    @classmethod
    def map_of(cls, value: ValueShape) -> ValueShape:
        return cls(ShapeKind.MAP, map_value=value)

    @classmethod
    def union_of(cls, *variants: ValueShape) -> ValueShape:
        return cls(ShapeKind.UNION, variants=variants)

    def referenced_type_refs(self) -> frozenset[str]:
        refs: set[str] = set()
        if self.type_ref is not None:
            refs.add(self.type_ref)
        for nested in (self.element, self.map_value):
            if nested is not None:
                refs.update(nested.referenced_type_refs())
        for variant in self.variants:
            refs.update(variant.referenced_type_refs())
        return frozenset(refs)

    def to_wire(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "scalar_kind": None if self.scalar_kind is None else self.scalar_kind.value,
            "type_ref": self.type_ref,
            "element": None if self.element is None else self.element.to_wire(),
            "map_value": None if self.map_value is None else self.map_value.to_wire(),
            "variants": [value.to_wire() for value in self.variants],
        }


@dataclass(frozen=True, slots=True)
class IdentityDefinition:
    field_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        refs = _tokens(self.field_refs, "identity.field_refs")
        if not refs:
            raise ValueError("identity requires field_refs")
        object.__setattr__(self, "field_refs", refs)

    def to_wire(self) -> dict[str, object]:
        return {"field_refs": list(self.field_refs)}


@dataclass(frozen=True, slots=True)
class FieldDefinition:
    field_ref: str
    name: str
    shape: ValueShape
    required: bool = False
    nullable: bool = False
    default_value: FrozenJson | None = None
    constraints: FrozenJson = field(default_factory=lambda: FrozenJson.from_value({}))
    aliases: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "field_ref", _token(self.field_ref, "field_ref"))
        object.__setattr__(self, "name", _token(self.name, "name"))
        if not isinstance(self.shape, ValueShape):
            raise TypeError("shape must be ValueShape")
        if not isinstance(self.required, bool) or not isinstance(self.nullable, bool):
            raise TypeError("required and nullable must be bool")
        if self.default_value is not None and not isinstance(
            self.default_value, FrozenJson
        ):
            raise TypeError("default_value must be FrozenJson or None")
        if not isinstance(self.constraints, FrozenJson):
            raise TypeError("constraints must be FrozenJson")
        object.__setattr__(self, "aliases", _tokens(self.aliases, "aliases", sort=True))

    def to_wire(self) -> dict[str, object]:
        return {
            "field_ref": self.field_ref,
            "name": self.name,
            "shape": self.shape.to_wire(),
            "required": self.required,
            "nullable": self.nullable,
            "has_default": self.default_value is not None,
            "default_value": None
            if self.default_value is None
            else self.default_value.to_wire(),
            "constraints": self.constraints.to_wire(),
            "aliases": list(self.aliases),
        }


@dataclass(frozen=True, slots=True)
class TypeDefinition:
    type_ref: str
    name: str
    kind: TypeKind
    fields: tuple[FieldDefinition, ...] = ()
    identity: IdentityDefinition | None = None
    enum_values: tuple[str, ...] = ()
    union_variants: tuple[ValueShape, ...] = ()
    scalar_target: ScalarKind | None = None
    discriminant_field_ref: str | None = None
    constraints: FrozenJson = field(default_factory=lambda: FrozenJson.from_value({}))
    aliases: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "type_ref", _token(self.type_ref, "type_ref"))
        object.__setattr__(self, "name", _token(self.name, "name"))
        object.__setattr__(self, "kind", TypeKind(self.kind))
        fields = tuple(self.fields)
        if any(not isinstance(value, FieldDefinition) for value in fields):
            raise TypeError("fields must contain FieldDefinition")
        refs = tuple(value.field_ref for value in fields)
        names = tuple(value.name for value in fields)
        if len(refs) != len(set(refs)) or len(names) != len(set(names)):
            raise ValueError("field refs and names must be unique")
        object.__setattr__(self, "fields", fields)
        if self.identity is not None and not isinstance(
            self.identity, IdentityDefinition
        ):
            raise TypeError("identity must be IdentityDefinition or None")
        enums = _tokens(self.enum_values, "enum_values")
        object.__setattr__(self, "enum_values", enums)
        variants = tuple(self.union_variants)
        if any(not isinstance(value, ValueShape) for value in variants):
            raise TypeError("union_variants must contain ValueShape")
        if len(variants) != len(set(variants)):
            raise ValueError("union_variants contains duplicates")
        object.__setattr__(self, "union_variants", variants)
        if self.scalar_target is not None:
            object.__setattr__(self, "scalar_target", ScalarKind(self.scalar_target))
        if self.discriminant_field_ref is not None:
            object.__setattr__(
                self,
                "discriminant_field_ref",
                _token(self.discriminant_field_ref, "discriminant_field_ref"),
            )
        if not isinstance(self.constraints, FrozenJson):
            raise TypeError("constraints must be FrozenJson")
        object.__setattr__(self, "aliases", _tokens(self.aliases, "aliases", sort=True))
        is_object = self.kind in (TypeKind.VALUE_OBJECT, TypeKind.GRAPH_OBJECT)
        if is_object:
            if enums or variants or self.scalar_target is not None:
                raise ValueError("object types may contain only fields and identity")
            if self.discriminant_field_ref is not None:
                raise ValueError("object types cannot declare discriminant")
            if self.identity and not set(self.identity.field_refs).issubset(refs):
                raise ValueError("identity field refs must belong to the type")
        elif self.kind is TypeKind.ENUM:
            if (
                fields
                or self.identity
                or not enums
                or variants
                or self.scalar_target
                or self.discriminant_field_ref
            ):
                raise ValueError("enum types require only enum_values")
        elif self.kind is TypeKind.UNION:
            if (
                fields
                or self.identity
                or enums
                or len(variants) < 2
                or self.scalar_target
            ):
                raise ValueError("union types require only two or more variants")
        elif (
            fields
            or self.identity
            or enums
            or variants
            or self.scalar_target is None
            or self.discriminant_field_ref
        ):
            raise ValueError("scalar aliases require only scalar_target")

    def referenced_type_refs(self) -> frozenset[str]:
        refs: set[str] = set()
        for value in self.fields:
            refs.update(value.shape.referenced_type_refs())
        for value in self.union_variants:
            refs.update(value.referenced_type_refs())
        return frozenset(refs)

    def to_wire(self) -> dict[str, object]:
        return {
            "type_ref": self.type_ref,
            "name": self.name,
            "kind": self.kind.value,
            "fields": [value.to_wire() for value in self.fields],
            "identity": None if self.identity is None else self.identity.to_wire(),
            "enum_values": list(self.enum_values),
            "union_variants": [value.to_wire() for value in self.union_variants],
            "scalar_target": None
            if self.scalar_target is None
            else self.scalar_target.value,
            "discriminant_field_ref": self.discriminant_field_ref,
            "constraints": self.constraints.to_wire(),
            "aliases": list(self.aliases),
        }


def _types(values: Iterable[TypeDefinition]) -> tuple[TypeDefinition, ...]:
    result = tuple(values)
    if any(not isinstance(value, TypeDefinition) for value in result):
        raise TypeError("types must contain TypeDefinition")
    refs = tuple(value.type_ref for value in result)
    if len(refs) != len(set(refs)):
        raise ValueError("types contain duplicate type_ref")
    return tuple(sorted(result, key=lambda value: value.type_ref))


def _closure(by_ref: dict[str, TypeDefinition], roots: Iterable[str]) -> set[str]:
    pending = list(roots)
    result: set[str] = set()
    while pending:
        ref = pending.pop()
        if ref in result:
            continue
        value = by_ref.get(ref)
        if value is None:
            raise ValueError(f"unresolved type ref {ref!r}")
        result.add(ref)
        pending.extend(sorted(value.referenced_type_refs() - result))
    return result


@dataclass(frozen=True, slots=True)
class TypeSchemaBundle:
    namespace: str
    semantic_version: str
    types: tuple[TypeDefinition, ...]
    schema_digest: str
    contract: str = SCHEMA_CONTRACT

    def __post_init__(self) -> None:
        if self.contract != SCHEMA_CONTRACT:
            raise ValueError(f"unsupported schema contract {self.contract!r}")
        object.__setattr__(self, "namespace", _token(self.namespace, "namespace"))
        object.__setattr__(
            self, "semantic_version", _token(self.semantic_version, "semantic_version")
        )
        values = _types(self.types)
        if not values:
            raise ValueError("bundle requires at least one type")
        _closure(
            {value.type_ref: value for value in values},
            [value.type_ref for value in values],
        )
        object.__setattr__(self, "types", values)
        expected = digest_payload(SCHEMA_CONTRACT, self.semantic_wire())
        if self.schema_digest != expected:
            raise ValueError(f"schema_digest mismatch; expected {expected}")

    @classmethod
    def create(
        cls,
        *,
        namespace: str,
        semantic_version: str,
        types: Iterable[TypeDefinition],
    ) -> TypeSchemaBundle:
        values = _types(types)
        semantic = {
            "contract": SCHEMA_CONTRACT,
            "namespace": _token(namespace, "namespace"),
            "semantic_version": _token(semantic_version, "semantic_version"),
            "types": [value.to_wire() for value in values],
        }
        return cls(
            namespace,
            semantic_version,
            values,
            digest_payload(SCHEMA_CONTRACT, semantic),
        )

    def semantic_wire(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "namespace": self.namespace,
            "semantic_version": self.semantic_version,
            "types": [value.to_wire() for value in self.types],
        }

    def to_wire(self) -> dict[str, object]:
        return {**self.semantic_wire(), "schema_digest": self.schema_digest}


@dataclass(frozen=True, slots=True)
class TypeSchemaSlice:
    bundle_digest: str
    namespace: str
    semantic_version: str
    root_type_refs: tuple[str, ...]
    types: tuple[TypeDefinition, ...]
    slice_digest: str
    contract: str = SLICE_CONTRACT

    def __post_init__(self) -> None:
        if self.contract != SLICE_CONTRACT:
            raise ValueError(f"unsupported slice contract {self.contract!r}")
        object.__setattr__(
            self, "bundle_digest", _token(self.bundle_digest, "bundle_digest")
        )
        object.__setattr__(self, "namespace", _token(self.namespace, "namespace"))
        object.__setattr__(
            self, "semantic_version", _token(self.semantic_version, "semantic_version")
        )
        roots = _tokens(self.root_type_refs, "root_type_refs", sort=True)
        if not roots:
            raise ValueError("slice requires root_type_refs")
        object.__setattr__(self, "root_type_refs", roots)
        values = _types(self.types)
        object.__setattr__(self, "types", values)
        by_ref = {value.type_ref: value for value in values}
        exact = _closure(by_ref, roots)
        extras = sorted(set(by_ref) - exact)
        if extras:
            raise ValueError(f"slice contains types outside closure: {extras!r}")
        expected = digest_payload(SLICE_CONTRACT, self.semantic_wire())
        if self.slice_digest != expected:
            raise ValueError(f"slice_digest mismatch; expected {expected}")

    @classmethod
    def create(
        cls, bundle: TypeSchemaBundle, *, root_type_refs: Iterable[str]
    ) -> TypeSchemaSlice:
        if not isinstance(bundle, TypeSchemaBundle):
            raise TypeError("bundle must be TypeSchemaBundle")
        roots = _tokens(root_type_refs, "root_type_refs", sort=True)
        if not roots:
            raise ValueError("slice requires root_type_refs")
        by_ref = {value.type_ref: value for value in bundle.types}
        refs = _closure(by_ref, roots)
        values = tuple(by_ref[ref] for ref in sorted(refs))
        semantic = {
            "contract": SLICE_CONTRACT,
            "bundle_digest": bundle.schema_digest,
            "namespace": bundle.namespace,
            "semantic_version": bundle.semantic_version,
            "root_type_refs": list(roots),
            "types": [value.to_wire() for value in values],
        }
        return cls(
            bundle.schema_digest,
            bundle.namespace,
            bundle.semantic_version,
            roots,
            values,
            digest_payload(SLICE_CONTRACT, semantic),
        )

    def semantic_wire(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "bundle_digest": self.bundle_digest,
            "namespace": self.namespace,
            "semantic_version": self.semantic_version,
            "root_type_refs": list(self.root_type_refs),
            "types": [value.to_wire() for value in self.types],
        }

    def to_wire(self) -> dict[str, object]:
        return {**self.semantic_wire(), "slice_digest": self.slice_digest}
