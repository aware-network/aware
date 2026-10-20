"""The owning detached v5 topology values and retained execution closure."""

from __future__ import annotations

import builtins
import importlib as _native_importlib
import importlib.util as _native_import_util
import sys
from _operator import attrgetter as _native_attrgetter
from _operator import is_ as _same_object
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from itertools import chain as _native_chain
from types import (
    FunctionType,
    MappingProxyType,
    MemberDescriptorType,
    MethodType,
    ModuleType,
)
from typing import Any

from aware_meta_type_schema import TypeSchemaSlice, ValueShape

from . import owner_values as _owner
from .owner_values import (
    ActionValueMode,
    Cardinality,
    MutationScope,
    ProjectionDefinition,
    RelationshipEndpointResidence,
    RelationshipKind,
    SchemaActionDefinition,
    SchemaActionParameterDefinition,
    SchemaTopologyInputGrade,
    TraversalPolicy,
    digest_payload,
)

if __package__ is None:
    raise ImportError
try:
    _native_scan_module = _native_importlib.import_module(__package__ + "._preparation_scan")
except ModuleNotFoundError as _native_scan_error:
    if _native_scan_error.name != __package__ + "._preparation_scan":
        raise
    if _native_import_util.find_spec(__package__ + "._preparation_scan") is not None:
        raise
    _native_scan_module = None

__all__ = [
    "SCHEMA_TOPOLOGY_CONTRACT",
    "ActionValueMode",
    "AssociationEndpointDirection",
    "AssociationEndpointRoleInput",
    "GraphIdentityMode",
    "GraphTypeBinding",
    "MutationScope",
    "SchemaActionParameterDefinition",
    "SchemaFieldRelationshipInput",
    "SchemaOntologyRuntimeTopology",
    "SchemaRelationshipInputKind",
    "SchemaTopologyRelationshipInput",
    "ValueShape",
]

SCHEMA_TOPOLOGY_CONTRACT = "aware.ontology.runtime-schema-topology.v5"


class GraphIdentityMode(StrEnum, metaclass=_owner._TopologyEnumMeta):
    SCHEMA_FIELDS = "schema_fields"
    INSTANCE_REF = "instance_ref"


class SchemaRelationshipInputKind(StrEnum, metaclass=_owner._TopologyEnumMeta):
    SCHEMA_FIELD_RELATIONSHIP = "schema_field_relationship"
    ASSOCIATION_ENDPOINT_ROLE = "association_endpoint_role"


class AssociationEndpointDirection(StrEnum, metaclass=_owner._TopologyEnumMeta):
    ASSOCIATION_TO_TARGET = "association_to_target"


@dataclass(frozen=True, slots=True, order=True)
class GraphTypeBinding(metaclass=_owner._TopologyMeta):
    type_ref: str
    identity_mode: GraphIdentityMode
    identity_field_refs: tuple[str, ...]
    schema_relationship_field_refs: tuple[str, ...]
    association_role_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        _call(
            object.__setattr__,
            self,
            "type_ref",
            _call(_token, self.type_ref, "type_ref"),
        )
        _call(
            object.__setattr__,
            self,
            "identity_mode",
            _call(GraphIdentityMode, self.identity_mode),
        )
        identity_field_refs = _call(
            tuple,
            (
                _call(_token, value, "identity_field_refs")
                for value in self.identity_field_refs
            ),
        )
        if _call(len, identity_field_refs) != _call(
            len, _call(set, identity_field_refs)
        ):
            raise _call(ValueError, "identity_field_refs contains duplicates")
        _call(object.__setattr__, self, "identity_field_refs", identity_field_refs)
        _call(
            object.__setattr__,
            self,
            "schema_relationship_field_refs",
            _call(
                _refs,
                self.schema_relationship_field_refs,
                "schema_relationship_field_refs",
            ),
        )
        _call(
            object.__setattr__,
            self,
            "association_role_refs",
            _call(_refs, self.association_role_refs, "association_role_refs"),
        )
        if _call(set, self.schema_relationship_field_refs) & _call(
            set, self.association_role_refs
        ):
            raise _call(
                ValueError, "schema relationship and association refs must be disjoint"
            )
        if self.identity_mode is GraphIdentityMode.SCHEMA_FIELDS and (
            not self.identity_field_refs
        ):
            raise _call(
                ValueError, "schema_fields identity requires identity_field_refs"
            )
        if (
            self.identity_mode is GraphIdentityMode.INSTANCE_REF
            and self.identity_field_refs
        ):
            raise _call(ValueError, "instance_ref identity forbids identity_field_refs")

    def to_wire(self) -> dict[str, object]:
        return {
            "type_ref": self.type_ref,
            "identity_mode": self.identity_mode.value,
            "identity_field_refs": _call(list, self.identity_field_refs),
            "schema_relationship_field_refs": _call(
                list, self.schema_relationship_field_refs
            ),
            "association_role_refs": _call(list, self.association_role_refs),
        }


@dataclass(frozen=True, slots=True, order=True)
class SchemaFieldRelationshipInput(metaclass=_owner._TopologyMeta):
    relationship_ref: str
    source_type_ref: str
    target_type_ref: str
    target_package_ref: str
    source_cardinality: Cardinality
    target_cardinality: Cardinality
    relationship_kind: RelationshipKind
    traversal: TraversalPolicy
    endpoint_residence: RelationshipEndpointResidence
    schema_evidence_ref: str
    input_kind: SchemaRelationshipInputKind

    def __post_init__(self) -> None:
        for field in (
            "relationship_ref",
            "source_type_ref",
            "target_type_ref",
            "target_package_ref",
            "schema_evidence_ref",
        ):
            _call(
                object.__setattr__,
                self,
                field,
                _call(_token, _call(getattr, self, field), field),
            )
        _call(
            object.__setattr__,
            self,
            "source_cardinality",
            _call(Cardinality, self.source_cardinality),
        )
        _call(
            object.__setattr__,
            self,
            "target_cardinality",
            _call(Cardinality, self.target_cardinality),
        )
        _call(
            object.__setattr__,
            self,
            "relationship_kind",
            _call(RelationshipKind, self.relationship_kind),
        )
        _call(
            object.__setattr__,
            self,
            "traversal",
            _call(TraversalPolicy, self.traversal),
        )
        _call(
            object.__setattr__,
            self,
            "endpoint_residence",
            _call(RelationshipEndpointResidence, self.endpoint_residence),
        )
        _call(
            object.__setattr__,
            self,
            "input_kind",
            _call(SchemaRelationshipInputKind, self.input_kind),
        )
        if self.input_kind is not SchemaRelationshipInputKind.SCHEMA_FIELD_RELATIONSHIP:
            raise _call(
                ValueError, "schema field relationship requires its exact input kind"
            )

    def to_wire(self) -> dict[str, object]:
        return {
            "input_kind": self.input_kind.value,
            "relationship_ref": self.relationship_ref,
            "source_type_ref": self.source_type_ref,
            "target_type_ref": self.target_type_ref,
            "target_package_ref": self.target_package_ref,
            "source_cardinality": self.source_cardinality.value,
            "target_cardinality": self.target_cardinality.value,
            "relationship_kind": self.relationship_kind.value,
            "traversal": self.traversal.value,
            "endpoint_residence": self.endpoint_residence.value,
            "schema_evidence_ref": self.schema_evidence_ref,
        }


