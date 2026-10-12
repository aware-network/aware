"""Meta-owned coordination for one package/catalog/composed operation."""

from __future__ import annotations

import builtins as _python_builtins
import operator
import os
import threading
import weakref
from collections.abc import Callable
from dataclasses import dataclass, field, fields
from time import perf_counter_ns
from types import MemberDescriptorType
from typing import Self

from .composed_slice_advancement import (
    _PREVALIDATED_SLICE_ADMISSION_TOKEN,
    AdmittedTypeSchemaComposedSlice,
    _admit_prevalidated_composed_slice,
    _slice_admission_context,
)
from .composition import TypeSchemaComposedSlice
from .composition_codec import encode_composition_value
from .composition_transition import (
    TypeSchemaCatalogTransition,
    TypeSchemaPackageTransition,
)
from .persistent_index import (
    _META_DATACLASS_FIELD_NAMES,
    PersistentBodyAuthority,
    PersistentBodyCoordinate,
    PersistentIndexNode,
    TypeSchemaPersistentIndexError,
    _flat_protected_operand_guard,
    _is_registered_exact_type,
    _matches_flat_protected_operand_guard,
    _matches_protected_operand_guard,
    _meta_operand_type_registry,
    _prevalidated_json,
    _protected_operand_wire,
)
from .positive_reader import (
    _PREVALIDATED_PROOF_BUNDLE_ADMISSION_TOKEN,
    _OperationBodyFragmentArena,
    _OperationDecodedNodeArena,
    _reader_coordinate_values,
)


@dataclass(frozen=True, slots=True)
class _ResultEvidence:
    value: object
    canonical_bytes: bytes
    guard: object
    guard_matcher: Callable[[object, object], bool]
    module_globals: dict[str, object]
    matcher_globals: dict[str, object]
    absent_builtin_names: tuple[str, ...]
    matcher_absent_builtin_names: tuple[str, ...]
    present_bindings: tuple[tuple[str, object], ...]
    matcher_present_bindings: tuple[tuple[str, object], ...]
    dict_contains: Callable[..., object]
    dict_getitem: Callable[..., object]


@dataclass(frozen=True, slots=True)
class _TransitionResultGuard:
    value_type: type[object]
    prefix: tuple[object, ...]
    prefix_guard: tuple[object, ...]
    emitted_bodies: tuple[PersistentBodyAuthority, ...]
    coordinate_fragments: (
        dict[str, tuple[object, bytes, bytes]] | _OperationBodyFragmentArena
    )


@dataclass(frozen=True, slots=True)
class _ComposedResultGuard:
    values: tuple[object, ...]
    schemas: tuple[
        tuple[type[object], int, tuple[MemberDescriptorType, ...]], ...
    ]


def _matches_retained_coordinate_values(
    value: PersistentBodyCoordinate,
    retained: tuple[str, str, str, str, str, int, str, str],
    _fields: Callable[[object], tuple[object, ...]] = operator.attrgetter(
        "schema",
        "ref_field",
        "authority_ref",
        "body_ref",
        "body_digest",
        "size_bytes",
        "coordinate_ref",
        "contract",
    ),
) -> bool:
    """Compare an already admitted coordinate without repeating format admission."""

    if type(value) is not PersistentBodyCoordinate:
        return False
    try:
        current = _fields(value)
    except AttributeError:
        return False
    return (
        type(current[0]) is str
        and type(current[1]) is str
        and type(current[2]) is str
        and type(current[3]) is str
        and type(current[4]) is str
        and type(current[5]) is int
        and type(current[6]) is str
        and type(current[7]) is str
        and current == retained
    )


def _composed_result_guard(
    value: object,
    *,
    _type: Callable[[object], type[object]] = type,
    _id: Callable[[object], int] = id,
    _object_getattribute: Callable[..., object] = object.__getattribute__,
    _type_getattribute: Callable[..., object] = type.__getattribute__,
    _descriptor_type: type[MemberDescriptorType] = MemberDescriptorType,
    _descriptor_get: Callable[..., object] = MemberDescriptorType.__get__,
) -> _ComposedResultGuard:
    """Capture one admitted composed graph as a compact exact identity stream."""

    dataclass_types, enum_types, nominal_types = _meta_operand_type_registry()
    values: list[object] = []
    schemas: list[
        tuple[type[object], int, tuple[MemberDescriptorType, ...]]
    ] = []
    schema_by_type_id: dict[
        int, tuple[int, type[object], int, tuple[MemberDescriptorType, ...]]
    ] = {}
    seen: set[int] = set()
    pending = [value]
    while pending:
        item = pending.pop()
        values.append(item)
        item_type = _type(item)
        if (
            item is None
            or item_type is bool
            or item_type is int
            or item_type is float
            or item_type is str
            or item_type is bytes
        ):
            continue
        identity = _id(item)
        if identity in seen:
            continue
        seen.add(identity)
        if item_type is tuple:
            pending.extend(reversed(item))
            continue
        if item_type is list:
            pending.extend(reversed(item))
            continue
        if item_type is dict:
            if any(_type(key) is not str for key in item):
                raise TypeSchemaPersistentIndexError(
                    "private operation mapping keys must be exact text"
                )
            for key in sorted(item, reverse=True):
                pending.append(item[key])
                pending.append(key)
            continue
        schema_entry = schema_by_type_id.get(_id(item_type))
        if schema_entry is None or schema_entry[1] is not item_type:
            if _is_registered_exact_type(item_type, enum_types):
                kind = 1
                descriptors: tuple[MemberDescriptorType, ...] = ()
            elif _is_registered_exact_type(item_type, nominal_types):
                kind = 2
                descriptors = ()
            elif _is_registered_exact_type(item_type, dataclass_types):
                kind = 3
                field_names = _META_DATACLASS_FIELD_NAMES.get(item_type)
                if field_names is None:
                    field_names = tuple(field.name for field in fields(item))
                    _META_DATACLASS_FIELD_NAMES[item_type] = field_names
                descriptor_values = tuple(
                    _type_getattribute(item_type, field_name)
                    for field_name in field_names
                )
                if any(
                    _type(descriptor) is not _descriptor_type
                    for descriptor in descriptor_values
                ):
                    raise TypeSchemaPersistentIndexError(
                        "private operation dataclass fields must use exact slots"
                    )
                descriptors = descriptor_values
            else:
                raise TypeSchemaPersistentIndexError(
                    "private operation contains foreign or unsupported operand"
                )
            schema_index = len(schemas)
            schema = (item_type, kind, descriptors)
            schemas.append(schema)
            schema_by_type_id[_id(item_type)] = (
                schema_index,
                item_type,
                kind,
                descriptors,
            )
        else:
            _, _, kind, descriptors = schema_entry
        if kind == 1:
            pending.append(_object_getattribute(item, "_value_"))
        elif kind == 3:
            for descriptor in reversed(descriptors):
                pending.append(_descriptor_get(descriptor, item, item_type))
    return _ComposedResultGuard(tuple(values), tuple(schemas))


