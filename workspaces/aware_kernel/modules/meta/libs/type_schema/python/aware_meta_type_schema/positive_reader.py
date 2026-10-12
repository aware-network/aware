"""Request-scoped authenticated positive reads and zero-write trie patching."""

from __future__ import annotations

import copy
import hashlib
import weakref
from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

from .encoding import digest_payload
from .persistent_index import (
    PERSISTENT_BODY_COORDINATE_CONTRACT,
    PERSISTENT_INDEX_DEPTH,
    PERSISTENT_INDEX_NODE_CONTRACT,
    PersistentBodyAuthority,
    PersistentBodyCoordinate,
    PersistentIndexChild,
    PersistentIndexNode,
    PersistentIndexRoot,
    TypeSchemaPersistentIndexError,
    _create_prevalidated_index_root,
    _meta_type_schema_operation,
    _MetaTypeSchemaOperationContext,
    _prevalidated_digest,
    _prevalidated_index_node_semantic_bytes,
    _prevalidated_json,
    _prevalidated_node_coordinate_wire,
    _protected_operand_wire,
    _require_meta_type_schema_operation,
    decode_persistent_index_node,
    key_digest_path,
)

PERSISTENT_INDEX_MEMBERSHIP_CONTRACT = (
    "aware.meta.type-schema.persistent-index-membership.v1"
)
PERSISTENT_INDEX_PROOF_BUNDLE_CONTRACT = (
    "aware.meta.type-schema.persistent-index-proof-bundle.v1"
)


class TypeSchemaPositiveReadError(ValueError):
    """Raised before substituted or out-of-scope persistent data is consumed."""


@dataclass(frozen=True, slots=True)
class PositiveBodyRead:
    body_ref: str
    body_digest: str
    size_bytes: int
    schema: str
    canonical_bytes: bytes
    cache_hit: bool = False
    elapsed_ns: int = 0

    def __post_init__(self) -> None:
        if type(self.canonical_bytes) is not bytes:
            raise TypeError("canonical_bytes must be exact bytes")
        if not isinstance(self.cache_hit, bool):
            raise TypeError("cache_hit must be bool")
        if type(self.elapsed_ns) is not int or self.elapsed_ns < 0:
            raise TypeError("elapsed_ns must be non-negative int")


@dataclass(frozen=True, slots=True)
class PositiveReadObservation:
    read_count: int = 0
    read_bytes: int = 0
    cache_hits: int = 0
    max_lookup_depth: int = 0
    elapsed_ns: int = 0
    enumeration_attempts: int = 0

    def __post_init__(self) -> None:
        for field in (
            "read_count",
            "read_bytes",
            "cache_hits",
            "max_lookup_depth",
            "elapsed_ns",
            "enumeration_attempts",
        ):
            value = getattr(self, field)
            if type(value) is not int or value < 0:
                raise TypeError(f"{field} must be non-negative int")

    def plus(self, other: PositiveReadObservation) -> PositiveReadObservation:
        return PositiveReadObservation(
            read_count=self.read_count + other.read_count,
            read_bytes=self.read_bytes + other.read_bytes,
            cache_hits=self.cache_hits + other.cache_hits,
            max_lookup_depth=max(self.max_lookup_depth, other.max_lookup_depth),
            elapsed_ns=self.elapsed_ns + other.elapsed_ns,
            enumeration_attempts=(
                self.enumeration_attempts + other.enumeration_attempts
            ),
        )


@dataclass(frozen=True, slots=True)
class PersistentIndexMembershipProof:
    root: PersistentIndexRoot
    key: str
    value: PersistentBodyCoordinate
    node_refs: tuple[str, ...]
    membership_ref: str
    contract: str = PERSISTENT_INDEX_MEMBERSHIP_CONTRACT

    def __post_init__(self) -> None:
        if self.contract != PERSISTENT_INDEX_MEMBERSHIP_CONTRACT:
            raise TypeSchemaPositiveReadError("membership proof contract unsupported")
        if not isinstance(self.root, PersistentIndexRoot):
            raise TypeError("membership root must be PersistentIndexRoot")
        _ = key_digest_path(self.key)
        if not isinstance(self.value, PersistentBodyCoordinate):
            raise TypeError("membership value must be PersistentBodyCoordinate")
        if (
            type(self.node_refs) is not tuple
            or len(self.node_refs) != PERSISTENT_INDEX_DEPTH + 1
        ):
            raise TypeSchemaPositiveReadError(
                "membership proof requires one immutable node ref per index depth"
            )
        if any(not isinstance(value, str) or not value for value in self.node_refs):
            raise TypeSchemaPositiveReadError(
                "membership node refs must be nonempty text"
            )
        expected = digest_payload(self.contract, self.semantic_wire())
        if self.membership_ref != expected:
            raise TypeSchemaPositiveReadError(
                f"membership_ref mismatch; expected {expected}"
            )

    @classmethod
    def create(
        cls,
        *,
        root: PersistentIndexRoot,
        key: str,
        value: PersistentBodyCoordinate,
        node_refs: tuple[str, ...],
    ) -> PersistentIndexMembershipProof:
        semantic = {
            "contract": PERSISTENT_INDEX_MEMBERSHIP_CONTRACT,
            "root": root.to_wire(),
            "key": key,
            "value": value.to_wire(),
            "node_refs": list(node_refs),
        }
        return cls(
            root,
            key,
            value,
            node_refs,
            digest_payload(PERSISTENT_INDEX_MEMBERSHIP_CONTRACT, semantic),
        )

    def semantic_wire(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "root": self.root.to_wire(),
            "key": self.key,
            "value": self.value.to_wire(),
            "node_refs": list(self.node_refs),
        }

    def to_wire(self) -> dict[str, object]:
        return {**self.semantic_wire(), "membership_ref": self.membership_ref}


def _create_prevalidated_membership_proof(
    context: _MetaTypeSchemaOperationContext,
    *,
    root: PersistentIndexRoot,
    key: str,
    value: PersistentBodyCoordinate,
    node_refs: tuple[str, ...],
) -> PersistentIndexMembershipProof:
    _require_meta_type_schema_operation(context)
    semantic = {
        "contract": PERSISTENT_INDEX_MEMBERSHIP_CONTRACT,
        "root": root.to_wire(),
        "key": key,
        "value": value.to_wire(),
        "node_refs": list(node_refs),
    }
    proof = object.__new__(PersistentIndexMembershipProof)
    object.__setattr__(proof, "root", root)
    object.__setattr__(proof, "key", key)
    object.__setattr__(proof, "value", value)
    object.__setattr__(proof, "node_refs", node_refs)
    object.__setattr__(
        proof,
        "membership_ref",
        _prevalidated_digest(PERSISTENT_INDEX_MEMBERSHIP_CONTRACT, semantic),
    )
    object.__setattr__(proof, "contract", PERSISTENT_INDEX_MEMBERSHIP_CONTRACT)
    return proof


