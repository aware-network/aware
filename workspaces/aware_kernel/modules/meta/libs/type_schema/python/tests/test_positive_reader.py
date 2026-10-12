from __future__ import annotations

import hashlib

import pytest
from aware_meta_type_schema.persistent_index import (
    PersistentBodyAuthority,
    PersistentBodyCoordinate,
    PersistentIndexNode,
    PersistentIndexRoot,
    _meta_type_schema_operation,
    create_empty_persistent_index,
)
from aware_meta_type_schema.positive_reader import (
    IndexBindingMovement,
    PersistentIndexProofBundle,
    PositiveBodyRead,
    TypeSchemaPositiveReaderCapability,
    TypeSchemaPositiveReadError,
    _admit_validated_proof_bundle,
    _AdmittedPersistentIndexProofBundle,
    _advance_admitted_proof_bundle,
    _lookup_index_value_with_context,
    lookup_index_value,
    patch_persistent_index,
    prove_index_membership,
)


def _reply(body: PersistentBodyAuthority, **changes: object) -> PositiveBodyRead:
    values = {
        "body_ref": body.coordinate.body_ref,
        "body_digest": body.coordinate.body_digest,
        "size_bytes": body.coordinate.size_bytes,
        "schema": body.coordinate.schema,
        "canonical_bytes": body.canonical_bytes,
        "cache_hit": False,
        "elapsed_ns": 0,
    }
    values.update(changes)
    return PositiveBodyRead(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize("field", ("body_ref", "body_digest", "size_bytes", "schema"))
def test_positive_reader_authenticates_exact_body_envelope(field: str) -> None:
    root, values = create_empty_persistent_index("test:index")
    body = values[0]
    substitutions = {
        "body_ref": "cas://substituted/body",
        "body_digest": "sha256:" + "0" * 64,
        "size_bytes": body.coordinate.size_bytes + 1,
        "schema": "substituted.schema.v1",
    }
    reader = TypeSchemaPositiveReaderCapability(
        request_ref="request:test",
        read_body=lambda expected: _reply(body, **{field: substitutions[field]}),
    )

    with pytest.raises(TypeSchemaPositiveReadError, match="substitution"):
        lookup_index_value(
            root,
            key="absent",
            reader=reader,
            request_ref="request:test",
        )


def test_positive_reader_detaches_callback_coordinate_from_protected_expectation() -> (
    None
):
    root, values = create_empty_persistent_index("test:index")
    body = values[0]
    calls: list[str] = []
    observed: list[PersistentBodyCoordinate] = []

    class ForeignCoordinateRef(str):
        def __hash__(self) -> int:
            calls.append("foreign_coordinate_hash")
            raise RuntimeError("foreign coordinate hash executed")

    def mutating_read(expected: PersistentBodyCoordinate) -> PositiveBodyRead:
        observed.append(expected)
        object.__setattr__(
            expected,
            "coordinate_ref",
            ForeignCoordinateRef(expected.coordinate_ref),
        )
        return _reply(body)

    reader = TypeSchemaPositiveReaderCapability(
        request_ref="request:test",
        read_body=mutating_read,
    )
    value, _ = lookup_index_value(
        root,
        key="absent",
        reader=reader,
        request_ref="request:test",
    )

    assert value is None
    assert observed
    assert observed[0] is not root.root_node
    assert type(root.root_node.coordinate_ref) is str
    assert calls == []


def test_positive_reader_rejects_missing_and_noncanonical_bytes() -> None:
    root, values = create_empty_persistent_index("test:index")
    body = values[0]
    missing = TypeSchemaPositiveReaderCapability(
        request_ref="request:test",
        read_body=lambda expected: None,  # type: ignore[arg-type,return-value]
    )
    with pytest.raises(TypeSchemaPositiveReadError, match="unsupported"):
        lookup_index_value(
            root,
            key="absent",
            reader=missing,
            request_ref="request:test",
        )

    changed = b" " + body.canonical_bytes
    coordinate = PersistentBodyCoordinate.create(
        schema=body.coordinate.schema,
        ref_field=body.coordinate.ref_field,
        authority_ref=body.coordinate.authority_ref,
        size_bytes=len(changed),
        body_digest="sha256:" + hashlib.sha256(changed).hexdigest(),
    )
    forged_root = PersistentIndexRoot.create(
        keyspace=root.keyspace,
        root_node=coordinate,
        binding_count=0,
    )
    noncanonical = TypeSchemaPositiveReaderCapability(
        request_ref="request:test",
        read_body=lambda expected: PositiveBodyRead(
            coordinate.body_ref,
            coordinate.body_digest,
            coordinate.size_bytes,
            coordinate.schema,
            changed,
        ),
    )
    with pytest.raises(TypeSchemaPositiveReadError, match="canonical"):
        lookup_index_value(
            forged_root,
            key="absent",
            reader=noncanonical,
            request_ref="request:test",
        )


def test_positive_reader_validates_node_depth_and_key_path() -> None:
    child = PersistentIndexNode.create(keyspace="test:index", depth=1, path="a")
    body = child.to_body()
    forged_root = PersistentIndexRoot.create(
        keyspace="test:index",
        root_node=body.coordinate,
        binding_count=0,
    )
    reader = TypeSchemaPositiveReaderCapability(
        request_ref="request:test",
        read_body=lambda expected: _reply(body),
    )

    with pytest.raises(TypeSchemaPositiveReadError, match="depth/path"):
        lookup_index_value(
            forged_root,
            key="absent",
            reader=reader,
            request_ref="request:test",
        )


def test_reader_capability_rejects_mapping_subclass_and_cross_request() -> None:
    root, values = create_empty_persistent_index("test:index")
    body = values[0]
    reader = TypeSchemaPositiveReaderCapability(
        request_ref="request:test",
        read_body=lambda expected: _reply(body),
    )
    with pytest.raises(TypeSchemaPositiveReadError, match="another request"):
        lookup_index_value(
            root,
            key="absent",
            reader=reader,
            request_ref="request:foreign",
        )
    with pytest.raises(TypeSchemaPositiveReadError, match="exact"):
        lookup_index_value(
            root,
            key="absent",
            reader={},  # type: ignore[arg-type]
            request_ref="request:test",
        )

    class MutatingReader(TypeSchemaPositiveReaderCapability):
        def write(self) -> None:
            raise AssertionError

    mutating = MutatingReader(
        request_ref="request:test",
        read_body=lambda expected: _reply(body),
    )
    with pytest.raises(TypeSchemaPositiveReadError, match="exact"):
        lookup_index_value(
            root,
            key="absent",
            reader=mutating,
            request_ref="request:test",
        )


def test_observation_variation_cannot_change_root_or_lookup_value() -> None:
    root, values = create_empty_persistent_index("test:index")
    body = values[0]
    cold = TypeSchemaPositiveReaderCapability(
        request_ref="request:test",
        read_body=lambda expected: _reply(body, elapsed_ns=100),
    )
    warm = TypeSchemaPositiveReaderCapability(
        request_ref="request:test",
        read_body=lambda expected: _reply(body, cache_hit=True, elapsed_ns=1),
    )

    cold_value, cold_observation = lookup_index_value(
        root,
        key="absent",
        reader=cold,
        request_ref="request:test",
    )
    warm_value, warm_observation = lookup_index_value(
        root,
        key="absent",
        reader=warm,
        request_ref="request:test",
    )
    assert cold_value == warm_value is None
    assert cold_observation != warm_observation
    assert root.root_ref == root.root_ref


def test_call_local_decoded_node_reuse_requires_exact_fresh_bytes() -> None:
    root, values = create_empty_persistent_index("test:index")
    body = values[0]
    calls = 0

    def read(expected):
        nonlocal calls
        calls += 1
        return _reply(body)

    reader = TypeSchemaPositiveReaderCapability(
        request_ref="request:test",
        read_body=read,
    )
    decoded_nodes = {}
    with _meta_type_schema_operation(
        operation_ref="persistent-index.lookup",
        operands=(root, "absent"),
        reader=reader,
        request_ref="request:test",
    ) as context:
        first, first_observation = _lookup_index_value_with_context(
            context,
            root,
            key="absent",
            reader=reader,
            request_ref="request:test",
            decoded_nodes=decoded_nodes,
        )
        second, second_observation = _lookup_index_value_with_context(
            context,
            root,
            key="absent",
            reader=reader,
            request_ref="request:test",
            decoded_nodes=decoded_nodes,
        )
        assert first is second is None
        assert calls == 2
        assert first_observation.read_count == second_observation.read_count == 1

        signature, retained_bytes, node = decoded_nodes[root.root_node.coordinate_ref]
        decoded_nodes[root.root_node.coordinate_ref] = (
            signature,
            retained_bytes + b" ",
            node,
        )
        with pytest.raises(
            TypeSchemaPositiveReadError, match="retained persistent node"
        ):
            _lookup_index_value_with_context(
                context,
                root,
                key="absent",
                reader=reader,
                request_ref="request:test",
                decoded_nodes=decoded_nodes,
            )


def test_selective_proof_issuance_requires_exact_admission() -> None:
    root, bodies = create_empty_persistent_index("test:index")
    store = {value.coordinate.body_ref: value for value in bodies}

    def read(expected):
        return _reply(store[expected.body_ref])

    reader = TypeSchemaPositiveReaderCapability(
        request_ref="request:test",
        read_body=read,
    )
    value_a = bodies[0].coordinate
    value_b = bodies[-1].coordinate
    patched = patch_persistent_index(
        root,
        movements=(
            IndexBindingMovement("a", None, value_a),
            IndexBindingMovement("b", None, value_b),
        ),
        reader=reader,
        request_ref="request:test",
    )
    store.update((value.coordinate.body_ref, value) for value in patched.emitted_bodies)
    proof_a, nodes_a, _ = prove_index_membership(
        patched.root,
        key="a",
        reader=reader,
        request_ref="request:test",
    )
    proof_b, nodes_b, _ = prove_index_membership(
        patched.root,
        key="b",
        reader=reader,
        request_ref="request:test",
    )
    assert proof_a is not None and proof_b is not None
    complete = PersistentIndexProofBundle.create(
        memberships=(proof_a, proof_b),
        nodes=(*nodes_a, *nodes_b),
    )
    admission = _admit_validated_proof_bundle(complete)
    proof_operands = (
        admission,
        (proof_a.membership_ref,),
        (proof_b,),
        nodes_b,
    )
    with _meta_type_schema_operation(
        operation_ref="positive-reader.advance-proof-bundle",
        operands=proof_operands,
        reader=reader,
        request_ref="request:test",
    ) as context:
        advanced = _advance_admitted_proof_bundle(
            context,
            admission,
            retained_membership_refs=(proof_a.membership_ref,),
            fresh_memberships=(proof_b,),
            fresh_nodes=nodes_b,
        )
    assert advanced.to_wire() == complete.to_wire()

    poisoned = object.__new__(PersistentIndexProofBundle)
    object.__setattr__(poisoned, "memberships", complete.memberships)
    object.__setattr__(poisoned, "nodes", complete.nodes)
    object.__setattr__(poisoned, "bundle_ref", "sha256:" + "9" * 64)
    object.__setattr__(poisoned, "contract", complete.contract)
    with pytest.raises(TypeSchemaPositiveReadError, match="strict"):
        _admit_validated_proof_bundle(poisoned)

    with _meta_type_schema_operation(
        operation_ref="positive-reader.advance-proof-bundle",
        operands=(
            _AdmittedPersistentIndexProofBundle(),
            (proof_a.membership_ref,),
            (proof_b,),
            nodes_b,
        ),
        reader=reader,
        request_ref="request:test",
    ) as context, pytest.raises(
        TypeSchemaPositiveReadError, match="not active"
    ):
        _advance_admitted_proof_bundle(
            context,
            _AdmittedPersistentIndexProofBundle(),
            retained_membership_refs=(proof_a.membership_ref,),
            fresh_memberships=(proof_b,),
            fresh_nodes=nodes_b,
        )