def _matches_composed_result_guard(
    value: object,
    guard: object,
    *,
    _type: Callable[[object], type[object]] = type,
    _id: Callable[[object], int] = id,
    _object_getattribute: Callable[..., object] = object.__getattribute__,
    _descriptor_get: Callable[..., object] = MemberDescriptorType.__get__,
) -> bool:
    """Verify the complete visible graph against its exact identity stream."""

    if _type(guard) is not _ComposedResultGuard:
        return False
    expected = iter(guard.values)
    schemas = {
        _id(value_type): (value_type, kind, descriptors)
        for value_type, kind, descriptors in guard.schemas
    }
    seen: set[int] = set()
    pending = [value]
    try:
        while pending:
            item = pending.pop()
            if item is not next(expected):
                return False
            item_type = _type(item)
            if (
                item is None
                or item_type is bool
                or item_type is int
                or item_type is float
                or item_type is str
                or item_type is bytes
            ):
                continue
            identity = _id(item)
            if identity in seen:
                continue
            seen.add(identity)
            if item_type is tuple or item_type is list:
                pending.extend(reversed(item))
                continue
            if item_type is dict:
                if any(_type(key) is not str for key in item):
                    return False
                for key in sorted(item, reverse=True):
                    pending.append(item[key])
                    pending.append(key)
                continue
            schema = schemas.get(_id(item_type))
            if schema is None or schema[0] is not item_type:
                return False
            _, kind, descriptors = schema
            if kind == 1:
                pending.append(_object_getattribute(item, "_value_"))
            elif kind == 3:
                for descriptor in reversed(descriptors):
                    pending.append(_descriptor_get(descriptor, item, item_type))
            elif kind != 2:
                return False
        next(expected)
    except StopIteration:
        return not pending
    except (AttributeError, KeyError, TypeError, ValueError):
        return False
    return False


def _transition_result_guard(
    value: object,
    coordinate_fragments: (
        dict[str, tuple[object, bytes, bytes]]
        | _OperationBodyFragmentArena
        | None
    ) = None,
) -> _TransitionResultGuard:
    value_type = type(value)
    if value_type is TypeSchemaPackageTransition:
        transition = value
        prefix = (
            transition.prior,
            transition.successor,
            transition.definition_lifecycle,
            transition.attribution_lifecycle,
            transition.definition_movement_refs,
            transition.attribution_movement_refs,
            transition.reused_coordinates,
            transition.transition_ref,
            transition.observation,
            transition.contract,
        )
        emitted = transition.emitted_bodies
    elif value_type is TypeSchemaCatalogTransition:
        transition = value
        prefix = (
            transition.prior_ref,
            transition.successor,
            transition.package_movement_refs,
            transition.owner_movement_refs,
            transition.reused_coordinates,
            transition.transition_ref,
            transition.observation,
            transition.contract,
        )
        emitted = transition.emitted_bodies
    else:
        raise TypeError("Meta transition result guard type is unsupported")
    if type(emitted) is not tuple:
        raise TypeError("Meta transition emitted bodies must be exact tuple")
    if coordinate_fragments is None:
        coordinate_fragments = {}
    for body in emitted:
        if type(body) is not PersistentBodyAuthority:
            raise TypeError("Meta transition emitted body must be exact")
        coordinate = object.__getattribute__(body, "coordinate")
        canonical_bytes = object.__getattribute__(body, "canonical_bytes")
        if (
            type(coordinate) is not PersistentBodyCoordinate
            or type(canonical_bytes) is not bytes
        ):
            raise TypeError("Meta transition emitted body fields must be exact")
        coordinate_ref = object.__getattribute__(coordinate, "coordinate_ref")
        retained = coordinate_fragments.get(coordinate_ref)
        if (
            retained is None
            or type(retained[0]) is not tuple
            or len(retained[0]) != 8
            or retained[1] != canonical_bytes
            or not _matches_retained_coordinate_values(coordinate, retained[0])
        ):
            coordinate_values = _reader_coordinate_values(coordinate)
            coordinate_fragments[coordinate_ref] = (
                coordinate_values,
                canonical_bytes,
                _prevalidated_json(coordinate.to_wire()),
            )
    return _TransitionResultGuard(
        value_type,
        prefix,
        _flat_protected_operand_guard(prefix),
        emitted,
        coordinate_fragments,
    )