@dataclass(frozen=True, slots=True, order=True)
class AssociationEndpointRoleInput(metaclass=_owner._TopologyMeta):
    role_ref: str
    source_type_ref: str
    source_field_ref: str
    association_type_ref: str
    target_type_ref: str
    target_package_ref: str
    endpoint_residence: RelationshipEndpointResidence
    member_name: str
    direction: AssociationEndpointDirection
    endpoint_cardinality: Cardinality
    relationship_semantics: RelationshipKind
    traversal: TraversalPolicy
    selecting_projection_ref: str
    projection_role_coordinate: str
    meaning_resolution_digest: str
    association_role_digest: str
    schema_evidence_ref: str
    input_kind: SchemaRelationshipInputKind

    def __post_init__(self) -> None:
        for field in (
            "role_ref",
            "source_type_ref",
            "source_field_ref",
            "association_type_ref",
            "target_type_ref",
            "target_package_ref",
            "member_name",
            "selecting_projection_ref",
            "projection_role_coordinate",
            "meaning_resolution_digest",
            "association_role_digest",
            "schema_evidence_ref",
        ):
            _call(
                object.__setattr__,
                self,
                field,
                _call(_token, _call(getattr, self, field), field),
            )
        _call(
            object.__setattr__,
            self,
            "direction",
            _call(AssociationEndpointDirection, self.direction),
        )
        _call(
            object.__setattr__,
            self,
            "endpoint_residence",
            _call(RelationshipEndpointResidence, self.endpoint_residence),
        )
        _call(
            object.__setattr__,
            self,
            "endpoint_cardinality",
            _call(Cardinality, self.endpoint_cardinality),
        )
        _call(
            object.__setattr__,
            self,
            "relationship_semantics",
            _call(RelationshipKind, self.relationship_semantics),
        )
        _call(
            object.__setattr__,
            self,
            "traversal",
            _call(TraversalPolicy, self.traversal),
        )
        _call(
            object.__setattr__,
            self,
            "input_kind",
            _call(SchemaRelationshipInputKind, self.input_kind),
        )
        if self.input_kind is not SchemaRelationshipInputKind.ASSOCIATION_ENDPOINT_ROLE:
            raise _call(
                ValueError, "association endpoint role requires its exact input kind"
            )
        if self.role_ref != f"{self.association_type_ref}.{self.member_name}":
            raise _call(
                ValueError, "association role ref differs from association member"
            )
        if not _call(self.source_field_ref.startswith, f"{self.source_type_ref}."):
            raise _call(ValueError, "association source field differs from source type")

    @property
    def relationship_ref(self) -> str:
        return self.role_ref

    @property
    def source_cardinality(self) -> Cardinality:
        return self.endpoint_cardinality

    @property
    def target_cardinality(self) -> Cardinality:
        return Cardinality.ONE

    def to_wire(self) -> dict[str, object]:
        return {
            "input_kind": self.input_kind.value,
            "role_ref": self.role_ref,
            "source_type_ref": self.source_type_ref,
            "source_field_ref": self.source_field_ref,
            "association_type_ref": self.association_type_ref,
            "target_type_ref": self.target_type_ref,
            "target_package_ref": self.target_package_ref,
            "endpoint_residence": self.endpoint_residence.value,
            "member_name": self.member_name,
            "direction": self.direction.value,
            "endpoint_cardinality": self.endpoint_cardinality.value,
            "relationship_semantics": self.relationship_semantics.value,
            "traversal": self.traversal.value,
            "selecting_projection_ref": self.selecting_projection_ref,
            "projection_role_coordinate": self.projection_role_coordinate,
            "meaning_resolution_digest": self.meaning_resolution_digest,
            "association_role_digest": self.association_role_digest,
            "schema_evidence_ref": self.schema_evidence_ref,
        }


