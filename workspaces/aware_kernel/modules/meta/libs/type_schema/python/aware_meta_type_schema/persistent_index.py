"""Immutable fixed-depth content-addressed index authorities.

The index is a 64-level SHA-256 radix trie.  Persistent values contain no
reader, cache, store, timing, or mutation capability.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, fields
from types import MappingProxyType
from typing import Any, Self, cast

from .encoding import canonical_json

PERSISTENT_BODY_COORDINATE_CONTRACT = (
    "aware.meta.type-schema.persistent-body-coordinate.v1"
)
PERSISTENT_INDEX_NODE_CONTRACT = "aware.meta.type-schema.persistent-index-node.v1"
PERSISTENT_INDEX_ROOT_CONTRACT = "aware.meta.type-schema.persistent-index-root.v1"
PERSISTENT_INDEX_DEPTH = 64
_PERSISTENT_BODY_COORDINATE_CONTRACT_BYTES = (
    PERSISTENT_BODY_COORDINATE_CONTRACT.encode("ascii")
)
_PERSISTENT_INDEX_NODE_CONTRACT_BYTES = PERSISTENT_INDEX_NODE_CONTRACT.encode("ascii")
_PERSISTENT_INDEX_DEPTH_BYTES = tuple(
    str(depth).encode("ascii") for depth in range(PERSISTENT_INDEX_DEPTH + 1)
)

_BODY_ROLE_BY_SCHEMA = {
    PERSISTENT_INDEX_NODE_CONTRACT: "node_ref",
    "aware.meta.type-schema.definition-fragment.v1": "fragment_ref",
    "aware.meta.type-schema.source-attribution-fragment.v1": "attribution_ref",
    "aware.meta.type-schema.package-root.v1": "package_root_ref",
    "aware.meta.type-schema.owner-binding.v1": "owner_ref",
}

_HEX = frozenset("0123456789abcdef")
_WHITESPACE = re.compile(r"\s").search
_NON_HEX = re.compile(r"[^0-9a-f]").search


class _MetaTypeSchemaOperationContext:
    """Nominal, synchronous authority for validation-bypassing helpers."""

    __slots__ = ("_sequence",)

    def __new__(cls) -> Self:
        raise TypeError("Meta operation contexts are runtime-issued")


_OPERATION_CONTEXT_LOCK = threading.Lock()
_OPERATION_CONTEXT_SEQUENCE = 0
_OPERATION_CONTEXTS: dict[
    int,
    tuple[
        _MetaTypeSchemaOperationContext,
        int,
        int,
        int,
        str,
        object,
        str,
        int,
    ],
] = {}
_OPERATION_CONTEXT_STACKS: dict[tuple[int, int], list[int]] = {}
_OPERATION_REFS = frozenset(
    {
        "persistent-index.lookup",
        "persistent-index.patch",
        "persistent-index.prove",
        "positive-reader.advance-proof-bundle",
        "composition.resolve",
        "composition.transition-package",
        "composition.transition-catalog",
        "composition.advance-attribution",
    }
)
_META_DATACLASS_FIELD_NAMES: dict[type[object], tuple[str, ...]] = {}
_META_OPERAND_TYPE_REGISTRY: tuple[
    Mapping[int, type[object]],
    Mapping[int, type[object]],
    Mapping[int, type[object]],
] | None = None


def _closed_exact_type_registry(
    *allowed_types: type[object],
) -> Mapping[int, type[object]]:
    return MappingProxyType(
        {id(allowed_type): allowed_type for allowed_type in allowed_types}
    )


def _is_registered_exact_type(
    candidate: type[object],
    registry: Mapping[int, type[object]],
) -> bool:
    """Resolve identity without candidate hashing or equality behavior."""

    return registry.get(id(candidate)) is candidate


def _meta_operand_type_registry() -> tuple[
    Mapping[int, type[object]],
    Mapping[int, type[object]],
    Mapping[int, type[object]],
]:
    """Return the closed exact-type set admitted by private Meta operations."""

    global _META_OPERAND_TYPE_REGISTRY
    retained = _META_OPERAND_TYPE_REGISTRY
    if retained is not None:
        return retained

    # Imports remain local because this module owns the persistent values used
    # by every module below.  The registry stores the actual class objects;
    # module/name metadata can neither extend nor impersonate it.
    from .composed_slice_advancement import AdmittedTypeSchemaComposedSlice
    from .composition import (
        ComposedPackageEvidence,
        ComposedTypeOwnerEvidence,
        TypeOwnerBinding,
        TypeSchemaCatalogRoot,
        TypeSchemaComposedSlice,
        TypeSchemaComposedSliceResult,
        TypeSchemaPackageRoot,
    )
    from .composition_transition import (
        DefinitionFragmentMovement,
        PackageRootMovement,
        SourceAttributionFragmentMovement,
        SourceAttributionLifecycleEvidence,
        TypeDefinitionLifecycleEvidence,
        TypeOwnerBindingMovement,
        TypeSchemaCatalogTransition,
        TypeSchemaPackageTransition,
        TypeSchemaTypedEmptyCatalogAuthority,
        TypeSchemaTypedEmptyPackageAuthority,
    )
    from .definition_fragment import (
        SourceDefinitionBinding,
        TypeDefinitionFragment,
        TypeSchemaSourceAttributionFragment,
    )
    from .encoding import FrozenJson
    from .model import (
        FieldDefinition,
        IdentityDefinition,
        ScalarKind,
        ShapeKind,
        TypeDefinition,
        TypeKind,
        TypeSchemaBundle,
        TypeSchemaSlice,
        ValueShape,
    )
    from .positive_reader import (
        IndexBindingMovement,
        PersistentIndexMembershipProof,
        PersistentIndexPatchResult,
        PersistentIndexProofBundle,
        PositiveBodyRead,
        PositiveReadObservation,
        _AdmittedPersistentIndexProofBundle,
    )

    retained = (
        _closed_exact_type_registry(
            FrozenJson,
            ValueShape,
            IdentityDefinition,
            FieldDefinition,
            TypeDefinition,
            TypeSchemaBundle,
            TypeSchemaSlice,
            TypeDefinitionFragment,
            SourceDefinitionBinding,
            TypeSchemaSourceAttributionFragment,
            PersistentBodyCoordinate,
            PersistentBodyAuthority,
            PersistentIndexChild,
            PersistentIndexNode,
            PersistentIndexRoot,
            PositiveBodyRead,
            PositiveReadObservation,
            PersistentIndexMembershipProof,
            PersistentIndexProofBundle,
            IndexBindingMovement,
            PersistentIndexPatchResult,
            TypeSchemaPackageRoot,
            TypeOwnerBinding,
            TypeSchemaCatalogRoot,
            ComposedTypeOwnerEvidence,
            ComposedPackageEvidence,
            TypeSchemaComposedSlice,
            TypeSchemaComposedSliceResult,
            TypeSchemaTypedEmptyPackageAuthority,
            TypeSchemaTypedEmptyCatalogAuthority,
            DefinitionFragmentMovement,
            SourceAttributionFragmentMovement,
            PackageRootMovement,
            TypeOwnerBindingMovement,
            TypeDefinitionLifecycleEvidence,
            SourceAttributionLifecycleEvidence,
            TypeSchemaPackageTransition,
            TypeSchemaCatalogTransition,
        ),
        _closed_exact_type_registry(TypeKind, ShapeKind, ScalarKind),
        _closed_exact_type_registry(
            AdmittedTypeSchemaComposedSlice,
            _AdmittedPersistentIndexProofBundle,
        ),
    )
    _META_OPERAND_TYPE_REGISTRY = retained
    return retained


def _preflight_meta_type_schema_operands(value: object) -> None:
    """Reject foreign nested values without allocating an operand copy."""

    dataclass_types, enum_types, nominal_types = _meta_operand_type_registry()
    seen: set[int] = set()

    def visit(item: object) -> None:
        item_type = type(item)
        if (
            item is None
            or item_type is str
            or item_type is int
            or item_type is bool
            or item_type is bytes
            or item_type is float
        ):
            return
        if item_type is PersistentBodyCoordinate:
            coordinate = cast(PersistentBodyCoordinate, item)
            if (
                any(
                    type(object.__getattribute__(coordinate, field_name)) is not str
                    for field_name in (
                        "schema",
                        "ref_field",
                        "authority_ref",
                        "body_ref",
                        "body_digest",
                        "coordinate_ref",
                        "contract",
                    )
                )
                or type(object.__getattribute__(coordinate, "size_bytes")) is not int
            ):
                raise TypeSchemaPersistentIndexError(
                    "private operation contains foreign coordinate fields"
                )
            return
        if item_type is PersistentBodyAuthority:
            authority = cast(PersistentBodyAuthority, item)
            coordinate = object.__getattribute__(authority, "coordinate")
            canonical_bytes = object.__getattribute__(authority, "canonical_bytes")
            if (
                type(coordinate) is not PersistentBodyCoordinate
                or type(canonical_bytes) is not bytes
            ):
                raise TypeSchemaPersistentIndexError(
                    "private operation contains foreign body authority fields"
                )
            visit(coordinate)
            return
        if item_type is PersistentIndexRoot:
            root = cast(PersistentIndexRoot, item)
            if (
                type(object.__getattribute__(root, "keyspace")) is not str
                or type(object.__getattribute__(root, "root_node"))
                is not PersistentBodyCoordinate
                or type(object.__getattribute__(root, "binding_count")) is not int
                or type(object.__getattribute__(root, "root_ref")) is not str
                or type(object.__getattribute__(root, "contract")) is not str
            ):
                raise TypeSchemaPersistentIndexError(
                    "private operation contains foreign index-root fields"
                )
            visit(object.__getattribute__(root, "root_node"))
            return
        if item_type is tuple or item_type is list:
            for child in cast(tuple[object, ...] | list[object], item):
                visit(child)
            return
        if item_type is dict:
            dictionary = cast(dict[object, object], item)
            if any(type(key) is not str for key in dictionary):
                raise TypeSchemaPersistentIndexError(
                    "private operation mapping keys must be exact text"
                )
            for child in dictionary.values():
                visit(child)
            return
        if _is_registered_exact_type(item_type, enum_types):
            visit(object.__getattribute__(item, "_value_"))
            return
        if _is_registered_exact_type(item_type, nominal_types):
            return
        if not _is_registered_exact_type(item_type, dataclass_types):
            raise TypeSchemaPersistentIndexError(
                "private operation contains foreign or unsupported operand "
                f"{item_type.__module__}.{item_type.__qualname__}"
            )
        identity = id(item)
        if identity in seen:
            return
        seen.add(identity)
        field_names = _META_DATACLASS_FIELD_NAMES.get(item_type)
        if field_names is None:
            field_names = tuple(field.name for field in fields(cast(Any, item)))
            _META_DATACLASS_FIELD_NAMES[item_type] = field_names
        for field_name in field_names:
            visit(object.__getattribute__(cast(Any, item), field_name))

    visit(value)


def _protected_operand_wire(value: object) -> object:
    """Return compact evidence after behavior-free recursive exact admission."""

    dataclass_types, enum_types, nominal_types = _meta_operand_type_registry()
    seen: dict[int, int] = {}
    node_count = 0

    def visit(item: object) -> object:
        nonlocal node_count
        node_count += 1
        item_type = type(item)
        if item is None:
            return ("none",)
        if (
            item_type is bool
            or item_type is int
            or item_type is float
            or item_type is str
            or item_type is bytes
        ):
            return (item_type.__name__, item)
        if item_type is PersistentBodyCoordinate:
            coordinate = cast(PersistentBodyCoordinate, item)
            return (
                "coordinate",
                object.__getattribute__(coordinate, "schema"),
                object.__getattribute__(coordinate, "ref_field"),
                object.__getattribute__(coordinate, "authority_ref"),
                object.__getattribute__(coordinate, "body_ref"),
                object.__getattribute__(coordinate, "body_digest"),
                object.__getattribute__(coordinate, "size_bytes"),
                object.__getattribute__(coordinate, "coordinate_ref"),
                object.__getattribute__(coordinate, "contract"),
            )
        if item_type is PersistentBodyAuthority:
            authority = cast(PersistentBodyAuthority, item)
            return (
                "body",
                visit(object.__getattribute__(authority, "coordinate")),
                object.__getattribute__(authority, "canonical_bytes"),
            )
        if item_type is PersistentIndexRoot:
            root = cast(PersistentIndexRoot, item)
            return (
                "index-root",
                object.__getattribute__(root, "keyspace"),
                visit(object.__getattribute__(root, "root_node")),
                object.__getattribute__(root, "binding_count"),
                object.__getattribute__(root, "root_ref"),
                object.__getattribute__(root, "contract"),
            )
        if item_type is tuple or item_type is list:
            values = cast(tuple[object, ...] | list[object], item)
            return (
                "tuple" if item_type is tuple else "list",
                tuple(visit(child) for child in values),
            )
        if item_type is dict:
            dictionary = cast(dict[object, object], item)
            if any(type(key) is not str for key in dictionary):
                raise TypeSchemaPersistentIndexError(
                    "private operation mapping keys must be exact text"
                )
            return (
                "dict",
                tuple(
                    (key, visit(dictionary[key]))
                    for key in sorted(cast(dict[str, object], dictionary))
                ),
            )
        if _is_registered_exact_type(item_type, enum_types):
            return (
                "enum",
                item_type,
                visit(object.__getattribute__(item, "_value_")),
            )
        if _is_registered_exact_type(item_type, nominal_types):
            return (
                "nominal",
                item_type,
                id(item),
            )
        if not _is_registered_exact_type(item_type, dataclass_types):
            raise TypeSchemaPersistentIndexError(
                "private operation contains foreign or unsupported operand "
                f"{item_type.__module__}.{item_type.__qualname__}"
            )
        identity = id(item)
        if identity in seen:
            return ("reference", item_type, seen[identity])
        identity_index = len(seen)
        seen[identity] = identity_index
        field_names = _META_DATACLASS_FIELD_NAMES.get(item_type)
        if field_names is None:
            field_names = tuple(field.name for field in fields(cast(Any, item)))
            _META_DATACLASS_FIELD_NAMES[item_type] = field_names
        return (
            "dataclass",
            item_type,
            identity_index,
            tuple(
                (
                    field_name,
                    visit(object.__getattribute__(cast(Any, item), field_name)),
                )
                for field_name in field_names
            ),
        )

    guard = visit(value)
    guard_nonce = f"{os.getpid()}:{threading.get_ident()}:{id(guard)}:{node_count}"
    return (
        "aware.meta.type-schema.operation-operand-snapshot.v1",
        guard,
        "sha256:" + hashlib.sha256(guard_nonce.encode("ascii")).hexdigest(),
        node_count,
    )


def _protected_operand_digest(value: object) -> str:
    if (
        type(value) is not tuple
        or len(value) != 2
        or type(value[0]) is not str
        or type(value[1]) is not tuple
        or len(value[1]) != 4
        or value[1][0] != "aware.meta.type-schema.operation-operand-snapshot.v1"
        or type(value[1][2]) is not str
    ):
        raise TypeSchemaPersistentIndexError(
            "protected operation snapshot is malformed"
        )
    return cast(str, value[1][2])


def _matches_protected_operand_guard(value: object, guard: object) -> bool:
    """Compare live operands with a private immutable guard without behavior."""

    dataclass_types, enum_types, nominal_types = _meta_operand_type_registry()
    seen: dict[int, int] = {}
    pending: list[tuple[object, object]] = [(value, guard)]
    scalar_types: dict[str, type[object]] = {
        "bool": bool,
        "int": int,
        "float": float,
        "str": str,
        "bytes": bytes,
    }
    while pending:
        item, expected = pending.pop()
        if type(expected) is not tuple or not expected:
            return False
        expected_values = cast(tuple[object, ...], expected)
        kind = expected_values[0]
        if kind == "none":
            if item is not None or len(expected_values) != 1:
                return False
            continue
        scalar_type = scalar_types.get(cast(str, kind))
        if scalar_type is not None:
            if (
                len(expected_values) != 2
                or type(item) is not scalar_type
                or (
                    repr(item) != repr(expected_values[1])
                    if scalar_type is float
                    else item != expected_values[1]
                )
            ):
                return False
            continue
        if kind == "coordinate":
            if type(item) is not PersistentBodyCoordinate or len(expected_values) != 9:
                return False
            coordinate = cast(PersistentBodyCoordinate, item)
            actual = (
                object.__getattribute__(coordinate, "schema"),
                object.__getattribute__(coordinate, "ref_field"),
                object.__getattribute__(coordinate, "authority_ref"),
                object.__getattribute__(coordinate, "body_ref"),
                object.__getattribute__(coordinate, "body_digest"),
                object.__getattribute__(coordinate, "size_bytes"),
                object.__getattribute__(coordinate, "coordinate_ref"),
                object.__getattribute__(coordinate, "contract"),
            )
            if any(type(value) is not str for value in (*actual[:5], *actual[6:])):
                return False
            if type(actual[5]) is not int or actual != expected_values[1:]:
                return False
            continue
        if kind == "body":
            if type(item) is not PersistentBodyAuthority or len(expected_values) != 3:
                return False
            authority = cast(PersistentBodyAuthority, item)
            canonical_bytes = object.__getattribute__(authority, "canonical_bytes")
            if (
                type(canonical_bytes) is not bytes
                or canonical_bytes != expected_values[2]
            ):
                return False
            pending.append(
                (
                    object.__getattribute__(authority, "coordinate"),
                    expected_values[1],
                )
            )
            continue
        if kind == "index-root":
            if type(item) is not PersistentIndexRoot or len(expected_values) != 6:
                return False
            root = cast(PersistentIndexRoot, item)
            keyspace = object.__getattribute__(root, "keyspace")
            binding_count = object.__getattribute__(root, "binding_count")
            root_ref = object.__getattribute__(root, "root_ref")
            contract = object.__getattribute__(root, "contract")
            if (
                type(keyspace) is not str
                or type(binding_count) is not int
                or type(root_ref) is not str
                or type(contract) is not str
                or keyspace != expected_values[1]
                or binding_count != expected_values[3]
                or root_ref != expected_values[4]
                or contract != expected_values[5]
            ):
                return False
            pending.append(
                (object.__getattribute__(root, "root_node"), expected_values[2])
            )
            continue
        if kind in {"tuple", "list"}:
            expected_type = tuple if kind == "tuple" else list
            if type(item) is not expected_type or len(expected_values) != 2:
                return False
            values = cast(tuple[object, ...] | list[object], item)
            children = expected_values[1]
            if type(children) is not tuple or len(values) != len(children):
                return False
            pending.extend(reversed(tuple(zip(values, children, strict=True))))
            continue
        if kind == "dict":
            if type(item) is not dict or len(expected_values) != 2:
                return False
            dictionary = cast(dict[object, object], item)
            entries = expected_values[1]
            if type(entries) is not tuple or any(
                type(key) is not str for key in dictionary
            ):
                return False
            expected_entries = cast(tuple[tuple[str, object], ...], entries)
            if tuple(sorted(cast(dict[str, object], dictionary))) != tuple(
                key for key, _ in expected_entries
            ):
                return False
            pending.extend(
                reversed(
                    tuple(
                        (dictionary[key], child_guard)
                        for key, child_guard in expected_entries
                    )
                )
            )
            continue
        if kind == "enum":
            if len(expected_values) != 3:
                return False
            item_type = type(item)
            if not (
                _is_registered_exact_type(item_type, enum_types)
                and item_type is expected_values[1]
            ):
                return False
            pending.append(
                (object.__getattribute__(item, "_value_"), expected_values[2])
            )
            continue
        if kind == "nominal":
            if len(expected_values) != 3:
                return False
            item_type = type(item)
            if not (
                _is_registered_exact_type(item_type, nominal_types)
                and item_type is expected_values[1]
                and id(item) == expected_values[2]
            ):
                return False
            continue
        if kind == "reference":
            if len(expected_values) != 3:
                return False
            item_type = type(item)
            if not (
                _is_registered_exact_type(item_type, dataclass_types)
                and item_type is expected_values[1]
                and seen.get(id(item)) == expected_values[2]
            ):
                return False
            continue
        if kind != "dataclass" or len(expected_values) != 4:
            return False
        item_type = type(item)
        if not (
            _is_registered_exact_type(item_type, dataclass_types)
            and item_type is expected_values[1]
            and type(expected_values[2]) is int
            and type(expected_values[3]) is tuple
        ):
            return False
        identity = id(item)
        if identity in seen:
            return False
        seen[identity] = cast(int, expected_values[2])
        expected_fields = cast(tuple[tuple[str, object], ...], expected_values[3])
        field_names = _META_DATACLASS_FIELD_NAMES.get(item_type)
        if field_names is None or field_names != tuple(
            field_name for field_name, _ in expected_fields
        ):
            return False
        pending.extend(
            reversed(
                tuple(
                    (
                        object.__getattribute__(cast(Any, item), field_name),
                        child_guard,
                    )
                    for field_name, child_guard in expected_fields
                )
            )
        )
    return True


def _flat_protected_operand_guard(
    value: object,
    *,
    _output: list[object] | None = None,
    _seen: dict[int, int] | None = None,
) -> tuple[object, ...]:
    """Capture an exact Meta graph in one allocation-light positional stream."""

    dataclass_types, enum_types, nominal_types = _meta_operand_type_registry()
    output = [] if _output is None else _output
    seen = {} if _seen is None else _seen
    mapping_key_task = object()
    pending: list[object] = [value]
    while pending:
        item = pending.pop()
        if (
            type(item) is tuple
            and len(item) == 2
            and item[0] is mapping_key_task
        ):
            key = item[1]
            if type(key) is not str:
                raise TypeSchemaPersistentIndexError(
                    "private operation mapping keys must be exact text"
                )
            output.append(key)
            continue
        item_type = type(item)
        if item is None:
            output.append(0)
            continue
        if item_type is bool:
            output.extend((1, item))
            continue
        if item_type is int:
            output.extend((2, item))
            continue
        if item_type is float:
            output.extend((3, item.hex()))
            continue
        if item_type is str:
            output.extend((4, item))
            continue
        if item_type is bytes:
            output.extend((5, item))
            continue
        if item_type is PersistentBodyCoordinate:
            coordinate = cast(PersistentBodyCoordinate, item)
            coordinate_fields = (
                object.__getattribute__(coordinate, "schema"),
                object.__getattribute__(coordinate, "ref_field"),
                object.__getattribute__(coordinate, "authority_ref"),
                object.__getattribute__(coordinate, "body_ref"),
                object.__getattribute__(coordinate, "body_digest"),
                object.__getattribute__(coordinate, "size_bytes"),
                object.__getattribute__(coordinate, "coordinate_ref"),
                object.__getattribute__(coordinate, "contract"),
            )
            if (
                type(coordinate_fields[0]) is not str
                or type(coordinate_fields[1]) is not str
                or type(coordinate_fields[2]) is not str
                or type(coordinate_fields[3]) is not str
                or type(coordinate_fields[4]) is not str
                or type(coordinate_fields[6]) is not str
                or type(coordinate_fields[7]) is not str
            ):
                raise TypeSchemaPersistentIndexError(
                    "private operation contains foreign coordinate fields"
                )
            if type(coordinate_fields[5]) is not int:
                raise TypeSchemaPersistentIndexError(
                    "private operation contains foreign coordinate fields"
                )
            output.extend((6, *coordinate_fields))
            continue
        if item_type is PersistentBodyAuthority:
            authority = cast(PersistentBodyAuthority, item)
            coordinate = object.__getattribute__(authority, "coordinate")
            canonical_bytes = object.__getattribute__(authority, "canonical_bytes")
            if (
                type(coordinate) is not PersistentBodyCoordinate
                or type(canonical_bytes) is not bytes
            ):
                raise TypeSchemaPersistentIndexError(
                    "private operation contains foreign body authority fields"
                )
            output.extend((7, canonical_bytes))
            pending.append(coordinate)
            continue
        if item_type is PersistentIndexRoot:
            root = cast(PersistentIndexRoot, item)
            keyspace = object.__getattribute__(root, "keyspace")
            root_node = object.__getattribute__(root, "root_node")
            binding_count = object.__getattribute__(root, "binding_count")
            root_ref = object.__getattribute__(root, "root_ref")
            contract = object.__getattribute__(root, "contract")
            if (
                type(keyspace) is not str
                or type(root_node) is not PersistentBodyCoordinate
                or type(binding_count) is not int
                or type(root_ref) is not str
                or type(contract) is not str
            ):
                raise TypeSchemaPersistentIndexError(
                    "private operation contains foreign index-root fields"
                )
            output.extend((8, keyspace, binding_count, root_ref, contract))
            pending.append(root_node)
            continue
        if item_type is tuple or item_type is list:
            values = cast(tuple[object, ...] | list[object], item)
            output.extend((9 if item_type is tuple else 10, len(values)))
            pending.extend(reversed(values))
            continue
        if item_type is dict:
            dictionary = cast(dict[object, object], item)
            if any(type(key) is not str for key in dictionary):
                raise TypeSchemaPersistentIndexError(
                    "private operation mapping keys must be exact text"
                )
            entries = tuple(
                (key, dictionary[key])
                for key in sorted(cast(dict[str, object], dictionary))
            )
            output.extend((11, len(entries)))
            for key, child in reversed(entries):
                pending.extend((child, (mapping_key_task, key)))
            continue
        if _is_registered_exact_type(item_type, enum_types):
            output.extend((12, item_type))
            pending.append(object.__getattribute__(item, "_value_"))
            continue
        if _is_registered_exact_type(item_type, nominal_types):
            output.extend((13, item_type, id(item)))
            continue
        if not _is_registered_exact_type(item_type, dataclass_types):
            raise TypeSchemaPersistentIndexError(
                "private operation contains foreign or unsupported operand"
            )
        identity = id(item)
        retained_index = seen.get(identity)
        if retained_index is not None:
            output.extend((15, item_type, retained_index))
            continue
        retained_index = len(seen)
        seen[identity] = retained_index
        field_names = _META_DATACLASS_FIELD_NAMES.get(item_type)
        if field_names is None:
            field_names = tuple(field.name for field in fields(cast(Any, item)))
            _META_DATACLASS_FIELD_NAMES[item_type] = field_names
        output.extend((14, item_type, retained_index, field_names))
        pending.extend(
            object.__getattribute__(cast(Any, item), field_name)
            for field_name in reversed(field_names)
        )
    return tuple(output)


def _admit_and_detach_exact_graph(value: object) -> tuple[tuple[object, ...], object]:
    """Admit and detach one Meta operand graph in a single field traversal.

    The public transition entrances historically captured a complete mutation
    guard and then walked the same graph again to create the execution copy.
    This owner-private entrance emits the identical positional guard while it
    constructs that copy.  Exact class admission always precedes field reads;
    the returned copy carries no nominal authority and is valid only for the
    operation that retains the guard.
    """

    dataclass_types, enum_types, nominal_types = _meta_operand_type_registry()
    output: list[object] = []
    seen: dict[int, int] = {}
    detached: dict[int, object] = {}

    def admit(item: object) -> object:
        item_type = type(item)
        if item is None:
            output.append(0)
            return None
        if item_type is bool:
            output.extend((1, item))
            return item
        if item_type is int:
            output.extend((2, item))
            return item
        if item_type is float:
            output.extend((3, item.hex()))
            return item
        if item_type is str:
            output.extend((4, item))
            return item
        if item_type is bytes:
            output.extend((5, item))
            return item
        if item_type is PersistentBodyCoordinate:
            coordinate = cast(PersistentBodyCoordinate, item)
            coordinate_fields = (
                object.__getattribute__(coordinate, "schema"),
                object.__getattribute__(coordinate, "ref_field"),
                object.__getattribute__(coordinate, "authority_ref"),
                object.__getattribute__(coordinate, "body_ref"),
                object.__getattribute__(coordinate, "body_digest"),
                object.__getattribute__(coordinate, "size_bytes"),
                object.__getattribute__(coordinate, "coordinate_ref"),
                object.__getattribute__(coordinate, "contract"),
            )
            if (
                type(coordinate_fields[0]) is not str
                or type(coordinate_fields[1]) is not str
                or type(coordinate_fields[2]) is not str
                or type(coordinate_fields[3]) is not str
                or type(coordinate_fields[4]) is not str
                or type(coordinate_fields[5]) is not int
                or type(coordinate_fields[6]) is not str
                or type(coordinate_fields[7]) is not str
            ):
                raise TypeSchemaPersistentIndexError(
                    "private operation contains foreign coordinate fields"
                )
            output.extend((6, *coordinate_fields))
            result = object.__new__(PersistentBodyCoordinate)
            for field_name, field_value in zip(
                (
                    "schema",
                    "ref_field",
                    "authority_ref",
                    "body_ref",
                    "body_digest",
                    "size_bytes",
                    "coordinate_ref",
                    "contract",
                ),
                coordinate_fields,
                strict=True,
            ):
                object.__setattr__(result, field_name, field_value)
            return result
        if item_type is PersistentBodyAuthority:
            authority = cast(PersistentBodyAuthority, item)
            coordinate = object.__getattribute__(authority, "coordinate")
            canonical_bytes = object.__getattribute__(authority, "canonical_bytes")
            if (
                type(coordinate) is not PersistentBodyCoordinate
                or type(canonical_bytes) is not bytes
            ):
                raise TypeSchemaPersistentIndexError(
                    "private operation contains foreign body authority fields"
                )
            output.extend((7, canonical_bytes))
            result = object.__new__(PersistentBodyAuthority)
            object.__setattr__(result, "coordinate", admit(coordinate))
            object.__setattr__(result, "canonical_bytes", canonical_bytes)
            return result
        if item_type is PersistentIndexRoot:
            root = cast(PersistentIndexRoot, item)
            keyspace = object.__getattribute__(root, "keyspace")
            root_node = object.__getattribute__(root, "root_node")
            binding_count = object.__getattribute__(root, "binding_count")
            root_ref = object.__getattribute__(root, "root_ref")
            contract = object.__getattribute__(root, "contract")
            if (
                type(keyspace) is not str
                or type(root_node) is not PersistentBodyCoordinate
                or type(binding_count) is not int
                or type(root_ref) is not str
                or type(contract) is not str
            ):
                raise TypeSchemaPersistentIndexError(
                    "private operation contains foreign index-root fields"
                )
            output.extend((8, keyspace, binding_count, root_ref, contract))
            result = object.__new__(PersistentIndexRoot)
            object.__setattr__(result, "keyspace", keyspace)
            object.__setattr__(result, "binding_count", binding_count)
            object.__setattr__(result, "root_ref", root_ref)
            object.__setattr__(result, "contract", contract)
            object.__setattr__(result, "root_node", admit(root_node))
            return result
        if item_type is tuple:
            values = cast(tuple[object, ...], item)
            output.extend((9, len(values)))
            return tuple(admit(child) for child in values)
        if item_type is list:
            values = cast(list[object], item)
            output.extend((10, len(values)))
            result_list: list[object] = []
            result_list.extend(admit(child) for child in values)
            return result_list
        if item_type is dict:
            dictionary = cast(dict[object, object], item)
            if any(type(key) is not str for key in dictionary):
                raise TypeSchemaPersistentIndexError(
                    "private operation mapping keys must be exact text"
                )
            entries = tuple(
                (key, dictionary[key])
                for key in sorted(cast(dict[str, object], dictionary))
            )
            output.extend((11, len(entries)))
            result_dict: dict[object, object] = {}
            for key, child in entries:
                output.append(key)
                result_dict[key] = admit(child)
            return result_dict
        if _is_registered_exact_type(item_type, enum_types):
            output.extend((12, item_type))
            _ = admit(object.__getattribute__(item, "_value_"))
            return item
        if _is_registered_exact_type(item_type, nominal_types):
            output.extend((13, item_type, id(item)))
            return item
        if not _is_registered_exact_type(item_type, dataclass_types):
            raise TypeSchemaPersistentIndexError(
                "private operation contains foreign or unsupported operand"
            )
        identity = id(item)
        retained_index = seen.get(identity)
        if retained_index is not None:
            output.extend((15, item_type, retained_index))
            return detached[identity]
        retained_index = len(seen)
        seen[identity] = retained_index
        field_names = _META_DATACLASS_FIELD_NAMES.get(item_type)
        if field_names is None:
            field_names = tuple(field.name for field in fields(cast(Any, item)))
            _META_DATACLASS_FIELD_NAMES[item_type] = field_names
        output.extend((14, item_type, retained_index, field_names))
        result = object.__new__(item_type)
        detached[identity] = result
        for field_name in field_names:
            object.__setattr__(
                result,
                field_name,
                admit(object.__getattribute__(item, field_name)),
            )
        return result

    result = admit(value)
    return tuple(output), result


def _matches_flat_protected_operand_guard(
    value: object, guard: object
) -> bool:
    """Match one live Meta graph against its flat positional stream."""

    if type(guard) is not tuple:
        return False
    stream = cast(tuple[object, ...], guard)
    stream_iterator = iter(stream)
    take = stream_iterator.__next__
    seen: dict[int, int] = {}
    mapping_key_task = object()
    pending: list[object] = [value]

    try:
        while pending:
            item = pending.pop()
            if (
                type(item) is tuple
                and len(item) == 2
                and item[0] is mapping_key_task
            ):
                key = item[1]
                expected_key = take()
                if type(key) is not str or expected_key != key:
                    return False
                continue
            tag = take()
            if type(tag) is not int:
                return False
            item_type = type(item)
            if item is None:
                if tag != 0:
                    return False
                continue
            if item_type is bool:
                if tag != 1 or take() is not item:
                    return False
                continue
            if item_type is int:
                retained = take()
                if tag != 2 or type(retained) is not int or retained != item:
                    return False
                continue
            if item_type is float:
                if tag != 3 or take() != item.hex():
                    return False
                continue
            if item_type is str:
                retained = take()
                if tag != 4 or type(retained) is not str or retained != item:
                    return False
                continue
            if item_type is bytes:
                retained = take()
                if tag != 5 or type(retained) is not bytes or retained != item:
                    return False
                continue
            if item_type is PersistentBodyCoordinate:
                coordinate = cast(PersistentBodyCoordinate, item)
                actual = (
                    object.__getattribute__(coordinate, "schema"),
                    object.__getattribute__(coordinate, "ref_field"),
                    object.__getattribute__(coordinate, "authority_ref"),
                    object.__getattribute__(coordinate, "body_ref"),
                    object.__getattribute__(coordinate, "body_digest"),
                    object.__getattribute__(coordinate, "size_bytes"),
                    object.__getattribute__(coordinate, "coordinate_ref"),
                    object.__getattribute__(coordinate, "contract"),
                )
                if (
                    tag != 6
                    or take() != actual[0]
                    or take() != actual[1]
                    or take() != actual[2]
                    or take() != actual[3]
                    or take() != actual[4]
                    or take() != actual[5]
                    or take() != actual[6]
                    or take() != actual[7]
                ):
                    return False
                continue
            if item_type is PersistentBodyAuthority:
                authority = cast(PersistentBodyAuthority, item)
                canonical_bytes = object.__getattribute__(authority, "canonical_bytes")
                if tag != 7 or type(canonical_bytes) is not bytes or take() != canonical_bytes:
                    return False
                pending.append(object.__getattribute__(authority, "coordinate"))
                continue
            if item_type is PersistentIndexRoot:
                root = cast(PersistentIndexRoot, item)
                actual = (
                    object.__getattribute__(root, "keyspace"),
                    object.__getattribute__(root, "binding_count"),
                    object.__getattribute__(root, "root_ref"),
                    object.__getattribute__(root, "contract"),
                )
                if (
                    tag != 8
                    or take() != actual[0]
                    or take() != actual[1]
                    or take() != actual[2]
                    or take() != actual[3]
                ):
                    return False
                pending.append(object.__getattribute__(root, "root_node"))
                continue
            if item_type is tuple or item_type is list:
                values = cast(tuple[object, ...] | list[object], item)
                if tag != (9 if item_type is tuple else 10) or take() != len(values):
                    return False
                pending.extend(reversed(values))
                continue
            if item_type is dict:
                dictionary = cast(dict[object, object], item)
                if any(type(key) is not str for key in dictionary):
                    return False
                entries = tuple(
                    (key, dictionary[key])
                    for key in sorted(cast(dict[str, object], dictionary))
                )
                if tag != 11 or take() != len(entries):
                    return False
                for key, child in reversed(entries):
                    pending.extend((child, (mapping_key_task, key)))
                continue
            if tag == 12:
                if take() is not item_type:
                    return False
                pending.append(object.__getattribute__(item, "_value_"))
                continue
            if tag == 13:
                if (
                    take() is not item_type
                    or take() != id(item)
                ):
                    return False
                continue
            identity = id(item)
            if tag == 15:
                if not (
                    take() is item_type
                    and take() == seen.get(identity)
                ):
                    return False
                continue
            if tag != 14:
                return False
            if take() is not item_type:
                return False
            retained_index = take()
            field_names = take()
            if (
                type(retained_index) is not int
                or retained_index != len(seen)
                or identity in seen
                or type(field_names) is not tuple
            ):
                return False
            seen[identity] = retained_index
            pending.extend(
                object.__getattribute__(cast(Any, item), field_name)
                for field_name in reversed(field_names)
            )
    except StopIteration:
        return False
    try:
        take()
    except StopIteration:
        return True
    return False


@contextmanager
def _meta_type_schema_operation(
    *,
    operation_ref: str,
    operands: tuple[object, ...],
    reader: object,
    request_ref: str,
    operand_snapshot: object | None = None,
) -> Iterator[_MetaTypeSchemaOperationContext]:
    """Issue one operand-bound context after behavior-free recursive admission."""

    global _OPERATION_CONTEXT_SEQUENCE
    if type(operation_ref) is not str or operation_ref not in _OPERATION_REFS:
        raise TypeSchemaPersistentIndexError(
            "private operation ref is unsupported"
        )
    if type(operands) is not tuple:
        raise TypeSchemaPersistentIndexError(
            "private operation operands must be exact tuple"
        )
    if type(request_ref) is not str or not request_ref or request_ref.strip() != request_ref:
        raise TypeSchemaPersistentIndexError(
            "private operation request_ref must be normalized text"
        )
    from .positive_reader import TypeSchemaPositiveReaderCapability

    if type(reader) is not TypeSchemaPositiveReaderCapability:
        raise TypeSchemaPersistentIndexError(
            "private operation reader must be exact capability"
        )
    retained_request_ref = object.__getattribute__(reader, "_request_ref")
    if type(retained_request_ref) is not str or retained_request_ref != request_ref:
        raise TypeSchemaPersistentIndexError(
            "private operation reader belongs to another request"
        )
    protected_snapshot = (
        (operation_ref, _flat_protected_operand_guard(operands))
        if operand_snapshot is None
        else operand_snapshot
    )
    if (
        type(protected_snapshot) is not tuple
        or len(protected_snapshot) != 2
        or protected_snapshot[0] != operation_ref
    ):
        raise TypeSchemaPersistentIndexError(
            "private operation snapshot does not bind operation ref"
        )
    snapshot_identity = id(protected_snapshot)
    context = object.__new__(_MetaTypeSchemaOperationContext)
    with _OPERATION_CONTEXT_LOCK:
        _OPERATION_CONTEXT_SEQUENCE += 1
        sequence = _OPERATION_CONTEXT_SEQUENCE
        object.__setattr__(context, "_sequence", sequence)
        _OPERATION_CONTEXTS[id(context)] = (
            context,
            os.getpid(),
            threading.get_ident(),
            sequence,
            operation_ref,
            protected_snapshot,
            snapshot_identity,
            id(reader),
        )
        stack_key = (os.getpid(), threading.get_ident())
        _OPERATION_CONTEXT_STACKS.setdefault(stack_key, []).append(id(context))
    try:
        yield context
    finally:
        with _OPERATION_CONTEXT_LOCK:
            retained = _OPERATION_CONTEXTS.get(id(context))
            if retained is not None and retained[0] is context:
                del _OPERATION_CONTEXTS[id(context)]
            stack_key = (os.getpid(), threading.get_ident())
            stack = _OPERATION_CONTEXT_STACKS.get(stack_key)
            if stack is not None and stack and stack[-1] == id(context):
                stack.pop()
                if not stack:
                    del _OPERATION_CONTEXT_STACKS[stack_key]


def _require_meta_type_schema_operation(
    context: _MetaTypeSchemaOperationContext,
    *,
    operation_refs: frozenset[str] | None = None,
) -> None:
    if type(context) is not _MetaTypeSchemaOperationContext:
        raise TypeSchemaPersistentIndexError("private operation context is foreign")
    try:
        sequence = object.__getattribute__(context, "_sequence")
    except AttributeError as error:
        raise TypeSchemaPersistentIndexError(
            "private operation context is uninitialized"
        ) from error
    if type(sequence) is not int:
        raise TypeSchemaPersistentIndexError(
            "private operation context is uninitialized"
        )
    # Contexts are creator-thread-bound. Issuance/closure remains synchronized;
    # these exact reads cannot race with a lawful operation on another thread.
    retained = _OPERATION_CONTEXTS.get(id(context))
    stack = _OPERATION_CONTEXT_STACKS.get((os.getpid(), threading.get_ident()))
    if (
        retained is None
        or retained[0] is not context
        or retained[1] != os.getpid()
        or retained[2] != threading.get_ident()
        or retained[3] != sequence
        or id(retained[5]) != retained[6]
        or (operation_refs is not None and retained[4] not in operation_refs)
        or stack is None
        or not stack
        or stack[-1] != id(context)
    ):
        raise TypeSchemaPersistentIndexError(
            "private operation context is inactive or out of scope"
        )


def _require_meta_type_schema_operation_operands(
    context: _MetaTypeSchemaOperationContext,
    *,
    operation_ref: str,
    operands: tuple[object, ...],
) -> None:
    """Recheck protected caller operands before any public authority escapes."""

    _require_meta_type_schema_operation(context)
    retained = _OPERATION_CONTEXTS.get(id(context))
    retained_snapshot = None if retained is None else retained[5]
    retained_protected = (
        None
        if type(retained_snapshot) is not tuple or len(retained_snapshot) != 2
        else retained_snapshot[1]
    )
    if (
        retained is None
        or retained[0] is not context
        or retained[4] != operation_ref
        or not _matches_flat_protected_operand_guard(operands, retained_protected)
    ):
        raise TypeSchemaPersistentIndexError(
            "private operation operands changed after admission"
        )


def _prevalidated_json(value: object) -> bytes:
    """Encode a Meta-internal graph whose scalar/container shapes are known."""

    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _prevalidated_digest(contract: str, semantic: object) -> str:
    return "sha256:" + hashlib.sha256(
        contract.encode("utf-8") + b"\n" + _prevalidated_json(semantic)
    ).hexdigest()


def _prevalidated_node_coordinate_wire(
    coordinate: PersistentBodyCoordinate,
    *,
    include_coordinate_ref: bool,
) -> bytes:
    """Encode a freshly derived index-node coordinate without rebuilding JSON."""

    if (
        type(coordinate) is not PersistentBodyCoordinate
        or coordinate.schema != PERSISTENT_INDEX_NODE_CONTRACT
        or coordinate.ref_field != "node_ref"
    ):
        raise TypeSchemaPersistentIndexError(
            "index node coordinate must be exact"
        )
    fields = [
        b'{"authority_ref":"',
        coordinate.authority_ref.encode("ascii"),
        b'","body_digest":"',
        coordinate.body_digest.encode("ascii"),
        b'","body_ref":"',
        coordinate.body_ref.encode("ascii"),
        b'","contract":"',
        _PERSISTENT_BODY_COORDINATE_CONTRACT_BYTES,
        b'"',
    ]
    if include_coordinate_ref:
        fields.extend(
            (
                b',"coordinate_ref":"',
                coordinate.coordinate_ref.encode("ascii"),
                b'"',
            )
        )
    fields.extend(
        (
            b',"ref_field":"node_ref","schema":"',
            _PERSISTENT_INDEX_NODE_CONTRACT_BYTES,
            b'","size_bytes":',
            str(coordinate.size_bytes).encode("ascii"),
            b"}",
        )
    )
    return b"".join(fields)


def _prevalidated_index_node_semantic_bytes(
    *,
    keyspace: str,
    depth: int,
    path: str,
    children: tuple[PersistentIndexChild, ...],
    key: str | None,
    value: PersistentBodyCoordinate | None,
    child_coordinate_fragments: dict[str, tuple[object, bytes, bytes]] | None = None,
    encoded_keyspace: bytes | None = None,
) -> bytes:
    """Assemble the fixed canonical node schema from already admitted values."""

    output = bytearray(b'{"children":[')
    for index, child in enumerate(children):
        if index:
            output.extend(b",")
        output.extend(b'{"nibble":"')
        output.extend(child.nibble.encode("ascii"))
        output.extend(b'","node":')
        output.extend(
            child_coordinate_fragments[child.node.coordinate_ref][2]
            if child_coordinate_fragments is not None
            and child.node.coordinate_ref in child_coordinate_fragments
            else _prevalidated_node_coordinate_wire(
                child.node,
                include_coordinate_ref=True,
            )
        )
        output.extend(b"}")
    output.extend(
        b"".join(
        (
            b'],"contract":"',
            _PERSISTENT_INDEX_NODE_CONTRACT_BYTES,
            b'","depth":',
            _PERSISTENT_INDEX_DEPTH_BYTES[depth],
            b',"key":',
            b"null" if key is None else _prevalidated_json(key),
            b',"keyspace":',
            _prevalidated_json(keyspace)
            if encoded_keyspace is None
            else encoded_keyspace,
            b',"path":"',
            path.encode("ascii"),
            b'","value":',
            b"null" if value is None else _prevalidated_json(value.to_wire()),
            b"}",
        )
        )
    )
    return bytes(output)


def _decoded_coordinate_ref(
    *,
    contract: str,
    schema: str,
    ref_field: str,
    authority_ref: str,
    body_ref: str,
    body_digest: str,
    size_bytes: int,
) -> str:
    """Recompute a decoded coordinate without rebuilding its JSON graph."""

    string_fields = (
        authority_ref,
        body_digest,
        body_ref,
        contract,
        ref_field,
        schema,
    )
    combined_fields = "".join(string_fields)
    if (
        combined_fields.isascii()
        and combined_fields.isprintable()
        and '"' not in combined_fields
        and "\\" not in combined_fields
    ):
        semantic_bytes = (
            '{"authority_ref":"'
            + authority_ref
            + '","body_digest":"'
            + body_digest
            + '","body_ref":"'
            + body_ref
            + '","contract":"'
            + contract
            + '","ref_field":"'
            + ref_field
            + '","schema":"'
            + schema
            + '","size_bytes":'
            + str(size_bytes)
            + "}"
        ).encode("ascii")
        return "sha256:" + hashlib.sha256(
            contract.encode("utf-8") + b"\n" + semantic_bytes
        ).hexdigest()
    return _prevalidated_digest(
        contract,
        {
            "contract": contract,
            "schema": schema,
            "ref_field": ref_field,
            "authority_ref": authority_ref,
            "body_ref": body_ref,
            "body_digest": body_digest,
            "size_bytes": size_bytes,
        },
    )


class TypeSchemaPersistentIndexError(ValueError):
    """Raised when persistent index authority is malformed or substituted."""


def _token(value: str, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value.strip() != value
        or _WHITESPACE(value) is not None
    ):
        raise TypeSchemaPersistentIndexError(f"{field} must be a nonempty token")
    return value


def _digest(value: str, field: str) -> str:
    value = _token(value, field)
    if not value.startswith("sha256:") or len(value) != 71 or value != value.lower():
        raise TypeSchemaPersistentIndexError(f"{field} must be a SHA-256 digest")
    try:
        int(value[7:], 16)
    except ValueError as error:
        raise TypeSchemaPersistentIndexError(
            f"{field} must be a SHA-256 digest"
        ) from error
    return value


def _count(value: int, field: str) -> int:
    if type(value) is not int or value < 0:
        raise TypeSchemaPersistentIndexError(f"{field} must be non-negative int")
    return value


def key_digest_path(key: str) -> str:
    """Return the fixed 64-nibble path for one normalized semantic key."""

    return hashlib.sha256(_token(key, "key").encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class PersistentBodyCoordinate:
    schema: str
    ref_field: str
    authority_ref: str
    body_ref: str
    body_digest: str
    size_bytes: int
    coordinate_ref: str
    contract: str = PERSISTENT_BODY_COORDINATE_CONTRACT

    def __post_init__(self) -> None:
        if self.contract != PERSISTENT_BODY_COORDINATE_CONTRACT:
            raise TypeSchemaPersistentIndexError("body coordinate contract unsupported")
        for field in ("schema", "ref_field", "authority_ref", "body_ref"):
            object.__setattr__(self, field, _token(getattr(self, field), field))
        expected_ref_field = _BODY_ROLE_BY_SCHEMA.get(self.schema)
        if expected_ref_field is None or self.ref_field != expected_ref_field:
            raise TypeSchemaPersistentIndexError(
                "body coordinate schema/ref-field role is unsupported"
            )
        object.__setattr__(
            self, "body_digest", _digest(self.body_digest, "body_digest")
        )
        expected_body_ref = (
            f"cas://aware-meta-type-schema/{self.body_digest.removeprefix('sha256:')}"
        )
        if self.body_ref != expected_body_ref:
            raise TypeSchemaPersistentIndexError(
                f"body_ref is not canonical; expected {expected_body_ref}"
            )
        _count(self.size_bytes, "size_bytes")
        expected = _prevalidated_digest(self.contract, self.semantic_wire())
        if self.coordinate_ref != expected:
            raise TypeSchemaPersistentIndexError(
                f"coordinate_ref mismatch; expected {expected}"
            )

    @classmethod
    def create(
        cls,
        *,
        schema: str,
        ref_field: str,
        authority_ref: str,
        body_digest: str,
        size_bytes: int,
    ) -> PersistentBodyCoordinate:
        body_digest = _digest(body_digest, "body_digest")
        normalized_schema = _token(schema, "schema")
        normalized_ref_field = _token(ref_field, "ref_field")
        normalized_authority_ref = _token(authority_ref, "authority_ref")
        body_ref = f"cas://aware-meta-type-schema/{body_digest[7:]}"
        normalized_size = _count(size_bytes, "size_bytes")
        semantic = {
            "contract": PERSISTENT_BODY_COORDINATE_CONTRACT,
            "schema": normalized_schema,
            "ref_field": normalized_ref_field,
            "authority_ref": normalized_authority_ref,
            "body_ref": body_ref,
            "body_digest": body_digest,
            "size_bytes": normalized_size,
        }
        return cls(
            normalized_schema,
            normalized_ref_field,
            normalized_authority_ref,
            body_ref,
            body_digest,
            normalized_size,
            _prevalidated_digest(PERSISTENT_BODY_COORDINATE_CONTRACT, semantic),
        )

    def semantic_wire(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "schema": self.schema,
            "ref_field": self.ref_field,
            "authority_ref": self.authority_ref,
            "body_ref": self.body_ref,
            "body_digest": self.body_digest,
            "size_bytes": self.size_bytes,
        }

    def to_wire(self) -> dict[str, object]:
        return {**self.semantic_wire(), "coordinate_ref": self.coordinate_ref}


@dataclass(frozen=True, slots=True)
class PersistentBodyAuthority:
    """One immutable CAS-ready canonical body; this value performs no write."""

    coordinate: PersistentBodyCoordinate
    canonical_bytes: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.coordinate, PersistentBodyCoordinate):
            raise TypeError("coordinate must be PersistentBodyCoordinate")
        if type(self.canonical_bytes) is not bytes:
            raise TypeError("canonical_bytes must be exact bytes")
        actual_digest = "sha256:" + hashlib.sha256(self.canonical_bytes).hexdigest()
        if actual_digest != self.coordinate.body_digest:
            raise TypeSchemaPersistentIndexError("body bytes digest mismatch")
        if len(self.canonical_bytes) != self.coordinate.size_bytes:
            raise TypeSchemaPersistentIndexError("body bytes size mismatch")
        value = _canonical_object(self.canonical_bytes)
        if value.get("contract") != self.coordinate.schema:
            raise TypeSchemaPersistentIndexError("body schema mismatch")
        if value.get(self.coordinate.ref_field) != self.coordinate.authority_ref:
            raise TypeSchemaPersistentIndexError("body authority ref mismatch")

    @classmethod
    def from_wire(
        cls,
        *,
        schema: str,
        ref_field: str,
        authority_ref: str,
        wire: dict[str, object],
    ) -> PersistentBodyAuthority:
        canonical_bytes = canonical_json(wire).encode("utf-8")
        body_digest = "sha256:" + hashlib.sha256(canonical_bytes).hexdigest()
        return cls(
            PersistentBodyCoordinate.create(
                schema=schema,
                ref_field=ref_field,
                authority_ref=authority_ref,
                body_digest=body_digest,
                size_bytes=len(canonical_bytes),
            ),
            canonical_bytes,
        )


@dataclass(frozen=True, slots=True)
class PersistentIndexChild:
    nibble: str
    node: PersistentBodyCoordinate

    def __post_init__(self) -> None:
        if self.nibble not in _HEX or len(self.nibble) != 1:
            raise TypeSchemaPersistentIndexError("child nibble must be lowercase hex")
        if not isinstance(self.node, PersistentBodyCoordinate):
            raise TypeError("child node must be PersistentBodyCoordinate")
        if self.node.schema != PERSISTENT_INDEX_NODE_CONTRACT:
            raise TypeSchemaPersistentIndexError("child must reference index node")

    def to_wire(self) -> dict[str, object]:
        return {"nibble": self.nibble, "node": self.node.to_wire()}


@dataclass(frozen=True, slots=True)
class PersistentIndexNode:
    keyspace: str
    depth: int
    path: str
    children: tuple[PersistentIndexChild, ...]
    key: str | None
    value: PersistentBodyCoordinate | None
    node_ref: str
    contract: str = PERSISTENT_INDEX_NODE_CONTRACT

    def __post_init__(self) -> None:
        if self.contract != PERSISTENT_INDEX_NODE_CONTRACT:
            raise TypeSchemaPersistentIndexError("index node contract unsupported")
        object.__setattr__(self, "keyspace", _token(self.keyspace, "keyspace"))
        _count(self.depth, "depth")
        if self.depth > PERSISTENT_INDEX_DEPTH:
            raise TypeSchemaPersistentIndexError("node depth exceeds fixed index depth")
        if (
            not isinstance(self.path, str)
            or len(self.path) != self.depth
            or _NON_HEX(self.path) is not None
        ):
            raise TypeSchemaPersistentIndexError("node path does not match depth")
        if type(self.children) is not tuple:
            raise TypeSchemaPersistentIndexError(
                "node children must be immutable tuple"
            )
        children = tuple(sorted(self.children, key=lambda item: item.nibble))
        if children != self.children or any(
            not isinstance(item, PersistentIndexChild) for item in children
        ):
            raise TypeSchemaPersistentIndexError(
                "node children must be typed and sorted"
            )
        nibbles = tuple(item.nibble for item in children)
        if len(nibbles) != len(set(nibbles)):
            raise TypeSchemaPersistentIndexError("node child nibbles must be unique")
        if self.depth == PERSISTENT_INDEX_DEPTH:
            if children or self.key is None or self.value is None:
                raise TypeSchemaPersistentIndexError(
                    "leaf requires exactly one key/value and no children"
                )
            object.__setattr__(self, "key", _token(self.key, "key"))
            if key_digest_path(self.key) != self.path:
                raise TypeSchemaPersistentIndexError("leaf key does not match path")
            if not isinstance(self.value, PersistentBodyCoordinate):
                raise TypeError("leaf value must be PersistentBodyCoordinate")
        elif self.key is not None or self.value is not None:
            raise TypeSchemaPersistentIndexError(
                "non-leaf node cannot contain key/value"
            )
        expected = _prevalidated_digest(self.contract, self.semantic_wire())
        if self.node_ref != expected:
            raise TypeSchemaPersistentIndexError(
                f"node_ref mismatch; expected {expected}"
            )

    @classmethod
    def create(
        cls,
        *,
        keyspace: str,
        depth: int,
        path: str,
        children: tuple[PersistentIndexChild, ...] = (),
        key: str | None = None,
        value: PersistentBodyCoordinate | None = None,
    ) -> PersistentIndexNode:
        children = tuple(sorted(children, key=lambda item: item.nibble))
        normalized_keyspace = _token(keyspace, "keyspace")
        normalized_depth = _count(depth, "depth")
        semantic = {
            "contract": PERSISTENT_INDEX_NODE_CONTRACT,
            "keyspace": normalized_keyspace,
            "depth": normalized_depth,
            "path": path,
            "children": [item.to_wire() for item in children],
            "key": key,
            "value": None if value is None else value.to_wire(),
        }
        return cls(
            normalized_keyspace,
            normalized_depth,
            path,
            children,
            key,
            value,
            _prevalidated_digest(PERSISTENT_INDEX_NODE_CONTRACT, semantic),
        )

    def semantic_wire(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "keyspace": self.keyspace,
            "depth": self.depth,
            "path": self.path,
            "children": [item.to_wire() for item in self.children],
            "key": self.key,
            "value": None if self.value is None else self.value.to_wire(),
        }

    def to_wire(self) -> dict[str, object]:
        return {**self.semantic_wire(), "node_ref": self.node_ref}

    def to_body(self) -> PersistentBodyAuthority:
        return PersistentBodyAuthority.from_wire(
            schema=self.contract,
            ref_field="node_ref",
            authority_ref=self.node_ref,
            wire=self.to_wire(),
        )


@dataclass(frozen=True, slots=True)
class PersistentIndexRoot:
    keyspace: str
    root_node: PersistentBodyCoordinate
    binding_count: int
    root_ref: str
    contract: str = PERSISTENT_INDEX_ROOT_CONTRACT

    def __post_init__(self) -> None:
        if self.contract != PERSISTENT_INDEX_ROOT_CONTRACT:
            raise TypeSchemaPersistentIndexError("index root contract unsupported")
        object.__setattr__(self, "keyspace", _token(self.keyspace, "keyspace"))
        if not isinstance(self.root_node, PersistentBodyCoordinate):
            raise TypeError("root_node must be PersistentBodyCoordinate")
        if self.root_node.schema != PERSISTENT_INDEX_NODE_CONTRACT:
            raise TypeSchemaPersistentIndexError("root must reference index node")
        _count(self.binding_count, "binding_count")
        expected = _prevalidated_digest(self.contract, self.semantic_wire())
        if self.root_ref != expected:
            raise TypeSchemaPersistentIndexError(
                f"root_ref mismatch; expected {expected}"
            )

    @classmethod
    def create(
        cls,
        *,
        keyspace: str,
        root_node: PersistentBodyCoordinate,
        binding_count: int,
    ) -> PersistentIndexRoot:
        normalized_keyspace = _token(keyspace, "keyspace")
        normalized_count = _count(binding_count, "binding_count")
        semantic = {
            "contract": PERSISTENT_INDEX_ROOT_CONTRACT,
            "keyspace": normalized_keyspace,
            "root_node": root_node.to_wire(),
            "binding_count": normalized_count,
        }
        return cls(
            normalized_keyspace,
            root_node,
            normalized_count,
            _prevalidated_digest(PERSISTENT_INDEX_ROOT_CONTRACT, semantic),
        )

    def semantic_wire(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "keyspace": self.keyspace,
            "root_node": self.root_node.to_wire(),
            "binding_count": self.binding_count,
        }

    def to_wire(self) -> dict[str, object]:
        return {**self.semantic_wire(), "root_ref": self.root_ref}


def create_empty_persistent_index(
    keyspace: str,
) -> tuple[PersistentIndexRoot, tuple[PersistentBodyAuthority, ...]]:
    node = PersistentIndexNode.create(keyspace=keyspace, depth=0, path="")
    body = node.to_body()
    root = PersistentIndexRoot.create(
        keyspace=keyspace,
        root_node=body.coordinate,
        binding_count=0,
    )
    return root, (body,)


def _create_prevalidated_index_node_body(
    context: _MetaTypeSchemaOperationContext,
    *,
    keyspace: str,
    depth: int,
    path: str,
    children: tuple[PersistentIndexChild, ...] = (),
    key: str | None = None,
    value: PersistentBodyCoordinate | None = None,
) -> tuple[PersistentIndexNode, PersistentBodyAuthority]:
    """Create a node/body already derived by Meta's private patch walker.

    Public constructors remain the strict admission surface. This helper only
    removes their repeated validation and parse of a value the fixed-depth
    walker has just derived. Canonical bytes and every digest remain fresh.
    """

    _require_meta_type_schema_operation(context)
    keyspace = _token(keyspace, "keyspace")
    depth = _count(depth, "depth")
    if type(path) is not str or len(path) != depth or _NON_HEX(path) is not None:
        raise TypeSchemaPersistentIndexError("node path does not match depth")
    if depth > PERSISTENT_INDEX_DEPTH:
        raise TypeSchemaPersistentIndexError("node depth exceeds fixed index depth")
    if type(children) is not tuple or any(
        type(item) is not PersistentIndexChild for item in children
    ):
        raise TypeSchemaPersistentIndexError(
            "node children must be exact immutable values"
        )
    if any(
        type(item.nibble) is not str
        or type(item.node) is not PersistentBodyCoordinate
        for item in children
    ):
        raise TypeSchemaPersistentIndexError(
            "node children contain foreign nested values"
        )
    if value is not None and type(value) is not PersistentBodyCoordinate:
        raise TypeSchemaPersistentIndexError("node value must be exact coordinate")
    if depth == PERSISTENT_INDEX_DEPTH:
        if children or type(key) is not str or value is None:
            raise TypeSchemaPersistentIndexError(
                "leaf requires exactly one key/value and no children"
            )
        if key_digest_path(key) != path:
            raise TypeSchemaPersistentIndexError("leaf key does not match path")
    elif key is not None or value is not None:
        raise TypeSchemaPersistentIndexError(
            "non-leaf node cannot contain key/value"
        )
    normalized_children = tuple(sorted(children, key=lambda item: item.nibble))
    if len({item.nibble for item in normalized_children}) != len(
        normalized_children
    ):
        raise TypeSchemaPersistentIndexError("node child nibbles must be unique")
    semantic_bytes = _prevalidated_index_node_semantic_bytes(
        keyspace=keyspace,
        depth=depth,
        path=path,
        children=normalized_children,
        key=key,
        value=value,
    )
    node_ref = "sha256:" + hashlib.sha256(
        PERSISTENT_INDEX_NODE_CONTRACT.encode("utf-8")
        + b"\n"
        + semantic_bytes
    ).hexdigest()
    node = object.__new__(PersistentIndexNode)
    object.__setattr__(node, "keyspace", keyspace)
    object.__setattr__(node, "depth", depth)
    object.__setattr__(node, "path", path)
    object.__setattr__(node, "children", normalized_children)
    object.__setattr__(node, "key", key)
    object.__setattr__(node, "value", value)
    object.__setattr__(node, "node_ref", node_ref)
    object.__setattr__(node, "contract", PERSISTENT_INDEX_NODE_CONTRACT)

    # Canonical key order places ``node_ref`` immediately before ``path``.
    # Insert the freshly derived ASCII digest into the already canonical
    # semantic bytes instead of normalizing and serializing the same deep
    # child-coordinate graph a second time.
    path_marker = b',"path":'
    path_offset = semantic_bytes.find(path_marker)
    if path_offset < 0:
        raise AssertionError("canonical node semantics must contain path")
    canonical_bytes = (
        semantic_bytes[:path_offset]
        + b',"node_ref":"'
        + node_ref.encode("ascii")
        + b'"'
        + semantic_bytes[path_offset:]
    )
    body_digest = "sha256:" + hashlib.sha256(canonical_bytes).hexdigest()
    body_ref = f"cas://aware-meta-type-schema/{body_digest[7:]}"
    coordinate = object.__new__(PersistentBodyCoordinate)
    object.__setattr__(coordinate, "schema", PERSISTENT_INDEX_NODE_CONTRACT)
    object.__setattr__(coordinate, "ref_field", "node_ref")
    object.__setattr__(coordinate, "authority_ref", node_ref)
    object.__setattr__(coordinate, "body_ref", body_ref)
    object.__setattr__(coordinate, "body_digest", body_digest)
    object.__setattr__(coordinate, "size_bytes", len(canonical_bytes))
    coordinate_semantic_bytes = _prevalidated_node_coordinate_wire(
        coordinate,
        include_coordinate_ref=False,
    )
    object.__setattr__(
        coordinate,
        "coordinate_ref",
        "sha256:"
        + hashlib.sha256(
            PERSISTENT_BODY_COORDINATE_CONTRACT.encode("utf-8")
            + b"\n"
            + coordinate_semantic_bytes
        ).hexdigest(),
    )
    object.__setattr__(coordinate, "contract", PERSISTENT_BODY_COORDINATE_CONTRACT)
    body = object.__new__(PersistentBodyAuthority)
    object.__setattr__(body, "coordinate", coordinate)
    object.__setattr__(body, "canonical_bytes", canonical_bytes)
    return node, body


def _create_prevalidated_body_authority(
    context: _MetaTypeSchemaOperationContext,
    *,
    schema: str,
    ref_field: str,
    authority_ref: str,
    wire: dict[str, object],
) -> PersistentBodyAuthority:
    """Encode one already-admitted Meta value as its ordinary body authority."""

    _require_meta_type_schema_operation(context)
    schema = _token(schema, "schema")
    ref_field = _token(ref_field, "ref_field")
    authority_ref = _token(authority_ref, "authority_ref")
    if _BODY_ROLE_BY_SCHEMA.get(schema) != ref_field:
        raise TypeSchemaPersistentIndexError("body schema/ref-field role mismatch")
    if type(wire) is not dict:
        raise TypeSchemaPersistentIndexError("body wire must be exact mapping")
    _protected_operand_wire(wire)
    if wire.get("contract") != schema or wire.get(ref_field) != authority_ref:
        raise TypeSchemaPersistentIndexError(
            "body wire does not bind schema and authority ref"
        )
    canonical_bytes = _prevalidated_json(wire)
    body_digest = "sha256:" + hashlib.sha256(canonical_bytes).hexdigest()
    body_ref = f"cas://aware-meta-type-schema/{body_digest[7:]}"
    coordinate_semantic = {
        "contract": PERSISTENT_BODY_COORDINATE_CONTRACT,
        "schema": schema,
        "ref_field": ref_field,
        "authority_ref": authority_ref,
        "body_ref": body_ref,
        "body_digest": body_digest,
        "size_bytes": len(canonical_bytes),
    }
    coordinate = object.__new__(PersistentBodyCoordinate)
    object.__setattr__(coordinate, "schema", schema)
    object.__setattr__(coordinate, "ref_field", ref_field)
    object.__setattr__(coordinate, "authority_ref", authority_ref)
    object.__setattr__(coordinate, "body_ref", body_ref)
    object.__setattr__(coordinate, "body_digest", body_digest)
    object.__setattr__(coordinate, "size_bytes", len(canonical_bytes))
    object.__setattr__(
        coordinate,
        "coordinate_ref",
        _prevalidated_digest(PERSISTENT_BODY_COORDINATE_CONTRACT, coordinate_semantic),
    )
    object.__setattr__(coordinate, "contract", PERSISTENT_BODY_COORDINATE_CONTRACT)
    body = object.__new__(PersistentBodyAuthority)
    object.__setattr__(body, "coordinate", coordinate)
    object.__setattr__(body, "canonical_bytes", canonical_bytes)
    return body


def _create_prevalidated_index_root(
    context: _MetaTypeSchemaOperationContext,
    *,
    keyspace: str,
    root_node: PersistentBodyCoordinate,
    binding_count: int,
) -> PersistentIndexRoot:
    """Create a root from the private patch walker's freshly issued node."""

    _require_meta_type_schema_operation(context)
    keyspace = _token(keyspace, "keyspace")
    if type(root_node) is not PersistentBodyCoordinate:
        raise TypeSchemaPersistentIndexError("root node must be exact coordinate")
    _protected_operand_wire(root_node)
    if root_node.schema != PERSISTENT_INDEX_NODE_CONTRACT:
        raise TypeSchemaPersistentIndexError("root must reference index node")
    binding_count = _count(binding_count, "binding_count")
    semantic = {
        "contract": PERSISTENT_INDEX_ROOT_CONTRACT,
        "keyspace": keyspace,
        "root_node": root_node.to_wire(),
        "binding_count": binding_count,
    }
    result = object.__new__(PersistentIndexRoot)
    object.__setattr__(result, "keyspace", keyspace)
    object.__setattr__(result, "root_node", root_node)
    object.__setattr__(result, "binding_count", binding_count)
    object.__setattr__(
        result,
        "root_ref",
        _prevalidated_digest(PERSISTENT_INDEX_ROOT_CONTRACT, semantic),
    )
    object.__setattr__(result, "contract", PERSISTENT_INDEX_ROOT_CONTRACT)
    return result