def _matches_transition_result_guard(value: object, guard: object) -> bool:
    if type(guard) is not _TransitionResultGuard or type(value) is not guard.value_type:
        return False
    if guard.value_type is TypeSchemaPackageTransition:
        transition = value
        prefix = (
            transition.prior,
            transition.successor,
            transition.definition_lifecycle,
            transition.attribution_lifecycle,
            transition.definition_movement_refs,
            transition.attribution_movement_refs,
            transition.reused_coordinates,
            transition.transition_ref,
            transition.observation,
            transition.contract,
        )
        emitted = transition.emitted_bodies
    else:
        transition = value
        prefix = (
            transition.prior_ref,
            transition.successor,
            transition.package_movement_refs,
            transition.owner_movement_refs,
            transition.reused_coordinates,
            transition.transition_ref,
            transition.observation,
            transition.contract,
        )
        emitted = transition.emitted_bodies
    if (
        type(emitted) is not tuple
        or emitted is not guard.emitted_bodies
        or not _matches_flat_protected_operand_guard(prefix, guard.prefix_guard)
    ):
        return False
    try:
        for body in emitted:
            if type(body) is not PersistentBodyAuthority:
                return False
            coordinate = object.__getattribute__(body, "coordinate")
            canonical_bytes = object.__getattribute__(body, "canonical_bytes")
            if type(coordinate) is not PersistentBodyCoordinate:
                return False
            retained = guard.coordinate_fragments.get(
                object.__getattribute__(coordinate, "coordinate_ref")
            )
            if (
                retained is None
                or not _matches_retained_coordinate_values(coordinate, retained[0])
                or type(canonical_bytes) is not bytes
                or canonical_bytes != retained[1]
            ):
                return False
    except (AttributeError, TypeError, ValueError):
        return False
    return True


class _MetaTypeSchemaOperation:
    __slots__ = ()

    def __new__(cls) -> Self:
        raise TypeError("Meta TypeSchema operation is runtime-issued")


class _MetaTypeSchemaOperationWitness:
    __slots__ = ()

    def __new__(cls) -> Self:
        raise TypeError("Meta TypeSchema witness is runtime-issued")


@dataclass(slots=True)
class _OperationState:
    operation: _MetaTypeSchemaOperation
    process_id: int
    thread_id: int
    package_transition: _ResultEvidence | None = None
    dependency_package_transitions: list[_ResultEvidence] = field(
        default_factory=list
    )
    detached_package_successors: list[
        tuple[TypeSchemaPackageTransition, object]
    ] = field(default_factory=list)
    catalog_transition: _ResultEvidence | None = None
    composed_bodies: dict[int, _ResultEvidence] = field(default_factory=dict)
    decoded_nodes: dict[
        str,
        tuple[
            tuple[str, str, str, str, str, int, str, str],
            bytes,
            PersistentIndexNode,
        ],
    ] = field(default_factory=_OperationDecodedNodeArena)
    diagnostics: list[tuple[str, int]] = field(default_factory=list)
    lifecycle: str = "active"


@dataclass(slots=True)
class _WitnessState:
    witness: _MetaTypeSchemaOperationWitness
    process_id: int
    thread_id: int
    package_transition: _ResultEvidence
    catalog_transition: _ResultEvidence
    composed_slice: _ResultEvidence
    canonical_bytes: bytes
    admission: AdmittedTypeSchemaComposedSlice
    body_fragments: _OperationBodyFragmentArena
    coordinate_wires: dict[int, tuple[PersistentBodyCoordinate, bytes]]
    diagnostics: list[tuple[str, int]]
    lifecycle: str = "active"