@dataclass(frozen=True, slots=True)
class SchemaOntologyRuntimeTopology(metaclass=_owner._TopologyMeta):
    namespace: str
    semantic_version: str
    schema_digest: str
    schema_slice_digest: str
    schema_root_type_refs: tuple[str, ...]
    graph_types: tuple[GraphTypeBinding, ...]
    relationships: tuple[SchemaTopologyRelationshipInput, ...]
    projections: tuple[ProjectionDefinition, ...]
    actions: tuple[SchemaActionDefinition, ...]
    input_grade: SchemaTopologyInputGrade
    topology_digest: str

    def __post_init__(self) -> None:
        _call(_normalize_topology, self)
        _call(_owner._digest, self.topology_digest, "topology_digest")
        payload = _call(self._wire_payload)
        expected = _call(digest_payload, SCHEMA_TOPOLOGY_CONTRACT, payload)
        if self.topology_digest != expected:
            raise _call(ValueError, "topology_digest mismatch")

    @classmethod
    def create(
        cls,
        *,
        namespace: str,
        semantic_version: str,
        schema_slice: TypeSchemaSlice,
        graph_types: Iterable[GraphTypeBinding],
        relationships: Iterable[SchemaTopologyRelationshipInput] = (),
        projections: Iterable[ProjectionDefinition] = (),
        actions: Iterable[SchemaActionDefinition] = (),
    ) -> SchemaOntologyRuntimeTopology:
        if not _call(isinstance, schema_slice, TypeSchemaSlice):
            raise _call(TypeError, "schema_slice must be TypeSchemaSlice")
        candidate = _call(
            _draft_topology,
            cls,
            namespace,
            semantic_version,
            schema_slice.bundle_digest,
            schema_slice.slice_digest,
            schema_slice.root_type_refs,
            _call(tuple, graph_types),
            _call(tuple, relationships),
            _call(tuple, projections),
            _call(tuple, actions),
            SchemaTopologyInputGrade.PORTABLE_INPUT,
            "pending",
        )
        candidate = _call(
            cls,
            namespace=candidate.namespace,
            semantic_version=candidate.semantic_version,
            schema_digest=candidate.schema_digest,
            schema_slice_digest=candidate.schema_slice_digest,
            schema_root_type_refs=candidate.schema_root_type_refs,
            graph_types=candidate.graph_types,
            relationships=candidate.relationships,
            projections=candidate.projections,
            actions=candidate.actions,
            input_grade=candidate.input_grade,
            topology_digest=_call(
                digest_payload, SCHEMA_TOPOLOGY_CONTRACT, _call(candidate._wire_payload)
            ),
        )
        _call(_validate_topology, candidate, schema_slice)
        return candidate

    def _payload(self) -> dict[str, object]:
        return {
            "namespace": self.namespace,
            "semantic_version": self.semantic_version,
            "schema_digest": self.schema_digest,
            "schema_slice_digest": self.schema_slice_digest,
            "schema_root_type_refs": self.schema_root_type_refs,
            "graph_types": self.graph_types,
            "relationships": self.relationships,
            "projections": self.projections,
            "actions": self.actions,
            "input_grade": self.input_grade,
        }

    def _wire_payload(self) -> dict[str, object]:
        return {
            "namespace": self.namespace,
            "semantic_version": self.semantic_version,
            "schema_digest": self.schema_digest,
            "schema_slice_digest": self.schema_slice_digest,
            "schema_root_type_refs": _call(list, self.schema_root_type_refs),
            "graph_types": [_call(value.to_wire) for value in self.graph_types],
            "relationships": [_call(value.to_wire) for value in self.relationships],
            "projections": [_call(value.to_wire) for value in self.projections],
            "actions": [_call(value.to_wire) for value in self.actions],
            "input_grade": self.input_grade.value,
        }

    def to_wire(self) -> dict[str, object]:
        _call(self.__post_init__)
        return {
            "contract": SCHEMA_TOPOLOGY_CONTRACT,
            **_call(self._wire_payload),
            "topology_digest": self.topology_digest,
        }


SchemaTopologyRelationshipInput = (
    SchemaFieldRelationshipInput | AssociationEndpointRoleInput
)

# Installed from the owning validator before sealing; no dispatch-time import.
_validate_topology: Any = None


# These lookup primitives reject foreign operands before traversal or conversion.
def _token(value: object, field: str) -> str:
    return _call(_owner._strict_token, value, field)


def _refs(value: object, field: str) -> tuple[str, ...]:
    return _call(_owner._record_refs, value, field)


def _typed_tuple(value: Any, expected: type, field: str) -> tuple:
    if _call(type, value) is not tuple and _call(type, value) is not list:
        raise _call(TypeError, "topology collections must be native tuples or lists")
    if _call(any, (_call(type, item) is not expected for item in value)):
        raise _call(TypeError, "topology collection has an invalid exact record")
    return _call(tuple, (_call(_revalidate, item) for item in value))


def _call(operation: Any, /, *args: Any, **kwargs: Any) -> Any:
    return operation(*args, **kwargs)


def _revalidate(value: Any) -> Any:
    cls = _call(type, value)
    if value is None or cls is str or cls is bool or cls is int or cls is bytes:
        return value
    if cls is tuple or cls is list:
        copied = [_call(_revalidate, item) for item in value]
        return _call(tuple, copied) if cls is tuple else copied
    if cls is dict:
        return {key: _call(_revalidate, item) for key, item in _call(value.items)}
    if _call(isinstance, value, StrEnum):
        return value
    # A mappingproxy is a live view, not a captured class/admission snapshot.
    # Keep it local to this revalidation; every recursive return and subsequent
    # dispatch still runs the original fresh guard before observing a member.
    members = _call(vars, cls)
    fields = members.get("__dataclass_fields__")
    if _call(type, fields) is not dict:
        raise _call(TypeError, "topology revalidation requires exact records")
    data = {
        name: _call(_revalidate, _call(getattr, value, name))
        for name in fields
        if _call(type, members.get(name)) is MemberDescriptorType
    }
    if _call(getattr, cls, "__module__").startswith("aware_meta_type_schema."):
        return _call(_lower_record, cls, data)
    return _call(cls, **data)


def _lower_record(cls: Any, data: Any) -> Any:
    raise TypeError("owning Meta record adapter is not initialized")


def _draft_topology(cls, *values):
    # A private, unencoded construction step; public constructors and to_wire
    # reject pending or incorrect digests. No provenance marker is retained.
    draft = _call(object.__new__, cls)
    names = (
        "namespace",
        "semantic_version",
        "schema_digest",
        "schema_slice_digest",
        "schema_root_type_refs",
        "graph_types",
        "relationships",
        "projections",
        "actions",
        "input_grade",
        "topology_digest",
    )
    for name, value in _call(zip, names, values):
        _call(object.__setattr__, draft, name, value)
    _call(_normalize_topology, draft)
    return draft


def _normalize_topology(self) -> None:
    for field in (
        "namespace",
        "semantic_version",
        "schema_digest",
        "schema_slice_digest",
        "topology_digest",
    ):
        _call(
            object.__setattr__,
            self,
            field,
            _call(_token, _call(getattr, self, field), field),
        )
    _call(
        object.__setattr__,
        self,
        "input_grade",
        _call(SchemaTopologyInputGrade, self.input_grade),
    )
    if self.input_grade is not SchemaTopologyInputGrade.PORTABLE_INPUT:
        raise _call(ValueError, "schema topology may only claim portable_input")
    _call(
        object.__setattr__,
        self,
        "schema_root_type_refs",
        _call(_refs, self.schema_root_type_refs, "schema_root_type_refs"),
    )
    if not self.schema_root_type_refs:
        raise _call(ValueError, "schema_root_type_refs must not be empty")
    for field, expected, key in (
        ("graph_types", GraphTypeBinding, "type_ref"),
        ("projections", ProjectionDefinition, "projection_ref"),
        ("actions", SchemaActionDefinition, "action_ref"),
    ):
        values = _call(_typed_tuple, _call(getattr, self, field), expected, field)
        _call(
            object.__setattr__,
            self,
            field,
            _call(
                tuple,
                _call(sorted, values, key=lambda value: _call(getattr, value, key)),
            ),
        )
    relationships = _call(
        tuple, (_call(_revalidate, item) for item in self.relationships)
    )
    if _call(
        any,
        (
            not _call(
                isinstance,
                value,
                (SchemaFieldRelationshipInput, AssociationEndpointRoleInput),
            )
            for value in relationships
        ),
    ):
        raise _call(TypeError, "relationships contain an invalid portable input")
    _call(
        object.__setattr__,
        self,
        "relationships",
        _call(
            tuple,
            _call(sorted, relationships, key=lambda value: value.relationship_ref),
        ),
    )