def decode_persistent_index_node(payload: bytes) -> PersistentIndexNode:
    item = _canonical_object(payload)
    _exact(
        item,
        {
            "contract",
            "keyspace",
            "depth",
            "path",
            "children",
            "key",
            "value",
            "node_ref",
        },
        "node",
    )
    if item["contract"] != PERSISTENT_INDEX_NODE_CONTRACT:
        raise TypeSchemaPersistentIndexError("index node schema unsupported")
    raw_children = _array(item, "children")
    children_values: list[PersistentIndexChild] = []
    for index, raw in enumerate(raw_children):
        child = _object(raw, f"children[{index}]")
        _exact(child, {"nibble", "node"}, f"children[{index}]")
        nibble = _text(child, "nibble")
        if nibble not in _HEX or len(nibble) != 1:
            raise TypeSchemaPersistentIndexError(
                "child nibble must be lowercase hex"
            )
        child_value = object.__new__(PersistentIndexChild)
        object.__setattr__(child_value, "nibble", nibble)
        object.__setattr__(
            child_value,
            "node",
            persistent_body_coordinate_from_wire(child["node"]),
        )
        children_values.append(child_value)
    children = tuple(children_values)
    raw_value = item["value"]
    value = (
        None
        if raw_value is None
        else persistent_body_coordinate_from_wire(raw_value)
    )
    keyspace = _token(_text(item, "keyspace"), "keyspace")
    depth = _count(_integer(item, "depth"), "depth")
    path = _text_allow_empty(item, "path")
    key = _optional_text(item, "key")
    node_ref = _text(item, "node_ref")
    if depth > PERSISTENT_INDEX_DEPTH:
        raise TypeSchemaPersistentIndexError("node depth exceeds fixed index depth")
    if len(path) != depth or _NON_HEX(path) is not None:
        raise TypeSchemaPersistentIndexError("node path does not match depth")
    if children != tuple(sorted(children, key=lambda child: child.nibble)):
        raise TypeSchemaPersistentIndexError(
            "node children must be typed and sorted"
        )
    nibbles = tuple(child.nibble for child in children)
    if len(nibbles) != len(set(nibbles)):
        raise TypeSchemaPersistentIndexError("node child nibbles must be unique")
    if depth == PERSISTENT_INDEX_DEPTH:
        if children or key is None or value is None:
            raise TypeSchemaPersistentIndexError(
                "leaf requires exactly one key/value and no children"
            )
        key = _token(key, "key")
        if key_digest_path(key) != path:
            raise TypeSchemaPersistentIndexError("leaf key does not match path")
    elif key is not None or value is not None:
        raise TypeSchemaPersistentIndexError(
            "non-leaf node cannot contain key/value"
        )

    marker = b',"node_ref":"'
    marker_offset = payload.find(marker)
    encoded_ref = node_ref.encode("utf-8")
    ref_end = marker_offset + len(marker) + len(encoded_ref)
    if (
        marker_offset < 0
        or payload.find(marker, marker_offset + 1) >= 0
        or payload[marker_offset + len(marker) : ref_end] != encoded_ref
        or payload[ref_end : ref_end + 1] != b'"'
    ):
        raise TypeSchemaPersistentIndexError("node_ref is not canonical")
    semantic_bytes = payload[:marker_offset] + payload[ref_end + 1 :]
    expected_ref = "sha256:" + hashlib.sha256(
        PERSISTENT_INDEX_NODE_CONTRACT.encode("utf-8") + b"\n" + semantic_bytes
    ).hexdigest()
    if node_ref != expected_ref:
        raise TypeSchemaPersistentIndexError(
            f"node_ref mismatch; expected {expected_ref}"
        )
    result = object.__new__(PersistentIndexNode)
    object.__setattr__(result, "keyspace", keyspace)
    object.__setattr__(result, "depth", depth)
    object.__setattr__(result, "path", path)
    object.__setattr__(result, "children", children)
    object.__setattr__(result, "key", key)
    object.__setattr__(result, "value", value)
    object.__setattr__(result, "node_ref", node_ref)
    object.__setattr__(result, "contract", PERSISTENT_INDEX_NODE_CONTRACT)
    return result