@dataclass(frozen=True, slots=True)
class PersistentIndexProofBundle:
    memberships: tuple[PersistentIndexMembershipProof, ...]
    nodes: tuple[PersistentIndexNode, ...]
    bundle_ref: str
    contract: str = PERSISTENT_INDEX_PROOF_BUNDLE_CONTRACT

    def __post_init__(self) -> None:
        if self.contract != PERSISTENT_INDEX_PROOF_BUNDLE_CONTRACT:
            raise TypeSchemaPositiveReadError("proof bundle contract unsupported")
        if type(self.memberships) is not tuple or type(self.nodes) is not tuple:
            raise TypeSchemaPositiveReadError(
                "proof bundle values must be immutable tuples"
            )
        if self.memberships != tuple(
            sorted(self.memberships, key=lambda value: value.membership_ref)
        ) or len({value.membership_ref for value in self.memberships}) != len(
            self.memberships
        ):
            raise TypeSchemaPositiveReadError(
                "proof memberships must be typed, sorted and unique"
            )
        if self.nodes != tuple(
            sorted(self.nodes, key=lambda value: value.node_ref)
        ) or len({value.node_ref for value in self.nodes}) != len(self.nodes):
            raise TypeSchemaPositiveReadError(
                "proof nodes must be typed, sorted and deduplicated"
            )
        node_by_ref = {node.node_ref: node for node in self.nodes}
        used: set[str] = set()
        for membership in self.memberships:
            if not isinstance(membership, PersistentIndexMembershipProof):
                raise TypeError("proof membership has unsupported type")
            path = key_digest_path(membership.key)
            expected_coordinate = membership.root.root_node
            for depth, node_ref in enumerate(membership.node_refs):
                node = node_by_ref.get(node_ref)
                if node is None:
                    raise TypeSchemaPositiveReadError("membership proof node is absent")
                used.add(node_ref)
                if node.to_body().coordinate != expected_coordinate:
                    raise TypeSchemaPositiveReadError(
                        "membership proof coordinate/path substitution"
                    )
                if (
                    node.keyspace != membership.root.keyspace
                    or node.depth != depth
                    or node.path != path[:depth]
                ):
                    raise TypeSchemaPositiveReadError(
                        "membership proof node does not bind exact index path"
                    )
                if depth == PERSISTENT_INDEX_DEPTH:
                    if node.key != membership.key or node.value != membership.value:
                        raise TypeSchemaPositiveReadError(
                            "membership proof leaf does not bind exact key/value"
                        )
                    continue
                child = next(
                    (item for item in node.children if item.nibble == path[depth]),
                    None,
                )
                if child is None:
                    raise TypeSchemaPositiveReadError(
                        "membership proof path terminates before leaf"
                    )
                expected_coordinate = child.node
        if used != set(node_by_ref):
            raise TypeSchemaPositiveReadError("proof bundle contains unused nodes")
        expected = digest_payload(self.contract, self.semantic_wire())
        if self.bundle_ref != expected:
            raise TypeSchemaPositiveReadError(
                f"bundle_ref mismatch; expected {expected}"
            )

    @classmethod
    def create(
        cls,
        *,
        memberships: tuple[PersistentIndexMembershipProof, ...],
        nodes: tuple[PersistentIndexNode, ...],
    ) -> PersistentIndexProofBundle:
        memberships = tuple(sorted(memberships, key=lambda value: value.membership_ref))
        nodes = tuple(
            sorted(
                {value.node_ref: value for value in nodes}.values(),
                key=lambda value: value.node_ref,
            )
        )
        semantic = {
            "contract": PERSISTENT_INDEX_PROOF_BUNDLE_CONTRACT,
            "memberships": [value.to_wire() for value in memberships],
            "nodes": [value.to_wire() for value in nodes],
        }
        return cls(
            memberships,
            nodes,
            digest_payload(PERSISTENT_INDEX_PROOF_BUNDLE_CONTRACT, semantic),
        )

    def semantic_wire(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "memberships": [value.to_wire() for value in self.memberships],
            "nodes": [value.to_wire() for value in self.nodes],
        }

    def to_wire(self) -> dict[str, object]:
        return {**self.semantic_wire(), "bundle_ref": self.bundle_ref}


def _create_prevalidated_proof_bundle(
    context: _MetaTypeSchemaOperationContext,
    *,
    memberships: tuple[PersistentIndexMembershipProof, ...],
    nodes: tuple[PersistentIndexNode, ...],
) -> PersistentIndexProofBundle:
    """Assemble evidence freshly proved by one private Meta resolution call."""

    result, _ = _create_prevalidated_proof_bundle_with_wire(
        context,
        memberships=memberships,
        nodes=nodes,
    )
    return result


def _create_prevalidated_proof_bundle_with_wire(
    context: _MetaTypeSchemaOperationContext,
    *,
    memberships: tuple[PersistentIndexMembershipProof, ...],
    nodes: tuple[PersistentIndexNode, ...],
    node_wires: dict[str, tuple[PersistentIndexNode, bytes]] | None = None,
) -> tuple[PersistentIndexProofBundle, bytes]:
    """Assemble one bundle and its canonical wire without rewalking its graph."""

    _require_meta_type_schema_operation(context)
    ordered_memberships = tuple(
        sorted(memberships, key=lambda value: value.membership_ref)
    )
    if len({value.membership_ref for value in ordered_memberships}) != len(
        ordered_memberships
    ):
        raise TypeSchemaPositiveReadError("proof memberships are not unique")
    ordered_nodes = tuple(
        sorted(
            {value.node_ref: value for value in nodes}.values(),
            key=lambda value: value.node_ref,
        )
    )
    membership_bytes = tuple(
        _prevalidated_json(value.to_wire()) for value in ordered_memberships
    )
    node_bytes: list[bytes] = []
    for value in ordered_nodes:
        retained = None if node_wires is None else node_wires.get(value.node_ref)
        node_bytes.append(
            retained[1]
            if retained is not None and retained[0] is value
            else _prevalidated_json(value.to_wire())
        )
    semantic_bytes = b"".join(
        (
            b'{"contract":"',
            PERSISTENT_INDEX_PROOF_BUNDLE_CONTRACT.encode("ascii"),
            b'","memberships":[',
            b",".join(membership_bytes),
            b'],"nodes":[',
            b",".join(node_bytes),
            b"]}",
        )
    )
    bundle_ref = "sha256:" + hashlib.sha256(
        PERSISTENT_INDEX_PROOF_BUNDLE_CONTRACT.encode("utf-8")
        + b"\n"
        + semantic_bytes
    ).hexdigest()
    result = object.__new__(PersistentIndexProofBundle)
    object.__setattr__(result, "memberships", ordered_memberships)
    object.__setattr__(result, "nodes", ordered_nodes)
    object.__setattr__(
        result,
        "bundle_ref",
        bundle_ref,
    )
    object.__setattr__(result, "contract", PERSISTENT_INDEX_PROOF_BUNDLE_CONTRACT)
    # ``bundle_ref`` sorts before ``contract``. Insert it into the already
    # canonical semantic object rather than recursively serializing the same
    # membership/node closure a second time.
    wire = b'{"bundle_ref":"' + bundle_ref.encode("ascii") + b'",' + semantic_bytes[1:]
    return result, wire


class _AdmittedPersistentIndexProofBundle:
    """Opaque execution-local admission used only by Meta composition."""

    __slots__ = ("__weakref__",)


@dataclass(frozen=True, slots=True)
class _ProofBundleAdmissionContext:
    membership_values: tuple[object, ...]
    membership_offsets: dict[str, int]
    node_values: tuple[object, ...]
    node_offsets: dict[str, int]


def _capture_proof_bundle_values(
    bundle: PersistentIndexProofBundle,
) -> _ProofBundleAdmissionContext:
    """Retain one admitted proof closure without cloning its public graph."""

    membership_values: list[object] = []
    membership_offsets: dict[str, int] = {}
    for value in bundle.memberships:
        membership_offsets[value.membership_ref] = len(membership_values)
        membership_values.extend(
            (
                value.membership_ref,
                value.root.keyspace,
                *_reader_coordinate_values(value.root.root_node),
                value.root.binding_count,
                value.root.root_ref,
                value.root.contract,
                value.key,
                *_reader_coordinate_values(value.value),
                value.node_refs,
                value.contract,
            )
        )

    node_values: list[object] = []
    node_offsets: dict[str, int] = {}
    for value in bundle.nodes:
        node_offsets[value.node_ref] = len(node_values)
        node_values.extend(
            (
                value.node_ref,
                value.keyspace,
                value.depth,
                value.path,
                len(value.children),
            )
        )
        for child in value.children:
            node_values.append(child.nibble)
            node_values.extend(_reader_coordinate_values(child.node))
        node_values.extend((value.key, value.value is not None))
        if value.value is not None:
            node_values.extend(_reader_coordinate_values(value.value))
        node_values.append(value.contract)
    return _ProofBundleAdmissionContext(
        tuple(membership_values),
        membership_offsets,
        tuple(node_values),
        node_offsets,
    )


def _membership_from_admission_values(
    context: _ProofBundleAdmissionContext,
    membership_ref: str,
) -> PersistentIndexMembershipProof:
    offset = context.membership_offsets[membership_ref]
    values = context.membership_values
    root = object.__new__(PersistentIndexRoot)
    object.__setattr__(root, "keyspace", values[offset + 1])
    object.__setattr__(
        root,
        "root_node",
        _coordinate_from_values(
            cast(
                tuple[str, str, str, str, str, int, str, str],
                values[offset + 2 : offset + 10],
            )
        ),
    )
    object.__setattr__(root, "binding_count", values[offset + 10])
    object.__setattr__(root, "root_ref", values[offset + 11])
    object.__setattr__(root, "contract", values[offset + 12])
    result = object.__new__(PersistentIndexMembershipProof)
    object.__setattr__(result, "root", root)
    object.__setattr__(result, "key", values[offset + 13])
    object.__setattr__(
        result,
        "value",
        _coordinate_from_values(
            cast(
                tuple[str, str, str, str, str, int, str, str],
                values[offset + 14 : offset + 22],
            )
        ),
    )
    object.__setattr__(result, "node_refs", values[offset + 22])
    object.__setattr__(result, "membership_ref", values[offset])
    object.__setattr__(result, "contract", values[offset + 23])
    return result