_LOCK = threading.RLock()
_OPERATIONS: dict[int, _OperationState] = {}
_WITNESSES: dict[int, _WitnessState] = {}
_ADMISSION_PACKAGE_TRANSITIONS: weakref.WeakKeyDictionary[
    AdmittedTypeSchemaComposedSlice, _ResultEvidence
] = weakref.WeakKeyDictionary()
_ADMISSION_COMPOSED_EVIDENCE: weakref.WeakKeyDictionary[
    AdmittedTypeSchemaComposedSlice, _ResultEvidence
] = weakref.WeakKeyDictionary()
_ADMISSION_DIAGNOSTICS: weakref.WeakKeyDictionary[
    AdmittedTypeSchemaComposedSlice, tuple[tuple[str, int], ...]
] = weakref.WeakKeyDictionary()
_TYPE_SCHEMA_OPERATION_MODULE_GLOBALS: dict[str, object] = globals()
_RETAINED_GUARD_MATCHER = _matches_protected_operand_guard
_RETAINED_GUARD_MATCHER_GLOBALS = _matches_protected_operand_guard.__globals__
_RETAINED_DICT_CONTAINS = dict.__contains__
_RETAINED_DICT_GETITEM = dict.__getitem__
_RESULT_VERIFIER_ABSENT_BUILTIN_NAMES = tuple(
    name
    for name in vars(_python_builtins)
    if name not in _TYPE_SCHEMA_OPERATION_MODULE_GLOBALS
)
_MATCHER_ABSENT_BUILTIN_NAMES = tuple(
    name
    for name in vars(_python_builtins)
    if name not in _RETAINED_GUARD_MATCHER_GLOBALS
)
def _canonical_result_evidence(
    value: object,
    canonical_bytes: bytes,
    *,
    _captured_guard: object | None = None,
    _transition_coordinate_fragments: dict[
        str, tuple[object, bytes, bytes]
    ]
    | None = None,
    _type: Callable[[object], type[object]] = type,
    _dict_contains: Callable[..., object] = dict.__contains__,
    _dict_getitem: Callable[..., object] = dict.__getitem__,
    _any: Callable[..., bool] = any,
    _retained_type: Callable[[object], type[object]] = type,
    _error_type: type[TypeError] = TypeError,
    _module_globals: dict[str, object] = _TYPE_SCHEMA_OPERATION_MODULE_GLOBALS,
    _matcher_globals: dict[str, object] = _matches_protected_operand_guard.__globals__,
    _absent_builtin_names: tuple[str, ...] = _RESULT_VERIFIER_ABSENT_BUILTIN_NAMES,
    _matcher_absent_builtin_names: tuple[
        str, ...
    ] = _MATCHER_ABSENT_BUILTIN_NAMES,
    _guard_matcher: Callable[
        [object, object], bool
    ] = _matches_flat_protected_operand_guard,
    _protected_wire: Callable[[object], object] = _flat_protected_operand_guard,
    _persistent_error: type[TypeSchemaPersistentIndexError] = TypeSchemaPersistentIndexError,
    _result_evidence_type: type[_ResultEvidence] = _ResultEvidence,
    _transition_guard: Callable[
        [object, dict[str, tuple[object, bytes, bytes]] | None],
        _TransitionResultGuard,
    ] = _transition_result_guard,
    _transition_matcher: Callable[[object, object], bool] = _matches_transition_result_guard,
    _composed_guard: Callable[[object], _ComposedResultGuard] = _composed_result_guard,
    _composed_matcher: Callable[[object, object], bool] = _matches_composed_result_guard,
    _expected_present_bindings: tuple[tuple[str, object], ...] = (
        ("_matches_protected_operand_guard", _matches_protected_operand_guard),
        ("_RETAINED_GUARD_MATCHER", _matches_protected_operand_guard),
        (
            "_RETAINED_GUARD_MATCHER_GLOBALS",
            _matches_protected_operand_guard.__globals__,
        ),
        ("_protected_operand_wire", _protected_operand_wire),
        ("_flat_protected_operand_guard", _flat_protected_operand_guard),
        (
            "_matches_flat_protected_operand_guard",
            _matches_flat_protected_operand_guard,
        ),
        (
            "_matches_retained_coordinate_values",
            _matches_retained_coordinate_values,
        ),
        ("_composed_result_guard", _composed_result_guard),
        ("_matches_composed_result_guard", _matches_composed_result_guard),
        ("_ComposedResultGuard", _ComposedResultGuard),
        ("_ResultEvidence", _ResultEvidence),
        ("_RETAINED_DICT_CONTAINS", dict.__contains__),
        ("_RETAINED_DICT_GETITEM", dict.__getitem__),
        ("_TYPE_SCHEMA_OPERATION_MODULE_GLOBALS", _TYPE_SCHEMA_OPERATION_MODULE_GLOBALS),
        (
            "_RESULT_VERIFIER_ABSENT_BUILTIN_NAMES",
            _RESULT_VERIFIER_ABSENT_BUILTIN_NAMES,
        ),
        ("_MATCHER_ABSENT_BUILTIN_NAMES", _MATCHER_ABSENT_BUILTIN_NAMES),
    ),
    _expected_matcher_bindings: tuple[tuple[str, object], ...] = (
        (
            "_meta_operand_type_registry",
            dict.__getitem__(
                _matches_protected_operand_guard.__globals__,
                "_meta_operand_type_registry",
            ),
        ),
        (
            "_is_registered_exact_type",
            dict.__getitem__(
                _matches_protected_operand_guard.__globals__,
                "_is_registered_exact_type",
            ),
        ),
        (
            "_META_DATACLASS_FIELD_NAMES",
            dict.__getitem__(
                _matches_protected_operand_guard.__globals__,
                "_META_DATACLASS_FIELD_NAMES",
            ),
        ),
        (
            "PersistentBodyCoordinate",
            dict.__getitem__(
                _matches_protected_operand_guard.__globals__,
                "PersistentBodyCoordinate",
            ),
        ),
        (
            "PersistentBodyAuthority",
            dict.__getitem__(
                _matches_protected_operand_guard.__globals__,
                "PersistentBodyAuthority",
            ),
        ),
        (
            "PersistentIndexRoot",
            dict.__getitem__(
                _matches_protected_operand_guard.__globals__,
                "PersistentIndexRoot",
            ),
        ),
        (
            "cast",
            dict.__getitem__(_matches_protected_operand_guard.__globals__, "cast"),
        ),
    ),
) -> _ResultEvidence:
    module_globals = _module_globals
    matcher_globals = _matcher_globals
    absent_builtin_names = _absent_builtin_names
    matcher_absent_builtin_names = _matcher_absent_builtin_names
    if _type(canonical_bytes) is not bytes:
        raise _error_type("Meta result canonical body must be exact bytes")
    if (
        _type is not _retained_type
        or _any(_dict_contains(module_globals, name) for name in absent_builtin_names)
        or _any(
            _dict_contains(matcher_globals, name)
            for name in matcher_absent_builtin_names
        )
        or _any(
            not _dict_contains(module_globals, name)
            or _dict_getitem(module_globals, name) is not expected
            for name, expected in _expected_present_bindings
        )
        or _any(
            not _dict_contains(matcher_globals, name)
            or _dict_getitem(matcher_globals, name) is not expected
            for name, expected in _expected_matcher_bindings
        )
    ):
        raise _error_type("Meta result verification primitive changed")
    if _captured_guard is None:
        try:
            if type(value) is TypeSchemaPackageTransition or type(
                value
            ) is TypeSchemaCatalogTransition:
                guard = _transition_guard(value, _transition_coordinate_fragments)
                guard_matcher = _transition_matcher
            elif type(value) is TypeSchemaComposedSlice:
                guard = _composed_guard(value)
                guard_matcher = _composed_matcher
            else:
                guard = _protected_wire(value)
                guard_matcher = _guard_matcher
        except _persistent_error as error:
            raise _error_type("Meta result graph is not exactly admitted") from error
    else:
        guard = _captured_guard
        guard_matcher = _guard_matcher
    if (
        type(guard) is not tuple
        and type(guard) is not _TransitionResultGuard
        and type(guard) is not _ComposedResultGuard
    ):
        raise TypeError("Meta result guard is invalid")
    return _result_evidence_type(
        value,
        canonical_bytes,
        guard,
        guard_matcher,
        module_globals,
        matcher_globals,
        absent_builtin_names,
        matcher_absent_builtin_names,
        _expected_present_bindings,
        _expected_matcher_bindings,
        _dict_contains,
        _dict_getitem,
    )