def persistent_index_root_from_wire(raw: object) -> PersistentIndexRoot:
    item = _object(raw, "root")
    _exact(
        item,
        {"contract", "keyspace", "root_node", "binding_count", "root_ref"},
        "root",
    )
    return PersistentIndexRoot(
        keyspace=_text(item, "keyspace"),
        root_node=persistent_body_coordinate_from_wire(item["root_node"]),
        binding_count=_integer(item, "binding_count"),
        root_ref=_text(item, "root_ref"),
        contract=_text(item, "contract"),
    )


def persistent_body_coordinate_from_wire(raw: object) -> PersistentBodyCoordinate:
    item = _object(raw, "coordinate")
    _exact(
        item,
        {
            "contract",
            "schema",
            "ref_field",
            "authority_ref",
            "body_ref",
            "body_digest",
            "size_bytes",
            "coordinate_ref",
        },
        "coordinate",
    )
    contract = _text(item, "contract")
    schema = _text(item, "schema")
    ref_field = _text(item, "ref_field")
    authority_ref = _text(item, "authority_ref")
    body_ref = _text(item, "body_ref")
    decoded_tokens = (schema, ref_field, authority_ref, body_ref)
    if not all(decoded_tokens) or _WHITESPACE("\0".join(decoded_tokens)) is not None:
        schema = _token(schema, "schema")
        ref_field = _token(ref_field, "ref_field")
        authority_ref = _token(authority_ref, "authority_ref")
        body_ref = _token(body_ref, "body_ref")
    body_digest = _text(item, "body_digest")
    try:
        if (
            len(body_digest) != 71
            or not body_digest.startswith("sha256:")
            or body_digest != body_digest.lower()
        ):
            raise ValueError
        int(body_digest[7:], 16)
    except ValueError:
        body_digest = _digest(body_digest, "body_digest")
    size_bytes = _integer(item, "size_bytes")
    if size_bytes < 0:
        size_bytes = _count(size_bytes, "size_bytes")
    coordinate_ref = _text(item, "coordinate_ref")
    if contract != PERSISTENT_BODY_COORDINATE_CONTRACT:
        raise TypeSchemaPersistentIndexError("body coordinate contract unsupported")
    expected_ref_field = _BODY_ROLE_BY_SCHEMA.get(schema)
    if expected_ref_field is None or ref_field != expected_ref_field:
        raise TypeSchemaPersistentIndexError(
            "body coordinate schema/ref-field role is unsupported"
        )
    expected_body_ref = (
        f"cas://aware-meta-type-schema/{body_digest.removeprefix('sha256:')}"
    )
    if body_ref != expected_body_ref:
        raise TypeSchemaPersistentIndexError(
            f"body_ref is not canonical; expected {expected_body_ref}"
        )
    expected_coordinate_ref = _decoded_coordinate_ref(
        contract=contract,
        schema=schema,
        ref_field=ref_field,
        authority_ref=authority_ref,
        body_ref=body_ref,
        body_digest=body_digest,
        size_bytes=size_bytes,
    )
    if coordinate_ref != expected_coordinate_ref:
        raise TypeSchemaPersistentIndexError(
            f"coordinate_ref mismatch; expected {expected_coordinate_ref}"
        )
    result = object.__new__(PersistentBodyCoordinate)
    object.__setattr__(result, "schema", schema)
    object.__setattr__(result, "ref_field", ref_field)
    object.__setattr__(result, "authority_ref", authority_ref)
    object.__setattr__(result, "body_ref", body_ref)
    object.__setattr__(result, "body_digest", body_digest)
    object.__setattr__(result, "size_bytes", size_bytes)
    object.__setattr__(result, "coordinate_ref", coordinate_ref)
    object.__setattr__(result, "contract", contract)
    return result