def _node_from_admission_values(
    context: _ProofBundleAdmissionContext,
    node_ref: str,
) -> PersistentIndexNode:
    offset = context.node_offsets[node_ref]
    values = context.node_values
    child_count = values[offset + 4]
    if type(child_count) is not int:
        raise AssertionError("admitted proof child count must be exact")
    cursor = offset + 5
    children: list[PersistentIndexChild] = []
    for _ in range(child_count):
        child = object.__new__(PersistentIndexChild)
        object.__setattr__(child, "nibble", values[cursor])
        object.__setattr__(
            child,
            "node",
            _coordinate_from_values(
                cast(
                    tuple[str, str, str, str, str, int, str, str],
                    values[cursor + 1 : cursor + 9],
                )
            ),
        )
        children.append(child)
        cursor += 9
    key = values[cursor]
    has_value = values[cursor + 1]
    cursor += 2
    coordinate = None
    if has_value is True:
        coordinate = _coordinate_from_values(
            cast(
                tuple[str, str, str, str, str, int, str, str],
                values[cursor : cursor + 8],
            )
        )
        cursor += 8
    result = object.__new__(PersistentIndexNode)
    object.__setattr__(result, "keyspace", values[offset + 1])
    object.__setattr__(result, "depth", values[offset + 2])
    object.__setattr__(result, "path", values[offset + 3])
    object.__setattr__(result, "children", tuple(children))
    object.__setattr__(result, "key", key)
    object.__setattr__(result, "value", coordinate)
    object.__setattr__(result, "node_ref", values[offset])
    object.__setattr__(result, "contract", values[cursor])
    return result


_PROOF_BUNDLE_ADMISSIONS: dict[
    int,
    tuple[
        weakref.ReferenceType[_AdmittedPersistentIndexProofBundle],
        _ProofBundleAdmissionContext,
    ],
] = {}
_PREVALIDATED_PROOF_BUNDLE_ADMISSION_TOKEN = object()


def _admit_validated_proof_bundle(
    bundle: PersistentIndexProofBundle,
    *,
    _token: object | None = None,
) -> _AdmittedPersistentIndexProofBundle:
    """Retain a bundle that was produced by a strict Meta decode."""

    if _token is _PREVALIDATED_PROOF_BUNDLE_ADMISSION_TOKEN:
        # The enclosing Meta operation has already recursively admitted and
        # terminally verified this exact public result.  Capture its admitted
        # scalar values immediately into flat private storage; the public graph
        # itself is never retained by the stable admission.
        validated = bundle
    else:
        validated = _strict_proof_bundle(bundle)
    admission = _AdmittedPersistentIndexProofBundle()
    admission_id = id(admission)

    def discard(
        reference: weakref.ReferenceType[_AdmittedPersistentIndexProofBundle],
        *,
        retained_id: int = admission_id,
    ) -> None:
        retained = _PROOF_BUNDLE_ADMISSIONS.get(retained_id)
        if retained is not None and retained[0] is reference:
            _PROOF_BUNDLE_ADMISSIONS.pop(retained_id, None)

    reference = weakref.ref(admission, discard)
    _PROOF_BUNDLE_ADMISSIONS[admission_id] = (
        reference,
        _capture_proof_bundle_values(validated),
    )
    return admission


def _advance_admitted_proof_bundle(
    operation_context: _MetaTypeSchemaOperationContext,
    admission: _AdmittedPersistentIndexProofBundle,
    *,
    retained_membership_refs: tuple[str, ...],
    fresh_memberships: tuple[PersistentIndexMembershipProof, ...],
    fresh_nodes: tuple[PersistentIndexNode, ...],
) -> PersistentIndexProofBundle:
    """Issue one exact bundle from admitted retained and freshly proved parts.

    This is a Meta-private issuance seam. Public construction and strict decode
    continue to validate every membership path and node.
    """

    _require_meta_type_schema_operation(operation_context)
    context = _proof_bundle_admission_context(admission)
    if (
        type(retained_membership_refs) is not tuple
        or any(
            type(value) is not str or not value for value in retained_membership_refs
        )
        or retained_membership_refs != tuple(sorted(set(retained_membership_refs)))
    ):
        raise TypeSchemaPositiveReadError(
            "retained membership refs must be sorted and unique"
        )
    if type(fresh_memberships) is not tuple or type(fresh_nodes) is not tuple:
        raise TypeSchemaPositiveReadError("fresh proof values must be exact tuples")
    # Fresh evidence is fully validated through the ordinary constructor. The
    # potentially large retained closure was fully validated at admission and
    # is selected only by its privately retained membership identity.
    fresh = _create_prevalidated_proof_bundle(
        operation_context,
        memberships=tuple(_strict_membership(value) for value in fresh_memberships),
        nodes=tuple(_strict_node(value) for value in fresh_nodes),
    )
    if any(
        value not in context.membership_offsets
        for value in retained_membership_refs
    ):
        raise TypeSchemaPositiveReadError(
            "retained membership ref is outside admitted bundle"
        )
    # Never expose objects retained by the opaque admission. A public result is
    # deliberately mutable through low-level Python mechanisms such as
    # ``object.__setattr__`` despite the frozen dataclass surface; every issue
    # therefore receives a strict detached copy.
    retained_memberships = tuple(
        _membership_from_admission_values(context, value)
        for value in retained_membership_refs
    )
    fresh_refs = {value.membership_ref for value in fresh.memberships}
    if fresh_refs.intersection(retained_membership_refs):
        raise TypeSchemaPositiveReadError(
            "fresh and retained membership evidence overlap"
        )

    retained_node_refs = {
        node_ref
        for membership in retained_memberships
        for node_ref in membership.node_refs
    }
    retained_node_by_ref = {
        node_ref: _node_from_admission_values(context, node_ref)
        for node_ref in retained_node_refs
        if node_ref in context.node_offsets
    }
    if not retained_node_refs.issubset(retained_node_by_ref):
        raise TypeSchemaPositiveReadError("admitted retained membership node is absent")
    nodes_by_ref = {
        value.node_ref: value
        for value in retained_node_by_ref.values()
        if value.node_ref in retained_node_refs
    }
    for node in fresh.nodes:
        retained = nodes_by_ref.get(node.node_ref)
        if retained is not None and retained != node:
            raise TypeSchemaPositiveReadError(
                "fresh node ref conflicts with admitted retained node"
            )
        nodes_by_ref[node.node_ref] = node

    memberships = tuple(
        sorted(
            (*retained_memberships, *fresh.memberships),
            key=lambda value: value.membership_ref,
        )
    )
    if len({value.membership_ref for value in memberships}) != len(memberships):
        raise TypeSchemaPositiveReadError("combined memberships are not unique")
    nodes = tuple(sorted(nodes_by_ref.values(), key=lambda value: value.node_ref))
    semantic = {
        "contract": PERSISTENT_INDEX_PROOF_BUNDLE_CONTRACT,
        "memberships": [value.to_wire() for value in memberships],
        "nodes": [value.to_wire() for value in nodes],
    }

    # Meta alone owns this selective issuance. The resulting public value is
    # ordinary wire-compatible proof authority; any later decode replays the
    # complete validation path.
    result = object.__new__(PersistentIndexProofBundle)
    object.__setattr__(result, "memberships", memberships)
    object.__setattr__(result, "nodes", nodes)
    object.__setattr__(
        result,
        "bundle_ref",
        digest_payload(PERSISTENT_INDEX_PROOF_BUNDLE_CONTRACT, semantic),
    )
    object.__setattr__(result, "contract", PERSISTENT_INDEX_PROOF_BUNDLE_CONTRACT)
    return result


def _proof_bundle_admission_context(
    admission: _AdmittedPersistentIndexProofBundle,
) -> _ProofBundleAdmissionContext:
    if type(admission) is not _AdmittedPersistentIndexProofBundle:
        raise TypeSchemaPositiveReadError("proof bundle admission is not exact")
    retained = _PROOF_BUNDLE_ADMISSIONS.get(id(admission))
    if retained is None or retained[0]() is not admission:
        raise TypeSchemaPositiveReadError("proof bundle admission is not active")
    return retained[1]