def _admit_composed_slice_for_head_transfer(
    value: TypeSchemaComposedSlice,
    canonical_bytes: bytes,
) -> AdmittedTypeSchemaComposedSlice:
    """Strictly admit one existing slice for immediate Ontology head transfer."""

    if type(value) is not TypeSchemaComposedSlice or type(canonical_bytes) is not bytes:
        raise TypeError("Meta head-transfer evidence must be exact")
    if encode_composition_value(value) != canonical_bytes:
        raise ValueError("Meta head-transfer composed slice bytes differ")
    admission = _admit_prevalidated_composed_slice(
        value,
        canonical_bytes,
        _token=_PREVALIDATED_SLICE_ADMISSION_TOKEN,
    )
    _ADMISSION_COMPOSED_EVIDENCE[admission] = _canonical_result_evidence(
        value, canonical_bytes
    )
    return admission


def _require_result_evidence(
    evidence: _ResultEvidence,
    value: object,
    *,
    _type: Callable[[object], type[object]] = type,
    _evidence_type: type[_ResultEvidence] = _ResultEvidence,
    _object_getattribute: Callable[..., object] = object.__getattribute__,
    _any: Callable[..., bool] = any,
    _error_type: type[ValueError] = ValueError,
) -> None:
    if _type(evidence) is not _evidence_type:
        raise _error_type("Meta result changed after owner admission")
    module_globals = evidence.module_globals
    matcher_globals = evidence.matcher_globals
    dict_contains = evidence.dict_contains
    dict_getitem = evidence.dict_getitem
    if (
        _any(
            dict_contains(module_globals, name)
            for name in evidence.absent_builtin_names
        )
        or _any(
            dict_contains(matcher_globals, name)
            for name in evidence.matcher_absent_builtin_names
        )
        or _any(
            not dict_contains(module_globals, name)
            or dict_getitem(module_globals, name) is not expected
            for name, expected in evidence.present_bindings
        )
        or _any(
            not dict_contains(matcher_globals, name)
            or dict_getitem(matcher_globals, name) is not expected
            for name, expected in evidence.matcher_present_bindings
        )
    ):
        raise _error_type("Meta result verification primitive changed")
    if (
        evidence.value is not value
    ):
        raise _error_type("Meta result changed after owner admission")
    matcher = evidence.guard_matcher
    if not matcher(value, evidence.guard):
        raise _error_type("Meta result changed after owner admission")


def _terminate_operation(state: _OperationState) -> None:
    state.lifecycle = "terminal"
    _OPERATIONS.pop(id(state.operation), None)


def _require_operation(
    value: _MetaTypeSchemaOperation,
    *,
    _type: Callable[[object], type[object]] = type,
    _operation_type: type[_MetaTypeSchemaOperation] = _MetaTypeSchemaOperation,
    _any: Callable[..., bool] = any,
    _dict_contains: Callable[..., object] = dict.__contains__,
    _module_globals: dict[str, object] = _TYPE_SCHEMA_OPERATION_MODULE_GLOBALS,
    _absent_builtin_names: tuple[
        str, ...
    ] = _RESULT_VERIFIER_ABSENT_BUILTIN_NAMES,
    _type_error: type[TypeError] = TypeError,
    _value_error: type[ValueError] = ValueError,
    _operations: dict[int, _OperationState] = _OPERATIONS,
    _id: Callable[..., int] = id,
) -> _OperationState:
    if _any(
        _dict_contains(_module_globals, name) for name in _absent_builtin_names
    ):
        poisoned = _operations.get(_id(value))
        if poisoned is not None and poisoned.operation is value:
            poisoned.lifecycle = "terminal"
            _operations.pop(_id(value), None)
        raise _value_error("Meta result verification primitive changed")
    if _type(value) is not _operation_type:
        raise _type_error("Meta TypeSchema operation must be exact")
    state = _OPERATIONS.get(id(value))
    if (
        state is None
        or state.operation is not value
        or state.process_id != os.getpid()
        or state.thread_id != threading.get_ident()
        or state.lifecycle != "active"
    ):
        raise _value_error("Meta TypeSchema operation is not active")
    return state


def _open_type_schema_operation() -> _MetaTypeSchemaOperation:
    with _LOCK:
        value = object.__new__(_MetaTypeSchemaOperation)
        key = id(value)
        if key in _OPERATIONS:
            raise ValueError("Meta TypeSchema operation identity collision")
        _OPERATIONS[key] = _OperationState(value, os.getpid(), threading.get_ident())
        return value


def _record_type_schema_package_transition(
    operation: _MetaTypeSchemaOperation,
    transition: TypeSchemaPackageTransition,
    canonical_bytes: bytes,
) -> None:
    with _LOCK:
        state = _require_operation(operation)
        try:
            if (
                type(transition) is not TypeSchemaPackageTransition
                or type(canonical_bytes) is not bytes
            ):
                raise TypeError("Meta package transition evidence must be exact")
            if state.package_transition is not None:
                raise ValueError("Meta package transition was already recorded")
            state.package_transition = _canonical_result_evidence(
                transition,
                canonical_bytes,
                _transition_coordinate_fragments=state.decoded_nodes.body_fragments,
            )
        except Exception:
            _terminate_operation(state)
            raise