def _install_dispatch(modules: tuple[ModuleType, ...]) -> tuple:
    """Install once during owning-module initialization, before any entrance.

    The lower adapter executes the retained Meta code in a retained namespace.
    It introduces no shape algebra, modifies no Meta module/class, and returns
    the original Meta types. Checks surround recursive helper returns as well
    as the outer call. Portable guards are sealed after the owner's own seals.
    """
    import collections
    import enum
    import hashlib
    import json
    from types import BuiltinFunctionType

    from aware_meta_type_schema import (
        codec as meta_codec,
    )
    from aware_meta_type_schema import (
        encoding as meta_encoding,
    )
    from aware_meta_type_schema import (
        model as meta_model,
    )

    kind, get, cls_get = type, object.__getattribute__, type.__getattribute__
    assign, native_new = object.__setattr__, object.__new__
    dict_get, dict_keys, dict_items = dict.get, dict.keys, dict.items
    native_tuple, native_any, native_len, native_id = tuple, any, len, id
    string_kind = str
    builtin_namespace = get(builtins, "__dict__")
    function_kind, method_kind, module_kind = FunctionType, MethodType, ModuleType
    fail_kind, unwind = TypeError, BaseException
    fail_new, fail_init = BaseException.__new__, BaseException.__init__
    guard = None
    guard_code = None
    known_calls = ()
    call_identities = MappingProxyType({})
    protected_invocations = []
    invocation_identities = MappingProxyType({})
    original_functions, wrappers = [], []
    lower_namespaces, lower_functions = {}, []
    public_classes = tuple(
        value
        for module in modules
        for value in vars(module).values()
        if isinstance(value, type) and value.__module__ == module.__name__
    )
    public_classes += (_owner.ProjectionDefinition, _owner.RelationshipKind)
    meta_classes = tuple(
        value
        for module in (meta_model, meta_codec, meta_encoding)
        for value in vars(module).values()
        if isinstance(value, type) and value.__module__ == module.__name__
    )
    owner_classes = tuple(
        value
        for value in vars(_owner).values()
        if isinstance(value, type) and value.__module__ == _owner.__name__
    )
    classes = tuple(
        dict.fromkeys(
            (*public_classes, *meta_classes, *owner_classes, collections.Counter)
        )
    )
    records = tuple(
        cls
        for cls in classes
        if kind(cls_get(cls, "__dict__").get("__dataclass_fields__")) is dict
    )
    slot_rows = tuple(
        (
            cls,
            tuple(
                (name, cls_get(cls, "__dict__").get(name))
                for name in cls_get(cls, "__dict__")["__dataclass_fields__"]
            ),
        )
        for cls in records
    )
    enum_members = tuple(
        member
        for cls in classes
        if isinstance(cls, enum.EnumType)
        for member in cls_get(cls, "__dict__")["_member_map_"].values()
    )
    native_functions = tuple(
        value for value in vars(builtins).values() if kind(value) is BuiltinFunctionType
    ) + (
        object.__getattribute__,
        object.__setattr__,
        object.__new__,
        type.__getattribute__,
        BaseException.__new__,
        BaseException.__init__,
        type,
        bool,
        int,
        str,
        bytes,
        list,
        tuple,
        dict,
        set,
        frozenset,
        enumerate,
        zip,
        range,
        TypeError,
        ValueError,
    )
    native_receivers = (str, bytes, tuple, list, dict, set, frozenset)
    # Immutable ORIGINAL identity inventories. Integer lookup never invokes
    # caller hashing/equality, and the final `is` preserves the old predicate.
    # Their private backing dictionaries are neither retained nor exported.
    native_input_identities = MappingProxyType({native_id(value): value
                                               for value in (*enum_members, *classes, *native_functions)})
    native_call_identities = MappingProxyType({native_id(value): value for value in native_functions})

    def refuse(message="topology executable identity mismatched"):
        error = fail_new(fail_kind)
        fail_init(error, message)
        return error

    def checked():
        if guard is None or get(guard, "__code__") is not guard_code:
            raise refuse()
        guard()

    def native(value, active=None, *, constructing=False):
        cls = kind(value)
        if value is None or cls is str or cls is bool or cls is int or cls is bytes:
            return
        if native_input_identities.get(native_id(value)) is value:
            return
        if active is None:
            active = set()
        coordinate = native_id(value)
        if coordinate in active:
            raise refuse("cyclic topology data")
        active.add(coordinate)
        try:
            if cls is tuple or cls is list or cls is set or cls is frozenset:
                for item in value:
                    native(item, active)
                return
            if cls is dict:
                for key, item in dict_items(value):
                    native(key, active)
                    native(item, active)
                return
            for record, slots in slot_rows:
                if cls is record:
                    for name, descriptor in slots:
                        if kind(descriptor) is not MemberDescriptorType:
                            raise refuse("topology data requires original slots")
                        try:
                            child = descriptor.__get__(value, record)
                        except AttributeError:
                            if constructing:
                                continue
                            raise refuse("incomplete topology record") from None
                        native(child, active)
                    return
        finally:
            active.remove(coordinate)
        raise refuse("topology operands must be exact native data")

    checked_identity, checked_code = checked, get(checked, "__code__")

    def invoke(row, args, kwargs):
        # One original admission/dispatch implementation, shared by standalone
        # wrappers and _call. The row is immutable original dispatch metadata,
        # never a successful-validation flag or a caller-supplied recipe.
        target, target_code, receiver, class_receiver, internal, name = row
        if get(target, "__code__") is not target_code:
            raise refuse()
        if receiver is not None and (
            (class_receiver and args[0] is not receiver)
            or (not class_receiver and kind(args[0]) is not receiver)
        ):
            raise refuse("topology method requires its exact receiver")
        start = 1 if class_receiver or name == "__init__" else 0
        if not internal:
            for item in args[start:]:
                native(item, constructing=name == "__post_init__")
            for key, item in dict_items(kwargs):
                if kind(key) is not str:
                    raise refuse("topology keyword names must be exact strings")
                native(item)
        return target(*args, **kwargs)

    def protect(target, *, receiver=None, class_receiver=False, internal=False):
        original_functions.append(target)
        name = target.__name__
        target_code = get(target, "__code__")
        row = (target, target_code, receiver, class_receiver, internal, name)

        def protected(*args, **kwargs):
            if (
                checked is not checked_identity
                or get(checked, "__code__") is not checked_code
            ):
                raise fail_kind("topology verifier identity mismatched")
            checked()
            try:
                result = invoke(row, args, kwargs)
            except unwind:
                checked()
                raise
            checked()
            return result

        for field in ("__name__", "__qualname__", "__module__", "__annotations__"):
            assign(protected, field, get(target, field))
        get(protected, "__dict__")["__wrapped__"] = target
        protected_invocations.append((protected, row))
        wrappers.append(protected)
        return protected

    def call(target, /, *args, **kwargs):
        if (
            checked is not checked_identity
            or get(checked, "__code__") is not checked_code
        ):
            raise fail_kind("topology verifier identity mismatched")
        # A writable helper can be rebound to a native callable too. Check its
        # owning lookup slots before admitting any dispatch, including native
        # operations; native identity alone cannot authenticate the binding.
        checked()
        if target is not None and native_call_identities.get(native_id(target)) is target:
            return target(*args, **kwargs)
        if kind(target) is BuiltinFunctionType:
            receiver = get(target, "__self__")
            if native_any(kind(receiver) is cls for cls in native_receivers):
                return target(*args, **kwargs)
        if kind(target) is method_kind:
            operation = get(target, "__func__")
            if call_identities.get(native_id(operation)) is not operation:
                raise refuse("unretained topology method")
        elif target is None or call_identities.get(native_id(target)) is not target:
            raise refuse("unretained topology dispatch")
        else:
            operation = target
        # The full preceding scan authenticates BOTH original callables and
        # their complete closures. Do not enter the public wrapper again: its
        # adjacent checks would repeat this same boundary. Independent calls
        # to that wrapper still perform their own complete fresh checks.
        invocation = invocation_identities.get(native_id(operation))
        try:
            if invocation is not None and invocation[0] is operation:
                if kind(target) is method_kind:
                    result = invoke(invocation[1], (get(target, "__self__"), *args), kwargs)
                else:
                    result = invoke(invocation[1], args, kwargs)
            else:
                result = target(*args, **kwargs)
        except unwind:
            checked()
            raise
        checked()
        return result

    # Replay Meta's actual recursive decoder in a closed lookup namespace.
    # Exact data preflight occurs at the public entry, before Meta's isinstance
    # and enum conversions; each recursive helper is a retained checked function.
    for lower_module in (meta_model, meta_codec, meta_encoding):
        namespace = dict(vars(lower_module))
        namespace["__builtins__"] = dict(vars(builtins))
        lower_namespaces[lower_module] = namespace
        for name, target in tuple(namespace.items()):
            if (
                kind(target) is function_kind
                and target.__module__ == lower_module.__name__
            ):
                cloned = function_kind(
                    target.__code__,
                    namespace,
                    target.__name__,
                    target.__defaults__,
                    target.__closure__,
                )
                cloned.__kwdefaults__ = target.__kwdefaults__
                protected = protect(cloned, internal=True)
                namespace[name] = protected
                lower_functions.extend((target, cloned, protected))
    for cls in meta_classes:
        for target in vars(cls).values():
            if kind(target) is function_kind:
                lower_functions.append(target)
            elif kind(target) is classmethod or kind(target) is staticmethod:
                lower_functions.append(target.__func__)
    # Cross-module helper aliases stay in the same owning, retained closure.
    lower_namespaces[meta_model]["digest_payload"] = lower_namespaces[meta_encoding][
        "digest_payload"
    ]
    json_view = module_kind(__name__ + "._retained_json")
    vars(json_view).update(vars(json))
    for name in ("loads", "dumps"):
        target = vars(json)[name]
        adapted = protect(target, internal=True)
        vars(json_view)[name] = adapted
        lower_functions.extend((target, adapted))
    lower_namespaces[meta_encoding]["json"] = json_view
    post_rows = []
    for cls in meta_classes:
        members = cls_get(cls, "__dict__")
        fields = members.get("__dataclass_fields__")
        post = members.get("__post_init__")
        if kind(fields) is not dict or kind(post) is not function_kind:
            continue
        field_names = tuple(
            name for name in fields if kind(members.get(name)) is MemberDescriptorType
        )
        # lower_namespaces is keyed by modules, not by caller-selected strings.
        namespace = next(
            lower_namespaces[module]
            for module in (meta_model, meta_codec, meta_encoding)
            if module.__name__ == cls.__module__
        )
        clone = function_kind(
            post.__code__, namespace, post.__name__, post.__defaults__, post.__closure__
        )
        clone.__kwdefaults__ = post.__kwdefaults__
        adapted = protect(clone, internal=True)
        post_rows.append((cls, field_names, adapted))
        lower_functions.extend((post, clone, adapted))
    post_rows = tuple(post_rows)

    def construct_record(cls, data):
        checked()
        native(data)
        for expected, names, post in post_rows:
            if cls is expected:
                if kind(data) is not dict or tuple(data) != names:
                    raise refuse(
                        "Meta record fields must retain their exact owning order"
                    )
                value = native_new(cls)
                for name in names:
                    assign(value, name, dict_get(data, name))
                post(value)
                checked()
                return value
        raise refuse("unretained Meta record constructor")

    lower_functions.append(construct_record)
    vars(modules[0])["_lower_record"] = construct_record

    # Shape construction uses the original owning post-init body and slots.
    # No mutable Meta __init__/__post_init__ lookup can intervene between returns.
    shape_cls = meta_model.ValueShape
    shape_post = shape_cls.__post_init__
    shape_post_clone = function_kind(
        shape_post.__code__,
        lower_namespaces[meta_model],
        shape_post.__name__,
        shape_post.__defaults__,
        shape_post.__closure__,
    )
    shape_fields = tuple(cls_get(shape_cls, "__dict__")["__dataclass_fields__"])

    def shape_construct(
        *,
        kind,
        scalar_kind=None,
        type_ref=None,
        element=None,
        map_value=None,
        variants=(),
    ):
        checked()
        fields = (kind, scalar_kind, type_ref, element, map_value, variants)
        for item in fields:
            native(item)
        value = native_new(shape_cls)
        for name, item in zip(shape_fields, fields):
            assign(value, name, item)
        shape_post_clone(value)
        checked()
        return value

    lower_functions.extend((shape_post, shape_post_clone, shape_construct))
    lower_namespaces[meta_codec]["ValueShape"] = shape_construct
    lower_shape = lower_namespaces[meta_codec]["_decode_shape"]

    def decode_shape(value, path):
        checked()
        native(value)
        native(path)
        try:
            return lower_shape(value, path)
        except (TypeError, ValueError) as error:
            checked()
            raise modules[2].SchemaTopologyManifestDecodeError(str(error)) from None

    lower_functions.append(decode_shape)

    ordinary_construct, enum_construct = type.__call__, enum.EnumType.__call__

    def construct(cls, *args, **kwargs):
        if (
            checked is not checked_identity
            or get(checked, "__code__") is not checked_code
        ):
            raise fail_kind("topology verifier identity mismatched")
        checked()
        if not native_any(cls is expected for expected in public_classes):
            raise refuse("topology constructor requires its exact owning class")
        for value in args:
            native(value)
        for key, value in dict_items(kwargs):
            if kind(key) is not string_kind:
                raise refuse("topology keyword names must be exact strings")
            native(value)
        try:
            result = (
                enum_construct if isinstance(cls, enum.EnumType) else ordinary_construct
            )(cls, *args, **kwargs)
        except unwind:
            checked()
            raise
        checked()
        return result

    type.__setattr__(_owner._TopologyMeta, "__call__", construct)
    type.__setattr__(_owner._TopologyEnumMeta, "__call__", construct)
    lower_functions.append(construct)

    for module in modules:
        namespace = vars(module)
        for name, target in tuple(namespace.items()):
            if (
                kind(target) is function_kind
                and target.__module__ == module.__name__
                and name != "_call"
            ):
                namespace[name] = protect(target)
        namespace["_call"] = call
    vars(modules[2])["_lower_shape"] = decode_shape
    vars(modules[0])["_validate_topology"] = modules[1].validate_schema_topology
    for cls in public_classes:
        if isinstance(cls, enum.EnumType):
            continue
        for name, target in tuple(cls_get(cls, "__dict__").items()):
            if kind(target) is function_kind:
                setattr(cls, name, protect(target, receiver=cls))
            elif kind(target) is classmethod:
                setattr(
                    cls,
                    name,
                    classmethod(
                        protect(target.__func__, receiver=cls, class_receiver=True)
                    ),
                )
            elif kind(target) is property:
                setattr(
                    cls,
                    name,
                    property(
                        protect(target.fget, receiver=cls),
                        target.fset,
                        target.fdel,
                        target.__doc__,
                    ),
                )

    def seal():
        nonlocal guard, guard_code, known_calls, call_identities, invocation_identities
        if guard is not None:
            checked()
            raise refuse("topology dispatch is already sealed")
        # The recursive fingerprint consists solely of identities and native
        # container structure. Foreign classes are never compared by equality.
        modules_to_check = (
            *modules,
            _owner,
            meta_model,
            meta_codec,
            meta_encoding,
            sys.modules["aware_meta_type_schema"],
            json,
            sys.modules["json.encoder"],
            sys.modules["json.decoder"],
            sys.modules["json.scanner"],
            hashlib,
            collections,
            enum,
            sys.modules["_operator"],
        )
        if _native_scan_module is not None:
            modules_to_check = (*modules_to_check, _native_scan_module)
        module_rows = tuple(
            (module, tuple(dict_keys(vars(module))), tuple(dict_items(vars(module))))
            for module in (*modules_to_check, json_view)
        )
        # Retain native mapping methods, without fingerprinting unrelated imports.
        sys_get = vars(sys).get
        sys_keys = vars(sys).keys
        registry_get = sys.modules.get
        registry_keys = sys.modules.keys
        registry_rows = tuple(
            (vars(module)["__name__"], module) for module in modules_to_check
        )
        singleton_rows = tuple(
            (singleton, kind(singleton))
            for singleton in (
                vars(json)["_default_decoder"],
                vars(json)["_default_encoder"],
            )
        )
        class_rows = tuple(
            (
                cls,
                kind(cls),
                tuple(cls_get(cls, "__dict__")),
                tuple(cls_get(cls, "__dict__").items()),
            )
            for cls in (
                *classes,
                enum.EnumType,
                enum.Enum,
                enum.StrEnum,
                enum.property,
                json.JSONEncoder,
                json.JSONDecoder,
                json.JSONDecodeError,
                collections.Counter,
            )
        )
        class_identity = tuple(
            (
                cls,
                cls_get(cls, "__bases__"),
                cls_get(cls, "__mro__"),
                tuple(
                    (name, cls_get(cls, name))
                    for name in ("__name__", "__qualname__", "__module__")
                ),
            )
            for cls, _, _, _ in class_rows
        )
        operations = [
            *original_functions,
            *wrappers,
            *lower_functions,
            call,
            native,
            invoke,
            checked,
            refuse,
        ]
        for items in (
            *tuple(row[2] for row in module_rows),
            *tuple(row[3] for row in class_rows),
        ):
            for _, value in items:
                if kind(value) is function_kind:
                    operations.append(value)
                elif kind(value) is classmethod or kind(value) is staticmethod:
                    operations.append(value.__func__)
                elif kind(value) is property or kind(value) is enum.property:
                    operations.extend(
                        fn
                        for fn in (value.fget, value.fset, value.fdel)
                        if kind(fn) is function_kind
                    )
        operations = tuple(dict.fromkeys(operations))
        # The shared private invoker is scanned as executable behavior but is
        # NOT a selectable target. Only original wrapper bindings supply rows.
        known_calls = (*(operation for operation in operations if operation is not invoke), *classes)
        call_identities = MappingProxyType({native_id(value): value for value in known_calls})
        invocation_identities = MappingProxyType({native_id(wrapper): (wrapper, row)
                                                for wrapper, row in protected_invocations})
        own_guard_cell = next(
            cell
            for name, cell in zip(
                checked.__code__.co_freevars, checked.__closure__ or ()
            )
            if name == "guard"
        )
        own_code_cell = next(
            cell
            for name, cell in zip(
                checked.__code__.co_freevars, checked.__closure__ or ()
            )
            if name == "guard_code"
        )
        cell_rows = tuple(
            (cell, get(cell, "cell_contents"))
            for target in operations
            for cell in get(target, "__closure__") or ()
        )
        function_rows = tuple(
            (
                target,
                get(target, "__code__"),
                get(target, "__defaults__"),
                get(target, "__kwdefaults__"),
            )
            for target in operations
        )
        seen = set()
        containers = []

        def retain(value):
            cls = kind(value)
            if cls is not dict and cls is not list and cls is not tuple:
                return
            if native_id(value) in seen:
                return
            seen.add(native_id(value))
            if cls is dict:
                entries = tuple(dict_items(value))
                containers.append((value, entries))
                for key, item in entries:
                    retain(key)
                    retain(item)
            else:
                entries = tuple(value)
                containers.append((value, entries))
                for item in entries:
                    retain(item)

        for items in (
            *tuple(row[2] for row in module_rows),
            *tuple(row[3] for row in class_rows),
        ):
            for _, value in items:
                retain(value)
        for singleton, _ in singleton_rows:
            retain(get(singleton, "__dict__"))
        for _, _, defaults, kwdefaults in function_rows:
            retain(defaults)
            retain(kwdefaults)
        for _, _, _, items in class_rows:
            members = dict(items).get("_member_map_")
            if kind(members) is dict:
                for member in members.values():
                    retain(get(member, "__dict__"))
        lower_rows = tuple(
            (namespace, tuple(dict_items(namespace)))
            for namespace in lower_namespaces.values()
        )
        builtin_rows = tuple(dict_items(builtin_namespace))
        builtin_keys = tuple(dict_keys(builtin_namespace))
        for namespace, _ in lower_rows:
            retain(namespace)

        # Plans retain the original objects as well as their identities. They
        # never remember a successful runtime check: every boundary scans the
        # current dictionaries, descriptors and cells again using native ports.
        native_map, native_all, same_object = map, all, _same_object
        dict_values = dict.values
        proxy_values = type(type.__dict__).values
        builtin_plan = (builtin_rows, tuple(value for _, value in builtin_rows))
        module_plans = tuple((module, names, items, tuple(value for _, value in items))
                             for module, names, items in module_rows)
        class_plans = tuple((cls, cls_kind, names, items, tuple(value for _, value in items))
                            for cls, cls_kind, names, items in class_rows)
        lower_plans = tuple((namespace, items, tuple(value for _, value in items))
                            for namespace, items in lower_rows)
        container_plans = tuple((value, expected,
                                 tuple(key for key, _ in expected) if kind(value) is dict else (),
                                 tuple(item for _, item in expected) if kind(value) is dict else expected)
                                for value, expected in containers)
        # One physical closure slot has one expected value. Schedule it once
        # WITHIN each fresh scan, not once per function that shares that cell.
        # No successful check or runtime value survives a scan.
        distinct_cells = {}
        for cell, expected in cell_rows:
            if cell is own_guard_cell or cell is own_code_cell:
                continue
            previous = distinct_cells.get(native_id(cell))
            if previous is not None and (previous[0] is not cell or previous[1] is not expected):
                raise refuse("inconsistent original topology closure slot")
            distinct_cells[native_id(cell)] = (cell, expected)
        ordinary_cells = tuple(distinct_cells.values())
        cell_plan = (ordinary_cells, tuple(cell for cell, _ in ordinary_cells),
                     tuple(expected for _, expected in ordinary_cells))
        special_cells = tuple(cell for cell, _ in cell_rows
                              if cell is own_guard_cell or cell is own_code_cell)
        read_cell = _native_attrgetter("cell_contents")
        function_targets = tuple(row[0] for row in function_rows)
        function_plan = (function_rows, tuple(row[1] for row in function_rows),
                         tuple(row[2] for row in function_rows), tuple(row[3] for row in function_rows))
        read_code = _native_attrgetter("__code__")
        read_defaults = _native_attrgetter("__defaults__")
        read_kwdefaults = _native_attrgetter("__kwdefaults__")
        flatten = _native_chain.from_iterable
        dictionary_targets = tuple(row[0] for row in container_plans if kind(row[0]) is dict)
        # Discovery above still descends through every exact tuple to retain
        # all nested mutable objects. A retained exact tuple cannot change its
        # element bindings: scan the mutable lists, not immutable tuple slots.
        # Incoming dictionary/function/cell identities are still checked fresh.
        sequence_targets = tuple(row[0] for row in container_plans if kind(row[0]) is list)
        immutable_sequence_count = sum(kind(row[0]) is tuple for row in container_plans)
        dictionary_lengths = tuple(native_len(row[1]) for row in container_plans if kind(row[0]) is dict)
        sequence_lengths = tuple(native_len(row[1]) for row in container_plans if kind(row[0]) is list)
        dictionary_expected_keys = tuple(key for row in container_plans if kind(row[0]) is dict for key in row[2])
        dictionary_expected_values = tuple(value for row in container_plans if kind(row[0]) is dict for value in row[3])
        sequence_expected_values = tuple(value for row in container_plans if kind(row[0]) is list for value in row[3])

        # Batch native reads, while preserving namespace boundaries, admission
        # before equality, and every original module/class/value observation.
        # These are immutable read schedules, NOT remembered validation.
        module_targets = tuple(row[0] for row in module_plans)
        # These are LIVE views of non-replaceable namespace dictionaries, not
        # snapshots or successful checks. Exact owner/metaclass identities are
        # checked before their contents are read at every boundary.
        module_namespaces = tuple(get(module, "__dict__") for module in module_targets)
        module_kinds = (module_kind,) * native_len(module_targets)
        module_names = tuple(row[1] for row in module_plans)
        module_lengths = tuple(native_len(row[3]) for row in module_plans)
        module_values = tuple(value for row in module_plans for value in row[3])
        class_targets = tuple(row[0] for row in class_plans)
        class_kinds = tuple(row[1] for row in class_plans)
        class_namespaces = tuple(cls_get(cls, "__dict__") for cls in class_targets)
        class_names = tuple(row[2] for row in class_plans)
        class_lengths = tuple(native_len(row[4]) for row in class_plans)
        class_values = tuple(value for row in class_plans for value in row[4])
        class_bases_names = ("__bases__",) * native_len(class_targets)
        class_mro_names = ("__mro__",) * native_len(class_targets)
        class_bases = tuple(row[1] for row in class_identity)
        class_mros = tuple(row[2] for row in class_identity)
        label_targets = tuple(cls for cls, _, _, labels in class_identity for _ in labels)
        label_names = tuple(name for _, _, _, labels in class_identity for name, _ in labels)
        label_values = tuple(value for _, _, _, labels in class_identity for _, value in labels)
        lower_targets = tuple(row[0] for row in lower_plans)
        lower_lengths = tuple(native_len(row[1]) for row in lower_plans)
        lower_values = tuple(value for row in lower_plans for value in row[2])

        def check():
            # Bound by the existing native owner before this installer runs.
            # No mutable module lookup selects the executable at a boundary.
            native_entry: Any = "__aware_native_topology_scan_anchor_v1__"
            if kind(native_entry) is not string_kind:
                if kind(native_entry) is not BuiltinFunctionType:
                    raise refuse()
                if native_entry(guard, guard_code) is not True:
                    raise refuse()
                return
            if (native_len(module_plans) != native_len(module_targets)
                    or kind(module_targets[0]) is not module_kind
                    or native_len(class_plans) != native_len(class_targets)
                    or native_len(class_identity) != native_len(class_targets)
                    or native_len(lower_plans) != native_len(lower_targets)):
                raise refuse()
            keys = native_tuple(sys_keys())
            if not native_all(native_map(same_object, native_map(kind, keys), (string_kind,) * native_len(keys))):
                raise refuse()
            if (
                sys_get("modules") is not get(registry_get, "__self__")
                or kind(get(registry_get, "__self__")) is not dict
            ):
                raise refuse()
            keys = native_tuple(registry_keys())
            if not native_all(native_map(same_object, native_map(kind, keys), (string_kind,) * native_len(keys))):
                raise refuse()
            for name, expected in registry_rows:
                if registry_get(name) is not expected:
                    raise refuse()
            for singleton, expected_class in singleton_rows:
                if kind(singleton) is not expected_class:
                    raise refuse()
            keys = native_tuple(dict_keys(builtin_namespace))
            if (
                not native_all(native_map(same_object, native_map(kind, keys), (string_kind,) * native_len(keys)))
                or keys != builtin_keys
            ):
                raise refuse()
            current_values = native_tuple(dict_values(builtin_namespace))
            if native_len(current_values) != native_len(builtin_plan[1]) or not native_all(native_map(same_object, current_values, builtin_plan[1])):
                raise refuse()
            if not native_all(native_map(same_object, native_map(kind, module_targets), module_kinds)):
                raise refuse()
            module_keys = native_tuple(native_map(native_tuple, native_map(dict_keys, module_namespaces)))
            keys = native_tuple(flatten(module_keys))
            if (not native_all(native_map(same_object, native_map(kind, keys), (string_kind,) * native_len(keys)))
                    or module_keys != module_names):
                raise refuse()
            current_values = native_tuple(native_map(native_tuple, native_map(dict_values, module_namespaces)))
            if (native_tuple(native_map(native_len, current_values)) != module_lengths
                    or not native_all(native_map(same_object, flatten(current_values), module_values))):
                raise refuse()
            if not native_all(native_map(same_object, native_map(kind, class_targets), class_kinds)):
                raise refuse()
            class_keys = native_tuple(native_map(native_tuple, class_namespaces))
            keys = native_tuple(flatten(class_keys))
            if (not native_all(native_map(same_object, native_map(kind, keys), (string_kind,) * native_len(keys)))
                    or class_keys != class_names):
                raise refuse()
            current_values = native_tuple(native_map(native_tuple, native_map(proxy_values, class_namespaces)))
            if (native_tuple(native_map(native_len, current_values)) != class_lengths
                    or not native_all(native_map(same_object, flatten(current_values), class_values))):
                raise refuse()
            if (not native_all(native_map(same_object, native_map(cls_get, class_targets, class_bases_names), class_bases))
                    or not native_all(native_map(same_object, native_map(cls_get, class_targets, class_mro_names), class_mros))
                    or not native_all(native_map(same_object, native_map(cls_get, label_targets, label_names), label_values))):
                raise refuse()
            if (native_len(container_plans) != native_len(dictionary_targets) + native_len(sequence_targets) + immutable_sequence_count
                    or native_tuple(native_map(native_len, dictionary_targets)) != dictionary_lengths
                    or native_tuple(native_map(native_len, sequence_targets)) != sequence_lengths
                    or not native_all(native_map(same_object, flatten(native_map(dict_keys, dictionary_targets)), dictionary_expected_keys))
                    or not native_all(native_map(same_object, flatten(native_map(dict_values, dictionary_targets)), dictionary_expected_values))
                    or not native_all(native_map(same_object, flatten(sequence_targets), sequence_expected_values))):
                raise refuse()
            if not native_all(native_map(same_object, native_map(read_cell, cell_plan[1]), cell_plan[2])):
                raise refuse()
            for cell in special_cells:
                if read_cell(cell) is not (guard if cell is own_guard_cell else guard_code):
                    raise refuse()
            if (not native_all(native_map(same_object, native_map(read_code, function_targets), function_plan[1]))
                    or not native_all(native_map(same_object, native_map(read_defaults, function_targets), function_plan[2]))
                    or not native_all(native_map(same_object, native_map(read_kwdefaults, function_targets), function_plan[3]))):
                raise refuse()
            # Lower dictionary keys/order were freshly authenticated by the
            # complete container ledger; retain their separate value reread.
            current_values = native_tuple(native_map(native_tuple, native_map(dict_values, lower_targets)))
            if (native_tuple(native_map(native_len, current_values)) != lower_lengths
                    or not native_all(native_map(same_object, flatten(current_values), lower_values))):
                raise refuse()

        guard = check
        guard_code = get(check, "__code__")

    return (seal,)


if _native_scan_module is not None:
    _native_scan_module.bind_topology_installer(_install_dispatch)