def _strict_proof_bundle(
    value: PersistentIndexProofBundle,
) -> PersistentIndexProofBundle:
    if type(value) is not PersistentIndexProofBundle:
        raise TypeSchemaPositiveReadError(
            "proof bundle admission requires exact validated bundle"
        )
    try:
        rebuilt = PersistentIndexProofBundle(
            memberships=tuple(_strict_membership(item) for item in value.memberships),
            nodes=tuple(_strict_node(item) for item in value.nodes),
            bundle_ref=value.bundle_ref,
            contract=value.contract,
        )
    except (TypeError, ValueError) as error:
        raise TypeSchemaPositiveReadError(
            f"proof bundle admission is not strict: {error}"
        ) from error
    if rebuilt != value:
        raise TypeSchemaPositiveReadError(
            "proof bundle differs from strict reconstruction"
        )
    return rebuilt


def _strict_membership(
    value: PersistentIndexMembershipProof,
) -> PersistentIndexMembershipProof:
    if type(value) is not PersistentIndexMembershipProof:
        raise TypeSchemaPositiveReadError("proof membership has foreign type")
    return PersistentIndexMembershipProof(
        root=_strict_root(value.root),
        key=value.key,
        value=_strict_coordinate(value.value),
        node_refs=value.node_refs,
        membership_ref=value.membership_ref,
        contract=value.contract,
    )


def _strict_node(value: PersistentIndexNode) -> PersistentIndexNode:
    if type(value) is not PersistentIndexNode:
        raise TypeSchemaPositiveReadError("proof node has foreign type")
    children: list[PersistentIndexChild] = []
    for child in value.children:
        if type(child) is not PersistentIndexChild:
            raise TypeSchemaPositiveReadError("proof child has foreign type")
        children.append(
            PersistentIndexChild(child.nibble, _strict_coordinate(child.node))
        )
    return PersistentIndexNode(
        keyspace=value.keyspace,
        depth=value.depth,
        path=value.path,
        children=tuple(children),
        key=value.key,
        value=None if value.value is None else _strict_coordinate(value.value),
        node_ref=value.node_ref,
        contract=value.contract,
    )


def _strict_root(value: PersistentIndexRoot) -> PersistentIndexRoot:
    if type(value) is not PersistentIndexRoot:
        raise TypeSchemaPositiveReadError("proof root has foreign type")
    return PersistentIndexRoot(
        keyspace=value.keyspace,
        root_node=_strict_coordinate(value.root_node),
        binding_count=value.binding_count,
        root_ref=value.root_ref,
        contract=value.contract,
    )


def _strict_coordinate(value: PersistentBodyCoordinate) -> PersistentBodyCoordinate:
    if type(value) is not PersistentBodyCoordinate:
        raise TypeSchemaPositiveReadError("proof coordinate has foreign type")
    text_fields = (
        "schema",
        "ref_field",
        "authority_ref",
        "body_ref",
        "body_digest",
        "coordinate_ref",
        "contract",
    )
    if (
        any(
            type(object.__getattribute__(value, field)) is not str
            for field in text_fields
        )
        or type(object.__getattribute__(value, "size_bytes")) is not int
    ):
        raise TypeSchemaPositiveReadError(
            "proof coordinate contains foreign scalar value"
        )
    return PersistentBodyCoordinate(
        schema=value.schema,
        ref_field=value.ref_field,
        authority_ref=value.authority_ref,
        body_ref=value.body_ref,
        body_digest=value.body_digest,
        size_bytes=value.size_bytes,
        coordinate_ref=value.coordinate_ref,
        contract=value.contract,
    )


def _detach_admitted_coordinate(
    value: PersistentBodyCoordinate,
) -> PersistentBodyCoordinate:
    """Detach a coordinate already protected by private strict admission."""

    result = object.__new__(PersistentBodyCoordinate)
    for field in (
        "schema",
        "ref_field",
        "authority_ref",
        "body_ref",
        "body_digest",
        "size_bytes",
        "coordinate_ref",
        "contract",
    ):
        object.__setattr__(result, field, object.__getattribute__(value, field))
    return result