def _type_schema_operation_package_transition_body(
    operation: _MetaTypeSchemaOperation,
    transition: TypeSchemaPackageTransition,
) -> bytes:
    """Return Meta's admitted bytes for this operation's package result."""

    with _LOCK:
        state = _require_operation(operation)
        try:
            evidence = state.package_transition
            if (
                type(transition) is not TypeSchemaPackageTransition
                or type(evidence) is not _ResultEvidence
                or evidence.value is not transition
            ):
                raise ValueError("Meta package transition result differs")
            _require_result_evidence(evidence, transition)
            return evidence.canonical_bytes
        except Exception:
            _terminate_operation(state)
            raise


def _admit_type_schema_operation_dependency_package(
    operation: _MetaTypeSchemaOperation,
    admission: AdmittedTypeSchemaComposedSlice,
    transition: TypeSchemaPackageTransition,
) -> None:
    """Admit one dependency package result already sealed by Meta."""

    with _LOCK:
        state = _require_operation(operation)
        try:
            retained = _slice_admission_context(admission)
            evidence = _ADMISSION_PACKAGE_TRANSITIONS.get(admission)
            if (
                type(transition) is not TypeSchemaPackageTransition
                or type(evidence) is not _ResultEvidence
                or not any(
                    item.package_ref == transition.successor.package_ref
                    and item.package.package_root_ref
                    == transition.successor.package_root_ref
                    for item in retained.slice.packages
                )
            ):
                raise ValueError(
                    "Meta dependency package result is not admitted"
                )
            _require_result_evidence(evidence, evidence.value)
            # A decoded dependency closure carries a fresh portable transition
            # graph.  It is admitted by the ordinary catalog-transition
            # entrance below; only the exact Meta-issued result participates
            # in the operation-local identity fast path.
            if evidence.value is not transition:
                return
            state.dependency_package_transitions.append(
                evidence
            )
        except Exception:
            _terminate_operation(state)
            raise


def _type_schema_operation_decoded_nodes(
    operation: _MetaTypeSchemaOperation,
) -> dict[
    str,
    tuple[
        tuple[str, str, str, str, str, int, str, str],
        bytes,
        PersistentIndexNode,
    ],
]:
    """Return the private node arena owned by one active Meta operation."""

    with _LOCK:
        return _require_operation(operation).decoded_nodes


def _record_type_schema_operation_diagnostic(
    operation: _MetaTypeSchemaOperation,
    name: str,
    duration_ns: int,
) -> None:
    """Record one nonportable, event-derived owner span."""

    if type(name) is not str or not name or type(duration_ns) is not int:
        raise TypeError("Meta operation diagnostic must be exact")
    if duration_ns < 0:
        raise ValueError("Meta operation diagnostic must be nonnegative")
    with _LOCK:
        _require_operation(operation).diagnostics.append((name, duration_ns))


def _type_schema_operation_admission_diagnostics(
    admission: AdmittedTypeSchemaComposedSlice,
) -> tuple[tuple[str, int], ...]:
    """Read diagnostics retained for the exact successor admission."""

    with _LOCK:
        diagnostics = _ADMISSION_DIAGNOSTICS.get(admission)
        if diagnostics is None:
            raise ValueError("Meta operation diagnostics are absent")
        return diagnostics


def _record_type_schema_catalog_transition(
    operation: _MetaTypeSchemaOperation,
    transition: TypeSchemaCatalogTransition,
    canonical_bytes: bytes,
) -> None:
    with _LOCK:
        state = _require_operation(operation)
        try:
            if (
                type(transition) is not TypeSchemaCatalogTransition
                or type(canonical_bytes) is not bytes
            ):
                raise TypeError("Meta catalog transition evidence must be exact")
            if state.package_transition is None or state.catalog_transition is not None:
                raise ValueError("Meta catalog transition ordering differs")
            state.catalog_transition = _canonical_result_evidence(
                transition,
                canonical_bytes,
                _transition_coordinate_fragments=state.decoded_nodes.body_fragments,
            )
        except Exception:
            _terminate_operation(state)
            raise


def _is_recorded_type_schema_catalog_successor(
    operation: _MetaTypeSchemaOperation,
    catalog: object,
) -> bool:
    """Correlate the fresh catalog successor inside the same Meta operation."""

    with _LOCK:
        state = _require_operation(operation)
        evidence = state.catalog_transition
        return (
            type(evidence) is _ResultEvidence
            and type(evidence.value) is TypeSchemaCatalogTransition
            and evidence.value.successor is catalog
        )


def _is_recorded_type_schema_package_successor(
    operation: _MetaTypeSchemaOperation,
    transition: TypeSchemaPackageTransition,
    successor: object,
) -> bool:
    """Correlate a package successor inside the same active Meta operation."""

    with _LOCK:
        state = _require_operation(operation)
        evidence = state.package_transition
        return (
            type(transition) is TypeSchemaPackageTransition
            and (
                (
                    type(evidence) is _ResultEvidence
                    and evidence.value is transition
                    or any(
                        item.value is transition
                        for item in state.dependency_package_transitions
                    )
                )
                and transition.successor is successor
                or any(
                    item_transition is transition and item_successor is successor
                    for item_transition, item_successor in (
                        state.detached_package_successors
                    )
                )
            )
        )


def _record_type_schema_operation_detached_package_successor(
    operation: _MetaTypeSchemaOperation,
    original: TypeSchemaPackageTransition,
    detached: TypeSchemaPackageTransition,
) -> None:
    """Correlate one trusted detached transition with its admitted original."""

    with _LOCK:
        state = _require_operation(operation)
        package_evidence = state.package_transition
        admitted = (
            type(package_evidence) is _ResultEvidence
            and package_evidence.value is original
        ) or any(
            item.value is original for item in state.dependency_package_transitions
        )
        if (
            not admitted
            or type(detached) is not TypeSchemaPackageTransition
            or detached.transition_ref != original.transition_ref
            or detached.successor.package_root_ref
            != original.successor.package_root_ref
        ):
            _terminate_operation(state)
            raise ValueError("detached Meta package result differs")
        state.detached_package_successors.append((detached, detached.successor))