def _canonical_object(payload: bytes) -> dict[str, object]:
    if type(payload) is not bytes:
        raise TypeError("persistent body must be exact bytes")
    try:
        value = json.loads(payload.decode("utf-8"), object_pairs_hook=_no_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise TypeSchemaPersistentIndexError(
            "body is not canonical UTF-8 JSON"
        ) from error
    if not isinstance(value, dict):
        raise TypeSchemaPersistentIndexError("body must be a JSON object")
    # ``json.loads`` has already reduced the wire to exact built-in JSON
    # scalars/containers and the owning decoder validates every field below.
    # Re-encoding that graph directly is byte-equivalent to ``canonical_json``
    # without recursively normalizing the same node a second time.
    if _prevalidated_json(value) != payload:
        raise TypeSchemaPersistentIndexError("body is not canonical JSON")
    return value


def _no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise TypeSchemaPersistentIndexError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _object(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TypeSchemaPersistentIndexError(f"{field} must be object")
    return value


def _array(value: dict[str, object], field: str) -> list[object]:
    result = value.get(field)
    if not isinstance(result, list):
        raise TypeSchemaPersistentIndexError(f"{field} must be array")
    return result


def _text(value: dict[str, object], field: str) -> str:
    result = value.get(field)
    if not isinstance(result, str) or not result:
        raise TypeSchemaPersistentIndexError(f"{field} must be text")
    return result


def _text_allow_empty(value: dict[str, object], field: str) -> str:
    result = value.get(field)
    if not isinstance(result, str):
        raise TypeSchemaPersistentIndexError(f"{field} must be text")
    return result


def _optional_text(value: dict[str, object], field: str) -> str | None:
    result = value.get(field)
    if result is not None and not isinstance(result, str):
        raise TypeSchemaPersistentIndexError(f"{field} must be text or null")
    return result


def _integer(value: dict[str, object], field: str) -> int:
    result = value.get(field)
    if type(result) is not int:
        raise TypeSchemaPersistentIndexError(f"{field} must be int")
    return result


def _exact(value: dict[str, object], expected: set[str], field: str) -> None:
    actual = set(value)
    if actual != expected:
        raise TypeSchemaPersistentIndexError(
            f"{field} fields are not exact; "
            f"missing={sorted(expected - actual)!r}, extra={sorted(actual - expected)!r}"
        )


__all__ = [
    "PERSISTENT_BODY_COORDINATE_CONTRACT",
    "PERSISTENT_INDEX_DEPTH",
    "PERSISTENT_INDEX_NODE_CONTRACT",
    "PERSISTENT_INDEX_ROOT_CONTRACT",
    "PersistentBodyAuthority",
    "PersistentBodyCoordinate",
    "PersistentIndexChild",
    "PersistentIndexNode",
    "PersistentIndexRoot",
    "TypeSchemaPersistentIndexError",
    "create_empty_persistent_index",
    "decode_persistent_index_node",
    "key_digest_path",
    "persistent_body_coordinate_from_wire",
    "persistent_index_root_from_wire",
]