def _protect_reader_coordinate(
    value: PersistentBodyCoordinate,
) -> PersistentBodyCoordinate:
    """Snapshot one exact coordinate before any provider callback executes.

    The enclosing root/node/transition authority already admitted coordinate
    semantics. This seam rechecks exact owned scalar shapes and the CAS body-ref
    binding, then detaches without repeating the coordinate digest computation
    for every positive read.
    """

    if type(value) is not PersistentBodyCoordinate:
        raise TypeSchemaPositiveReadError("reader expected coordinate has foreign type")
    schema = object.__getattribute__(value, "schema")
    ref_field = object.__getattribute__(value, "ref_field")
    authority_ref = object.__getattribute__(value, "authority_ref")
    body_ref = object.__getattribute__(value, "body_ref")
    body_digest = object.__getattribute__(value, "body_digest")
    coordinate_ref = object.__getattribute__(value, "coordinate_ref")
    contract = object.__getattribute__(value, "contract")
    size_bytes = object.__getattribute__(value, "size_bytes")
    if any(
        type(item) is not str or not item
        for item in (
            schema,
            ref_field,
            authority_ref,
            body_ref,
            body_digest,
            coordinate_ref,
            contract,
        )
    ) or (type(size_bytes) is not int or size_bytes < 0):
        raise TypeSchemaPositiveReadError(
            "reader expected coordinate contains foreign scalar value"
        )
    if (
        len(body_digest) != 71
        or not body_digest.startswith("sha256:")
        or body_digest != body_digest.lower()
    ):
        raise TypeSchemaPositiveReadError(
            "reader expected coordinate body digest is not SHA-256"
        )
    if body_ref != f"cas://aware-meta-type-schema/{body_digest[7:]}":
        raise TypeSchemaPositiveReadError(
            "reader expected coordinate body_ref is not canonical"
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


def _reader_coordinate_values(
    value: PersistentBodyCoordinate,
) -> tuple[str, str, str, str, str, int, str, str]:
    """Preflight and snapshot exact scalar authority for a positive read."""

    if type(value) is not PersistentBodyCoordinate:
        raise TypeSchemaPositiveReadError("reader expected coordinate has foreign type")
    schema = object.__getattribute__(value, "schema")
    ref_field = object.__getattribute__(value, "ref_field")
    authority_ref = object.__getattribute__(value, "authority_ref")
    body_ref = object.__getattribute__(value, "body_ref")
    body_digest = object.__getattribute__(value, "body_digest")
    size_bytes = object.__getattribute__(value, "size_bytes")
    coordinate_ref = object.__getattribute__(value, "coordinate_ref")
    contract = object.__getattribute__(value, "contract")
    if any(
        type(item) is not str or not item
        for item in (
            schema,
            ref_field,
            authority_ref,
            body_ref,
            body_digest,
            coordinate_ref,
            contract,
        )
    ) or (type(size_bytes) is not int or size_bytes < 0):
        raise TypeSchemaPositiveReadError(
            "reader expected coordinate contains foreign scalar value"
        )
    if (
        len(body_digest) != 71
        or not body_digest.startswith("sha256:")
        or body_digest != body_digest.lower()
    ):
        raise TypeSchemaPositiveReadError(
            "reader expected coordinate body digest is not SHA-256"
        )
    if body_ref != f"cas://aware-meta-type-schema/{body_digest[7:]}":
        raise TypeSchemaPositiveReadError(
            "reader expected coordinate body_ref is not canonical"
        )
    return (
        schema,
        ref_field,
        authority_ref,
        body_ref,
        body_digest,
        size_bytes,
        coordinate_ref,
        contract,
    )


def _coordinate_from_values(
    values: tuple[str, str, str, str, str, int, str, str],
) -> PersistentBodyCoordinate:
    result = object.__new__(PersistentBodyCoordinate)
    for field, value in zip(
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
        values,
        strict=True,
    ):
        object.__setattr__(result, field, value)
    return result


def _detach_admitted_root(value: PersistentIndexRoot) -> PersistentIndexRoot:
    result = object.__new__(PersistentIndexRoot)
    object.__setattr__(result, "keyspace", value.keyspace)
    object.__setattr__(
        result, "root_node", _detach_admitted_coordinate(value.root_node)
    )
    object.__setattr__(result, "binding_count", value.binding_count)
    object.__setattr__(result, "root_ref", value.root_ref)
    object.__setattr__(result, "contract", value.contract)
    return result


def _detach_admitted_membership(
    value: PersistentIndexMembershipProof,
) -> PersistentIndexMembershipProof:
    result = object.__new__(PersistentIndexMembershipProof)
    object.__setattr__(result, "root", _detach_admitted_root(value.root))
    object.__setattr__(result, "key", value.key)
    object.__setattr__(result, "value", _detach_admitted_coordinate(value.value))
    object.__setattr__(result, "node_refs", tuple(value.node_refs))
    object.__setattr__(result, "membership_ref", value.membership_ref)
    object.__setattr__(result, "contract", value.contract)
    return result


def _detach_admitted_node(value: PersistentIndexNode) -> PersistentIndexNode:
    result = object.__new__(PersistentIndexNode)
    object.__setattr__(result, "keyspace", value.keyspace)
    object.__setattr__(result, "depth", value.depth)
    object.__setattr__(result, "path", value.path)
    children = []
    for child in value.children:
        detached_child = object.__new__(PersistentIndexChild)
        object.__setattr__(detached_child, "nibble", child.nibble)
        object.__setattr__(
            detached_child, "node", _detach_admitted_coordinate(child.node)
        )
        children.append(detached_child)
    object.__setattr__(result, "children", tuple(children))
    object.__setattr__(result, "key", value.key)
    object.__setattr__(
        result,
        "value",
        None if value.value is None else _detach_admitted_coordinate(value.value),
    )
    object.__setattr__(result, "node_ref", value.node_ref)
    object.__setattr__(result, "contract", value.contract)
    return result


class _OperationBodyFragmentArena:
    """Compact parallel storage for operation-owned canonical fragments."""

    __slots__ = ("_canonical_bytes", "_coordinate_values", "_fragments")

    def __init__(self) -> None:
        self._coordinate_values: dict[str, object] = {}
        self._canonical_bytes: dict[str, bytes] = {}
        self._fragments: dict[str, bytes] = {}

    def __contains__(self, coordinate_ref: object) -> bool:
        return coordinate_ref in self._fragments

    def __getitem__(self, coordinate_ref: str) -> tuple[object, bytes, bytes]:
        return (
            self._coordinate_values[coordinate_ref],
            self._canonical_bytes[coordinate_ref],
            self._fragments[coordinate_ref],
        )

    def __setitem__(
        self, coordinate_ref: str, value: tuple[object, bytes, bytes]
    ) -> None:
        coordinate_values, canonical_bytes, fragment = value
        self._coordinate_values[coordinate_ref] = coordinate_values
        self._canonical_bytes[coordinate_ref] = canonical_bytes
        self._fragments[coordinate_ref] = fragment

    def get(
        self, coordinate_ref: str, default: object = None
    ) -> tuple[object, bytes, bytes] | object:
        if coordinate_ref not in self._fragments:
            return default
        return self[coordinate_ref]


class _OperationDecodedNodeArena(dict[str, tuple[object, bytes, PersistentIndexNode]]):
    """High-level operation arena whose admitted nodes skip reader callbacks."""

    def __init__(self) -> None:
        super().__init__()
        self.body_fragments = _OperationBodyFragmentArena()
        self.coordinate_wires: dict[
            int, tuple[PersistentBodyCoordinate, bytes]
        ] = {}


class TypeSchemaPositiveReaderCapability:
    """Ephemeral exact-request reader. It is not an authority or wire value."""

    __slots__ = ("_callback", "_request_ref")

    def __hash__(self) -> int:
        raise TypeError("reader capability is request-scoped and unhashable")

    def __init__(
        self,
        *,
        request_ref: str,
        read_body: Callable[[PersistentBodyCoordinate], PositiveBodyRead],
    ) -> None:
        if not isinstance(request_ref, str) or not request_ref.strip():
            raise TypeSchemaPositiveReadError("request_ref must be normalized text")
        if not callable(read_body):
            raise TypeError("read_body must be callable")
        self._request_ref = request_ref
        self._callback = read_body

    @property
    def request_ref(self) -> str:
        return self._request_ref

    def read_exact(
        self,
        *,
        request_ref: str,
        expected: PersistentBodyCoordinate,
        lookup_depth: int,
    ) -> tuple[PersistentBodyAuthority, PositiveReadObservation]:
        retained_request_ref = object.__getattribute__(self, "_request_ref")
        if (
            type(request_ref) is not str
            or type(retained_request_ref) is not str
            or not request_ref
            or not retained_request_ref
            or request_ref.strip() != request_ref
            or retained_request_ref.strip() != retained_request_ref
        ):
            raise TypeSchemaPositiveReadError(
                "reader request_ref must be exact normalized text"
            )
        if request_ref != retained_request_ref:
            raise TypeSchemaPositiveReadError(
                "reader capability belongs to another request"
            )
        protected_expected = _protect_reader_coordinate(expected)
        if type(lookup_depth) is not int or lookup_depth < 0:
            raise TypeError("lookup_depth must be non-negative int")
        callback_expected = _detach_admitted_coordinate(protected_expected)
        result = self._callback(callback_expected)
        if type(result) is not PositiveBodyRead:
            raise TypeSchemaPositiveReadError("reader returned unsupported body result")
        if (
            type(result.body_ref) is not str
            or type(result.body_digest) is not str
            or type(result.size_bytes) is not int
            or type(result.schema) is not str
            or type(result.canonical_bytes) is not bytes
            or type(result.cache_hit) is not bool
            or type(result.elapsed_ns) is not int
        ):
            raise TypeSchemaPositiveReadError(
                "reader returned foreign body envelope value"
            )
        if result.body_ref != protected_expected.body_ref:
            raise TypeSchemaPositiveReadError("reader body_ref substitution")
        if result.body_digest != protected_expected.body_digest:
            raise TypeSchemaPositiveReadError("reader body digest substitution")
        if result.size_bytes != protected_expected.size_bytes:
            raise TypeSchemaPositiveReadError("reader body size substitution")
        if result.schema != protected_expected.schema:
            raise TypeSchemaPositiveReadError("reader body schema substitution")
        actual_digest = "sha256:" + hashlib.sha256(result.canonical_bytes).hexdigest()
        if actual_digest != protected_expected.body_digest:
            raise TypeSchemaPositiveReadError(
                "reader bytes do not match expected digest"
            )
        if len(result.canonical_bytes) != protected_expected.size_bytes:
            raise TypeSchemaPositiveReadError("reader bytes do not match expected size")
        try:
            body = PersistentBodyAuthority(
                _detach_admitted_coordinate(protected_expected),
                result.canonical_bytes,
            )
        except (TypeError, TypeSchemaPersistentIndexError) as error:
            raise TypeSchemaPositiveReadError(
                f"reader returned invalid canonical authority: {error}"
            ) from error
        return body, PositiveReadObservation(
            read_count=1,
            read_bytes=len(result.canonical_bytes),
            cache_hits=int(result.cache_hit),
            max_lookup_depth=lookup_depth,
            elapsed_ns=result.elapsed_ns,
        )

    def _read_index_node_exact(
        self,
        *,
        request_ref: str,
        expected: PersistentBodyCoordinate,
        lookup_depth: int,
        decoded_nodes: dict[
            str,
            tuple[
                tuple[str, str, str, str, str, int, str, str],
                bytes,
                PersistentIndexNode,
            ],
        ]
        | None = None,
    ) -> tuple[PersistentIndexNode, PositiveReadObservation]:
        """Read and validate an index node with one canonical JSON parse."""

        retained_request_ref = object.__getattribute__(self, "_request_ref")
        if (
            type(request_ref) is not str
            or type(retained_request_ref) is not str
            or not request_ref
            or not retained_request_ref
            or request_ref.strip() != request_ref
            or retained_request_ref.strip() != retained_request_ref
        ):
            raise TypeSchemaPositiveReadError(
                "reader request_ref must be exact normalized text"
            )
        if request_ref != retained_request_ref:
            raise TypeSchemaPositiveReadError(
                "reader capability belongs to another request"
            )
        coordinate_values = _reader_coordinate_values(expected)
        if type(lookup_depth) is not int or lookup_depth < 0:
            raise TypeError("lookup_depth must be non-negative int")
        coordinate_ref = coordinate_values[6]
        retained = (
            decoded_nodes.get(coordinate_ref)
            if type(decoded_nodes) is _OperationDecodedNodeArena
            else None
        )
        if retained is not None:
            retained_signature, _, node = retained
            if retained_signature != coordinate_values:
                raise TypeSchemaPositiveReadError(
                    "retained persistent node differs from requested coordinate"
                )
            # The first demand admitted the exact coordinate, canonical bytes,
            # digest and decoded node into this operation-local arena.  A
            # subsequent semantic demand is a logical lookup, not another
            # backing read; invoking the callback again would both duplicate
            # work and let provider behavior re-enter after admission.
            return node, PositiveReadObservation(
                read_count=0,
                read_bytes=0,
                cache_hits=1,
                max_lookup_depth=lookup_depth,
                elapsed_ns=0,
            )
        result = self._callback(_coordinate_from_values(coordinate_values))
        if type(result) is not PositiveBodyRead:
            raise TypeSchemaPositiveReadError("reader returned unsupported body result")
        if (
            type(result.body_ref) is not str
            or type(result.body_digest) is not str
            or type(result.size_bytes) is not int
            or type(result.schema) is not str
            or type(result.canonical_bytes) is not bytes
            or type(result.cache_hit) is not bool
            or type(result.elapsed_ns) is not int
        ):
            raise TypeSchemaPositiveReadError(
                "reader returned foreign body envelope value"
            )
        schema, _, authority_ref, body_ref, body_digest, size_bytes, coordinate_ref, _ = (
            coordinate_values
        )
        if result.body_ref != body_ref:
            raise TypeSchemaPositiveReadError("reader body_ref substitution")
        if result.body_digest != body_digest:
            raise TypeSchemaPositiveReadError("reader body digest substitution")
        if result.size_bytes != size_bytes:
            raise TypeSchemaPositiveReadError("reader body size substitution")
        if result.schema != schema:
            raise TypeSchemaPositiveReadError("reader body schema substitution")
        if len(result.canonical_bytes) != size_bytes:
            raise TypeSchemaPositiveReadError("reader bytes do not match expected size")
        if decoded_nodes is not None and retained is None:
            retained = decoded_nodes.get(coordinate_ref)
        if retained is not None:
            retained_signature, retained_bytes, node = retained
            if (
                retained_signature != coordinate_values
                or retained_bytes != result.canonical_bytes
            ):
                raise TypeSchemaPositiveReadError(
                    "retained persistent node differs from fresh reader result"
                )
            return node, PositiveReadObservation(
                read_count=1,
                read_bytes=len(result.canonical_bytes),
                cache_hits=int(result.cache_hit),
                max_lookup_depth=lookup_depth,
                elapsed_ns=result.elapsed_ns,
            )
        actual_digest = "sha256:" + hashlib.sha256(result.canonical_bytes).hexdigest()
        if actual_digest != body_digest:
            raise TypeSchemaPositiveReadError(
                "reader bytes do not match expected digest"
            )
        try:
            node = decode_persistent_index_node(result.canonical_bytes)
        except (TypeError, TypeSchemaPersistentIndexError) as error:
            raise TypeSchemaPositiveReadError(
                f"persistent node decode failed: {error}"
            ) from error
        if node.node_ref != authority_ref:
            raise TypeSchemaPositiveReadError("persistent node ref substitution")
        if node.contract != schema:
            raise TypeSchemaPositiveReadError("persistent node schema substitution")
        if decoded_nodes is not None:
            decoded_nodes[coordinate_ref] = (
                coordinate_values,
                result.canonical_bytes,
                node,
            )
        return node, PositiveReadObservation(
            read_count=1,
            read_bytes=len(result.canonical_bytes),
            cache_hits=int(result.cache_hit),
            max_lookup_depth=lookup_depth,
            elapsed_ns=result.elapsed_ns,
        )

@dataclass(frozen=True, slots=True)
class IndexBindingMovement:
    key: str
    prior_value: PersistentBodyCoordinate | None
    next_value: PersistentBodyCoordinate | None

    def __post_init__(self) -> None:
        _ = key_digest_path(self.key)
        for value in (self.prior_value, self.next_value):
            if value is not None and not isinstance(value, PersistentBodyCoordinate):
                raise TypeError("movement values must be body coordinates or None")
        if self.prior_value == self.next_value:
            raise TypeSchemaPositiveReadError("movement must change its binding")


@dataclass(frozen=True, slots=True)
class PersistentIndexPatchResult:
    root: PersistentIndexRoot
    emitted_bodies: tuple[PersistentBodyAuthority, ...]
    reused_coordinates: tuple[PersistentBodyCoordinate, ...]
    observation: PositiveReadObservation


@dataclass(slots=True)
class _ReadState:
    capability: TypeSchemaPositiveReaderCapability
    request_ref: str
    cache: dict[str, PersistentIndexNode]
    coordinates: dict[str, PersistentBodyCoordinate]
    decoded_nodes: dict[
        str,
        tuple[
            tuple[str, str, str, str, str, int, str, str],
            bytes,
            PersistentIndexNode,
        ],
    ] | None = None
    read_count: int = 0
    read_bytes: int = 0
    cache_hits: int = 0
    max_lookup_depth: int = 0
    elapsed_ns: int = 0

    @property
    def observation(self) -> PositiveReadObservation:
        return PositiveReadObservation(
            read_count=self.read_count,
            read_bytes=self.read_bytes,
            cache_hits=self.cache_hits,
            max_lookup_depth=self.max_lookup_depth,
            elapsed_ns=self.elapsed_ns,
        )

    def add_observation(self, value: PositiveReadObservation) -> None:
        self.read_count += value.read_count
        self.read_bytes += value.read_bytes
        self.cache_hits += value.cache_hits
        self.max_lookup_depth = max(
            self.max_lookup_depth, value.max_lookup_depth
        )
        self.elapsed_ns += value.elapsed_ns

    def node(
        self,
        coordinate: PersistentBodyCoordinate,
        *,
        keyspace: str,
        depth: int,
        path: str,
    ) -> PersistentIndexNode:
        cached = self.cache.get(coordinate.coordinate_ref)
        if cached is not None:
            return cached
        node, observation = self.capability._read_index_node_exact(
            request_ref=self.request_ref,
            expected=coordinate,
            lookup_depth=depth,
            decoded_nodes=self.decoded_nodes,
        )
        self.add_observation(observation)
        if node.node_ref != coordinate.authority_ref:
            raise TypeSchemaPositiveReadError("persistent node ref substitution")
        if node.contract != coordinate.schema:
            raise TypeSchemaPositiveReadError("persistent node schema substitution")
        if node.keyspace != keyspace:
            raise TypeSchemaPositiveReadError("persistent node keyspace substitution")
        if node.depth != depth or node.path != path:
            raise TypeSchemaPositiveReadError("persistent node depth/path substitution")
        self.cache[coordinate.coordinate_ref] = node
        self.coordinates[coordinate.coordinate_ref] = coordinate
        return node


def _preflight_public_reader(
    reader: TypeSchemaPositiveReaderCapability,
    request_ref: str,
) -> None:
    if type(reader) is not TypeSchemaPositiveReaderCapability:
        raise TypeSchemaPositiveReadError(
            "reader must be exact TypeSchemaPositiveReaderCapability"
        )
    if (
        type(request_ref) is not str
        or not request_ref
        or request_ref.strip() != request_ref
    ):
        raise TypeSchemaPositiveReadError("request_ref must be normalized text")
    retained_request_ref = object.__getattribute__(reader, "_request_ref")
    if type(retained_request_ref) is not str or not retained_request_ref:
        raise TypeSchemaPositiveReadError(
            "reader request_ref must be exact normalized text"
        )
    if retained_request_ref != request_ref:
        raise TypeSchemaPositiveReadError(
            "reader capability belongs to another request"
        )


def _detach_public_operands(*values: object) -> tuple[object, ...]:
    try:
        _protected_operand_wire(values)
    except TypeSchemaPersistentIndexError as error:
        raise TypeSchemaPositiveReadError(
            f"positive-read operand admission failed: {error}"
        ) from error
    return copy.deepcopy(values)


def lookup_index_value(
    root: PersistentIndexRoot,
    *,
    key: str,
    reader: TypeSchemaPositiveReaderCapability,
    request_ref: str,
) -> tuple[PersistentBodyCoordinate | None, PositiveReadObservation]:
    _preflight_public_reader(reader, request_ref)
    admitted_values = _detach_public_operands(root, key)
    admitted_root = cast(PersistentIndexRoot, admitted_values[0])
    admitted_key = cast(str, admitted_values[1])
    with _meta_type_schema_operation(
        operation_ref="persistent-index.lookup",
        operands=(admitted_root, admitted_key),
        reader=reader,
        request_ref=request_ref,
    ) as context:
        return _lookup_index_value_with_context(
            context,
            admitted_root,
            key=admitted_key,
            reader=reader,
            request_ref=request_ref,
            decoded_nodes=None,
        )


def _lookup_index_value_with_context(
    context: _MetaTypeSchemaOperationContext,
    root: PersistentIndexRoot,
    *,
    key: str,
    reader: TypeSchemaPositiveReaderCapability,
    request_ref: str,
    decoded_nodes: dict[
        str,
        tuple[
            tuple[str, str, str, str, str, int, str, str],
            bytes,
            PersistentIndexNode,
        ],
    ]
    | None,
) -> tuple[PersistentBodyCoordinate | None, PositiveReadObservation]:
    _require_meta_type_schema_operation(context)
    state = _state(reader, request_ref, decoded_nodes=decoded_nodes)
    path = key_digest_path(key)
    coordinate: PersistentBodyCoordinate | None = root.root_node
    for depth in range(PERSISTENT_INDEX_DEPTH + 1):
        if coordinate is None:
            return None, state.observation
        node = state.node(
            coordinate,
            keyspace=root.keyspace,
            depth=depth,
            path=path[:depth],
        )
        if depth == PERSISTENT_INDEX_DEPTH:
            if node.key != key:
                raise TypeSchemaPositiveReadError("SHA-256 index key collision")
            return node.value, state.observation
        child = next(
            (item for item in node.children if item.nibble == path[depth]), None
        )
        coordinate = None if child is None else child.node
    raise AssertionError("fixed-depth lookup did not terminate")


def prove_index_membership(
    root: PersistentIndexRoot,
    *,
    key: str,
    reader: TypeSchemaPositiveReaderCapability,
    request_ref: str,
) -> tuple[
    PersistentIndexMembershipProof | None,
    tuple[PersistentIndexNode, ...],
    PositiveReadObservation,
]:
    _preflight_public_reader(reader, request_ref)
    admitted_values = _detach_public_operands(root, key)
    admitted_root = cast(PersistentIndexRoot, admitted_values[0])
    admitted_key = cast(str, admitted_values[1])
    with _meta_type_schema_operation(
        operation_ref="persistent-index.prove",
        operands=(admitted_root, admitted_key),
        reader=reader,
        request_ref=request_ref,
    ) as context:
        return _prove_index_membership(
            context,
            admitted_root,
            key=admitted_key,
            reader=reader,
            request_ref=request_ref,
        )


def _prove_index_membership(
    context: _MetaTypeSchemaOperationContext,
    root: PersistentIndexRoot,
    *,
    key: str,
    reader: TypeSchemaPositiveReaderCapability,
    request_ref: str,
) -> tuple[
    PersistentIndexMembershipProof | None,
    tuple[PersistentIndexNode, ...],
    PositiveReadObservation,
]:
    """Resolve one key and return immutable root-to-leaf membership evidence."""

    _require_meta_type_schema_operation(context)
    state = _state(reader, request_ref)
    path = key_digest_path(key)
    coordinate: PersistentBodyCoordinate | None = root.root_node
    node_refs: list[str] = []
    for depth in range(PERSISTENT_INDEX_DEPTH + 1):
        if coordinate is None:
            return (
                None,
                tuple(sorted(state.cache.values(), key=lambda value: value.node_ref)),
                state.observation,
            )
        node = state.node(
            coordinate,
            keyspace=root.keyspace,
            depth=depth,
            path=path[:depth],
        )
        node_refs.append(node.node_ref)
        if depth == PERSISTENT_INDEX_DEPTH:
            if node.key != key:
                raise TypeSchemaPositiveReadError("SHA-256 index key collision")
            if node.value is None:
                raise AssertionError("persistent leaf must contain a value")
            proof = _create_prevalidated_membership_proof(
                context,
                root=root,
                key=key,
                value=node.value,
                node_refs=tuple(node_refs),
            )
            return (
                proof,
                tuple(sorted(state.cache.values(), key=lambda value: value.node_ref)),
                state.observation,
            )
        child = next(
            (item for item in node.children if item.nibble == path[depth]), None
        )
        coordinate = None if child is None else child.node
    raise AssertionError("fixed-depth membership proof did not terminate")


def patch_persistent_index(
    prior: PersistentIndexRoot,
    *,
    movements: tuple[IndexBindingMovement, ...],
    reader: TypeSchemaPositiveReaderCapability,
    request_ref: str,
) -> PersistentIndexPatchResult:
    _preflight_public_reader(reader, request_ref)
    admitted_values = _detach_public_operands(prior, movements)
    admitted_prior = cast(PersistentIndexRoot, admitted_values[0])
    admitted_movements = cast(tuple[IndexBindingMovement, ...], admitted_values[1])
    with _meta_type_schema_operation(
        operation_ref="persistent-index.patch",
        operands=(admitted_prior, admitted_movements),
        reader=reader,
        request_ref=request_ref,
    ) as context:
        return _patch_persistent_index_with_context(
            context,
            admitted_prior,
            movements=admitted_movements,
            reader=reader,
            request_ref=request_ref,
            decoded_nodes=None,
        )


def _patch_persistent_index_with_context(
    context: _MetaTypeSchemaOperationContext,
    prior: PersistentIndexRoot,
    *,
    movements: tuple[IndexBindingMovement, ...],
    reader: TypeSchemaPositiveReaderCapability,
    request_ref: str,
    decoded_nodes: dict[
        str,
        tuple[
            tuple[str, str, str, str, str, int, str, str],
            bytes,
            PersistentIndexNode,
        ],
    ]
    | None,
) -> PersistentIndexPatchResult:
    """Patch while reusing only validated node bytes from this invocation."""

    _require_meta_type_schema_operation(context)
    if not isinstance(prior, PersistentIndexRoot):
        raise TypeError("prior must be PersistentIndexRoot")
    if type(movements) is not tuple or any(
        not isinstance(value, IndexBindingMovement) for value in movements
    ):
        raise TypeError("movements must be tuple[IndexBindingMovement, ...]")
    ordered = tuple(sorted(movements, key=lambda item: item.key))
    keys = tuple(item.key for item in ordered)
    paths = tuple(key_digest_path(key) for key in keys)
    if len(keys) != len(set(keys)):
        raise TypeSchemaPositiveReadError("movements contain duplicate key")
    if len(paths) != len(set(paths)):
        raise TypeSchemaPositiveReadError("SHA-256 index key collision")
    if not ordered:
        return PersistentIndexPatchResult(
            root=prior,
            emitted_bodies=(),
            reused_coordinates=(),
            observation=PositiveReadObservation(),
        )
    state = _state(reader, request_ref, decoded_nodes=decoded_nodes)
    emitted: dict[str, PersistentBodyAuthority] = {}
    movement_by_path = {key_digest_path(value.key): value for value in ordered}
    encoded_keyspace = _prevalidated_json(prior.keyspace)
    node_contract_bytes = PERSISTENT_INDEX_NODE_CONTRACT.encode("ascii")
    coordinate_contract_bytes = PERSISTENT_BODY_COORDINATE_CONTRACT.encode("ascii")

    def issue_node(
        *,
        depth: int,
        path: str,
        children: tuple[PersistentIndexChild, ...] = (),
        key: str | None = None,
        value: PersistentBodyCoordinate | None = None,
    ) -> tuple[PersistentIndexNode, PersistentBodyAuthority]:
        """Issue one node already proven by this fixed-depth patch walk."""

        child_coordinate_fragments = (
            state.decoded_nodes.body_fragments
            if type(state.decoded_nodes) is _OperationDecodedNodeArena and children
            else None
        )
        semantic_bytes = _prevalidated_index_node_semantic_bytes(
            keyspace=prior.keyspace,
            depth=depth,
            path=path,
            children=children,
            key=key,
            value=value,
            child_coordinate_fragments=child_coordinate_fragments,
            encoded_keyspace=encoded_keyspace,
        )
        node_ref = "sha256:" + hashlib.sha256(
            node_contract_bytes + b"\n" + semantic_bytes
        ).hexdigest()
        node = object.__new__(PersistentIndexNode)
        object.__setattr__(node, "keyspace", prior.keyspace)
        object.__setattr__(node, "depth", depth)
        object.__setattr__(node, "path", path)
        object.__setattr__(node, "children", children)
        object.__setattr__(node, "key", key)
        object.__setattr__(node, "value", value)
        object.__setattr__(node, "node_ref", node_ref)
        object.__setattr__(node, "contract", PERSISTENT_INDEX_NODE_CONTRACT)

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
        coordinate = object.__new__(PersistentBodyCoordinate)
        object.__setattr__(coordinate, "schema", PERSISTENT_INDEX_NODE_CONTRACT)
        object.__setattr__(coordinate, "ref_field", "node_ref")
        object.__setattr__(coordinate, "authority_ref", node_ref)
        object.__setattr__(
            coordinate,
            "body_ref",
            f"cas://aware-meta-type-schema/{body_digest[7:]}",
        )
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
                coordinate_contract_bytes + b"\n" + coordinate_semantic_bytes
            ).hexdigest(),
        )
        object.__setattr__(
            coordinate, "contract", PERSISTENT_BODY_COORDINATE_CONTRACT
        )
        coordinate_marker = b',"ref_field":'
        coordinate_prefix, marker, coordinate_suffix = (
            coordinate_semantic_bytes.rpartition(coordinate_marker)
        )
        if not marker:
            raise AssertionError("canonical coordinate must contain ref_field")
        coordinate_wire = (
            coordinate_prefix
            + b',"coordinate_ref":"'
            + coordinate.coordinate_ref.encode("ascii")
            + b'"'
            + marker
            + coordinate_suffix
        )
        body = object.__new__(PersistentBodyAuthority)
        object.__setattr__(body, "coordinate", coordinate)
        object.__setattr__(body, "canonical_bytes", canonical_bytes)
        if type(state.decoded_nodes) is _OperationDecodedNodeArena:
            coordinate_values = (
                coordinate.schema,
                coordinate.ref_field,
                coordinate.authority_ref,
                coordinate.body_ref,
                coordinate.body_digest,
                coordinate.size_bytes,
                coordinate.coordinate_ref,
                coordinate.contract,
            )
            state.decoded_nodes.body_fragments[coordinate.coordinate_ref] = (
                coordinate_values,
                canonical_bytes,
                coordinate_wire,
            )
            state.decoded_nodes[coordinate.coordinate_ref] = (
                coordinate_values,
                canonical_bytes,
                node,
            )
        return node, body

    def issue_child(
        nibble: str,
        coordinate: PersistentBodyCoordinate,
    ) -> PersistentIndexChild:
        """Project one child already proven by this operation's trie walk."""

        child = object.__new__(PersistentIndexChild)
        object.__setattr__(child, "nibble", nibble)
        object.__setattr__(child, "node", coordinate)
        return child

    bootstrap_additions = prior.binding_count == 0 and all(
        movement.prior_value is None and movement.next_value is not None
        for movement in ordered
    )
    if bootstrap_additions:
        empty_root = state.node(
            prior.root_node,
            keyspace=prior.keyspace,
            depth=0,
            path="",
        )
        if empty_root.children or empty_root.key is not None or empty_root.value is not None:
            raise TypeSchemaPositiveReadError(
                "empty persistent root contains bindings"
            )
        node_paths = {""}
        for movement_path in movement_by_path:
            node_paths.update(
                movement_path[:depth]
                for depth in range(1, PERSISTENT_INDEX_DEPTH + 1)
            )
        successor_by_path: dict[str, PersistentBodyCoordinate] = {}
        for node_path in sorted(
            node_paths, key=lambda item: (len(item), item), reverse=True
        ):
            depth = len(node_path)
            if depth == PERSISTENT_INDEX_DEPTH:
                movement = movement_by_path.get(node_path)
                if type(movement) is not IndexBindingMovement:
                    raise AssertionError("persistent bootstrap leaf is absent")
                successor, body = issue_node(
                    depth=depth,
                    path=node_path,
                    key=movement.key,
                    value=movement.next_value,
                )
            else:
                successor, body = issue_node(
                    depth=depth,
                    path=node_path,
                    children=tuple(
                        issue_child(
                            nibble,
                            successor_by_path[node_path + nibble],
                        )
                        for nibble in "0123456789abcdef"
                        if node_path + nibble in successor_by_path
                    ),
                )
            emitted[body.coordinate.coordinate_ref] = body
            successor_by_path[node_path] = body.coordinate
        coordinate = successor_by_path[""]
        count_delta = len(ordered)
    else:
        coordinate, count_delta = _patch_node(
            context,
            prior.root_node,
            keyspace=prior.keyspace,
            depth=0,
            path="",
            movements=movement_by_path,
            state=state,
            emitted=emitted,
            root_required=True,
            issue_node=issue_node,
            issue_child=issue_child,
        )
    if coordinate is None:
        raise AssertionError("root node must always be retained")
    binding_count = prior.binding_count + count_delta
    if binding_count < 0:
        raise TypeSchemaPositiveReadError("index binding count underflow")
    successor = _create_prevalidated_index_root(
        context,
        keyspace=prior.keyspace,
        root_node=coordinate,
        binding_count=binding_count,
    )
    reused = tuple(
        value for key, value in sorted(state.coordinates.items()) if key not in emitted
    )
    return PersistentIndexPatchResult(
        root=successor,
        emitted_bodies=tuple(emitted[key] for key in sorted(emitted)),
        reused_coordinates=reused,
        observation=state.observation,
    )