def _operation_bootstrap_package_movements(
    operation: _MetaTypeSchemaOperation,
    movements: object,
) -> object | None:
    """Shallow-project fresh Meta successors for one bootstrap catalog patch.

    The package transition results were created and admitted by this same
    active Meta operation.  Catalog patching serializes their successor roots
    into persistent bodies and retains no movement or transition object, so a
    second encode/decode of each complete transition graph is unnecessary.
    Non-bootstrap movements retain the strict detachment path.
    """

    from .composition_transition import PackageRootMovement

    if type(movements) is not tuple:
        return None
    with _LOCK:
        state = _require_operation(operation)
        admitted = tuple(
            evidence
            for evidence in (
                state.package_transition,
                *state.dependency_package_transitions,
            )
            if type(evidence) is _ResultEvidence
        )
        projected: list[PackageRootMovement] = []
        for movement in movements:
            if (
                type(movement) is not PackageRootMovement
                or movement.prior is not None
                or type(movement.transition) is not TypeSchemaPackageTransition
                or movement.next is not movement.transition.successor
                or not any(
                    evidence.value is movement.transition for evidence in admitted
                )
            ):
                return None
            value = object.__new__(PackageRootMovement)
            object.__setattr__(value, "package_ref", movement.package_ref)
            object.__setattr__(value, "prior", None)
            object.__setattr__(value, "next", movement.next)
            object.__setattr__(value, "transition", movement.transition)
            projected.append(value)
        return tuple(projected)


def _record_type_schema_composed_slice(
    operation: _MetaTypeSchemaOperation,
    value: TypeSchemaComposedSlice,
    canonical_bytes: bytes,
) -> None:
    with _LOCK:
        state = _require_operation(operation)
        try:
            if (
                type(value) is not TypeSchemaComposedSlice
                or type(canonical_bytes) is not bytes
            ):
                raise TypeError("Meta composed-slice result evidence must be exact")
            package_evidence = state.package_transition
            catalog_evidence = state.catalog_transition
            evidence = _canonical_result_evidence(
                value, canonical_bytes
            )
            if (
                type(package_evidence) is not _ResultEvidence
                or type(package_evidence.value) is not TypeSchemaPackageTransition
                or type(catalog_evidence) is not _ResultEvidence
                or type(catalog_evidence.value) is not TypeSchemaCatalogTransition
                or object.__getattribute__(
                    object.__getattribute__(value, "catalog"), "catalog_ref"
                )
                != catalog_evidence.value.successor.catalog_ref
                or not any(
                    object.__getattribute__(item, "package_ref")
                    == package_evidence.value.successor.package_ref
                    and object.__getattribute__(
                        object.__getattribute__(item, "package"),
                        "package_root_ref",
                    )
                    == package_evidence.value.successor.package_root_ref
                    for item in object.__getattribute__(value, "packages")
                )
            ):
                raise ValueError(
                    "Meta composed successor differs from recorded transitions"
                )
            state.composed_bodies[id(value)] = evidence
        except Exception:
            _terminate_operation(state)
            raise


def _finish_type_schema_operation(
    operation: _MetaTypeSchemaOperation,
    composed_slice: TypeSchemaComposedSlice,
    *,
    predecessor_admission: AdmittedTypeSchemaComposedSlice | None = None,
) -> _MetaTypeSchemaOperationWitness:
    finish_started = perf_counter_ns()
    with _LOCK:
        state = _require_operation(operation)
        try:
            package_evidence = state.package_transition
            catalog_evidence = state.catalog_transition
            if (
                type(package_evidence) is not _ResultEvidence
                or type(package_evidence.value) is not TypeSchemaPackageTransition
                or type(catalog_evidence) is not _ResultEvidence
                or type(catalog_evidence.value) is not TypeSchemaCatalogTransition
                or type(composed_slice) is not TypeSchemaComposedSlice
            ):
                raise ValueError(
                    "Meta composed successor differs from recorded transitions"
                )
            package_transition = package_evidence.value
            catalog_transition = catalog_evidence.value
            _require_result_evidence(package_evidence, package_transition)
            _require_result_evidence(catalog_evidence, catalog_transition)
            if predecessor_admission is None:
                composed_evidence = state.composed_bodies.get(id(composed_slice))
                if composed_evidence is None:
                    raise ValueError("Meta composed-slice result bytes are absent")
                _require_result_evidence(composed_evidence, composed_slice)
                canonical_bytes = composed_evidence.canonical_bytes
                admission = _admit_prevalidated_composed_slice(
                    composed_slice,
                    canonical_bytes,
                    _token=_PREVALIDATED_SLICE_ADMISSION_TOKEN,
                    _proof_bundle_token=(
                        _PREVALIDATED_PROOF_BUNDLE_ADMISSION_TOKEN
                    ),
                )
                _ADMISSION_PACKAGE_TRANSITIONS[admission] = package_evidence
                _ADMISSION_COMPOSED_EVIDENCE[admission] = composed_evidence
            else:
                retained = _slice_admission_context(predecessor_admission)
                if retained.slice is not composed_slice:
                    raise ValueError(
                        "Meta CURRENT slice differs from predecessor admission"
                    )
                canonical_bytes = retained.canonical_bytes
                admission = predecessor_admission
                composed_evidence = _ADMISSION_COMPOSED_EVIDENCE.get(admission)
                if (
                    type(composed_evidence) is not _ResultEvidence
                    or composed_evidence.value is not composed_slice
                    or composed_evidence.canonical_bytes != canonical_bytes
                ):
                    raise ValueError(
                        "Meta CURRENT predecessor evidence is not admitted"
                    )
                _require_result_evidence(composed_evidence, composed_slice)
        except Exception:
            _terminate_operation(state)
            raise
        witness = object.__new__(_MetaTypeSchemaOperationWitness)
        witness_state = _WitnessState(
            witness,
            state.process_id,
            state.thread_id,
            package_evidence,
            catalog_evidence,
            composed_evidence,
            canonical_bytes,
            admission,
            state.decoded_nodes.body_fragments,
            state.decoded_nodes.coordinate_wires,
            state.diagnostics,
        )
        key = id(witness)
        if key in _WITNESSES:
            _terminate_operation(state)
            raise ValueError("Meta TypeSchema witness identity collision")
        _WITNESSES[key] = witness_state
        state.diagnostics.append(
            ("meta_witness_finish", perf_counter_ns() - finish_started)
        )
        _terminate_operation(state)
        return witness