def _patch_node(
    context: _MetaTypeSchemaOperationContext,
    existing_coordinate: PersistentBodyCoordinate | None,
    *,
    keyspace: str,
    depth: int,
    path: str,
    movements: dict[str, IndexBindingMovement],
    state: _ReadState,
    emitted: dict[str, PersistentBodyAuthority],
    root_required: bool,
    issue_node: Callable[..., tuple[PersistentIndexNode, PersistentBodyAuthority]],
    issue_child: Callable[[str, PersistentBodyCoordinate], PersistentIndexChild],
) -> tuple[PersistentBodyCoordinate | None, int]:
    existing = (
        None
        if existing_coordinate is None
        else state.node(
            existing_coordinate,
            keyspace=keyspace,
            depth=depth,
            path=path,
        )
    )
    if depth == PERSISTENT_INDEX_DEPTH:
        movement = movements.get(path)
        if movement is None:
            return existing_coordinate, 0
        actual = None if existing is None else existing.value
        if actual != movement.prior_value:
            raise TypeSchemaPositiveReadError(
                f"prior binding mismatch for {movement.key!r}"
            )
        if movement.next_value is None:
            return None, -1
        successor, body = issue_node(
            depth=depth,
            path=path,
            key=movement.key,
            value=movement.next_value,
        )
        if existing is not None and successor.node_ref == existing.node_ref:
            return existing_coordinate, 0
        emitted[body.coordinate.coordinate_ref] = body
        return body.coordinate, 1 if existing is None else 0

    existing_children = (
        {}
        if existing is None
        else {item.nibble: item.node for item in existing.children}
    )
    changed = False
    count_delta = 0
    groups: dict[str, dict[str, IndexBindingMovement]] = {}
    for movement_path, movement in movements.items():
        groups.setdefault(movement_path[depth], {})[movement_path] = movement
    for nibble, group in sorted(groups.items()):
        previous = existing_children.get(nibble)
        successor, child_delta = _patch_node(
            context,
            previous,
            keyspace=keyspace,
            depth=depth + 1,
            path=path + nibble,
            movements=group,
            state=state,
            emitted=emitted,
            root_required=False,
            issue_node=issue_node,
            issue_child=issue_child,
        )
        count_delta += child_delta
        if successor != previous:
            changed = True
            if successor is None:
                existing_children.pop(nibble, None)
            else:
                existing_children[nibble] = successor
    if not changed and existing_coordinate is not None:
        return existing_coordinate, count_delta
    if not existing_children and not root_required:
        return None, count_delta
    successor, body = issue_node(
        depth=depth,
        path=path,
        children=tuple(
            issue_child(nibble, coordinate)
            for nibble, coordinate in sorted(existing_children.items())
        ),
    )
    emitted[body.coordinate.coordinate_ref] = body
    return body.coordinate, count_delta


def _state(
    reader: TypeSchemaPositiveReaderCapability,
    request_ref: str,
    *,
    decoded_nodes: dict[
        str,
        tuple[
            tuple[str, str, str, str, str, int, str, str],
            bytes,
            PersistentIndexNode,
        ],
    ]
    | None = None,
) -> _ReadState:
    if type(reader) is not TypeSchemaPositiveReaderCapability:
        raise TypeSchemaPositiveReadError(
            "reader must be exact TypeSchemaPositiveReaderCapability"
        )
    if request_ref != reader.request_ref:
        raise TypeSchemaPositiveReadError(
            "reader capability belongs to another request"
        )
    return _ReadState(reader, request_ref, {}, {}, decoded_nodes=decoded_nodes)


__all__ = [
    "PERSISTENT_INDEX_MEMBERSHIP_CONTRACT",
    "PERSISTENT_INDEX_PROOF_BUNDLE_CONTRACT",
    "IndexBindingMovement",
    "PersistentIndexMembershipProof",
    "PersistentIndexPatchResult",
    "PersistentIndexProofBundle",
    "PositiveBodyRead",
    "PositiveReadObservation",
    "TypeSchemaPositiveReadError",
    "TypeSchemaPositiveReaderCapability",
    "lookup_index_value",
    "patch_persistent_index",
    "prove_index_membership",
]