def _consume_type_schema_operation_witness(
    witness: _MetaTypeSchemaOperationWitness,
    *,
    package_transition: TypeSchemaPackageTransition,
    catalog_transition: TypeSchemaCatalogTransition,
    composed_slice: TypeSchemaComposedSlice,
    _type: Callable[[object], type[object]] = type,
    _witness_type: type[_MetaTypeSchemaOperationWitness] = _MetaTypeSchemaOperationWitness,
    _any: Callable[..., bool] = any,
    _dict_contains: Callable[..., object] = dict.__contains__,
    _module_globals: dict[str, object] = _TYPE_SCHEMA_OPERATION_MODULE_GLOBALS,
    _absent_builtin_names: tuple[
        str, ...
    ] = _RESULT_VERIFIER_ABSENT_BUILTIN_NAMES,
    _type_error: type[TypeError] = TypeError,
    _value_error: type[ValueError] = ValueError,
    _witnesses: dict[int, _WitnessState] = _WITNESSES,
    _id: Callable[..., int] = id,
) -> tuple[
    AdmittedTypeSchemaComposedSlice,
    bytes,
    tuple[object, ...],
    tuple[tuple[PersistentBodyCoordinate, bytes], ...],
    bytes,
    bytes,
]:
    consume_started = perf_counter_ns()
    with _LOCK:
        if _any(
            _dict_contains(_module_globals, name) for name in _absent_builtin_names
        ):
            poisoned = _witnesses.get(_id(witness))
            if poisoned is not None and poisoned.witness is witness:
                poisoned.lifecycle = "terminal"
                _witnesses.pop(_id(witness), None)
            raise _value_error("Meta result verification primitive changed")
        if _type(witness) is not _witness_type:
            raise _type_error("Meta TypeSchema witness must be exact")
        state = _WITNESSES.pop(id(witness), None)
        if (
            state is None
            or state.witness is not witness
            or state.process_id != os.getpid()
            or state.thread_id != threading.get_ident()
            or state.lifecycle != "active"
        ):
            raise ValueError("Meta TypeSchema witness is not active")
        state.lifecycle = "consumed"
        try:
            if (
                state.package_transition.value is not package_transition
                or state.catalog_transition.value is not catalog_transition
                or state.composed_slice.value is not composed_slice
            ):
                raise ValueError("Meta TypeSchema witness result differs")
            _require_result_evidence(state.package_transition, package_transition)
            _require_result_evidence(state.catalog_transition, catalog_transition)
            _require_result_evidence(state.composed_slice, composed_slice)
            retained = _slice_admission_context(state.admission)
            if (
                retained.slice is not composed_slice
                or retained.canonical_bytes != state.canonical_bytes
            ):
                raise ValueError("Meta composed-slice admission changed")
            fragments: list[object] = []
            seen_body_refs: set[str] = set()
            for result in (package_transition, catalog_transition):
                for body in result.emitted_bodies:
                    coordinate_ref = body.coordinate.coordinate_ref
                    if coordinate_ref in seen_body_refs:
                        continue
                    retained_fragment = state.body_fragments.get(coordinate_ref)
                    if retained_fragment is None:
                        continue
                    coordinate_values, canonical_bytes, fragment = retained_fragment
                    if (
                        not _matches_retained_coordinate_values(
                            body.coordinate, coordinate_values
                        )
                        or canonical_bytes != body.canonical_bytes
                    ):
                        raise ValueError("Meta body fragment changed")
                    seen_body_refs.add(coordinate_ref)
                    fragments.extend((body, fragment))
            state.diagnostics.append(
                ("meta_witness_consume", perf_counter_ns() - consume_started)
            )
            _ADMISSION_DIAGNOSTICS[state.admission] = tuple(state.diagnostics)
            return (
                state.admission,
                state.canonical_bytes,
                tuple(fragments),
                tuple(state.coordinate_wires.values()),
                state.package_transition.canonical_bytes,
                state.catalog_transition.canonical_bytes,
            )
        finally:
            state.lifecycle = "terminal"


def _discard_type_schema_operation(
    operation: _MetaTypeSchemaOperation | None,
) -> None:
    if type(operation) is not _MetaTypeSchemaOperation:
        return
    with _LOCK:
        state = _OPERATIONS.pop(id(operation), None)
        if state is not None and state.operation is operation:
            state.lifecycle = "terminal"


def _discard_type_schema_operation_witness(
    witness: _MetaTypeSchemaOperationWitness | None,
) -> None:
    if type(witness) is not _MetaTypeSchemaOperationWitness:
        return
    with _LOCK:
        state = _WITNESSES.pop(id(witness), None)
        if state is not None and state.witness is witness:
            state.lifecycle = "terminal"
