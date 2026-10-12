from __future__ import annotations

import multiprocessing
import threading
from dataclasses import replace
from typing import cast

import pytest
from aware_meta_type_schema.composition import TypeOwnerBinding
from aware_meta_type_schema.encoding import digest_payload
from aware_meta_type_schema.persistent_index import (
    PERSISTENT_INDEX_DEPTH,
    PersistentBodyAuthority,
    PersistentBodyCoordinate,
    PersistentIndexNode,
    PersistentIndexRoot,
    TypeSchemaPersistentIndexError,
    _create_prevalidated_body_authority,
    _create_prevalidated_index_node_body,
    _create_prevalidated_index_root,
    _meta_type_schema_operation,
    _MetaTypeSchemaOperationContext,
    create_empty_persistent_index,
    decode_persistent_index_node,
    persistent_body_coordinate_from_wire,
)
from aware_meta_type_schema.positive_reader import (
    IndexBindingMovement,
    PositiveBodyRead,
    TypeSchemaPositiveReaderCapability,
    TypeSchemaPositiveReadError,
    lookup_index_value,
    patch_persistent_index,
)


def _value(name: str) -> PersistentBodyAuthority:
    return TypeOwnerBinding.create(
        type_ref=f"test.{name}", package_ref="package:test@1.0.0"
    ).to_body()


def _restamped_coordinate(
    coordinate: PersistentBodyCoordinate, **changes: object
) -> PersistentBodyCoordinate:
    semantic = coordinate.semantic_wire()
    semantic.update(changes)
    return PersistentBodyCoordinate(
        schema=str(semantic["schema"]),
        ref_field=str(semantic["ref_field"]),
        authority_ref=str(semantic["authority_ref"]),
        body_ref=str(semantic["body_ref"]),
        body_digest=str(semantic["body_digest"]),
        size_bytes=cast(int, semantic["size_bytes"]),
        coordinate_ref=digest_payload(
            coordinate.contract,
            semantic,
        ),
    )


def _reader(
    bodies: dict[str, PersistentBodyAuthority],
    *,
    request_ref: str = "request:test",
    cache_hit: bool = False,
    elapsed_ns: int = 0,
) -> TypeSchemaPositiveReaderCapability:
    def read_body(expected):
        body = bodies[expected.body_ref]
        return PositiveBodyRead(
            body_ref=body.coordinate.body_ref,
            body_digest=body.coordinate.body_digest,
            size_bytes=body.coordinate.size_bytes,
            schema=body.coordinate.schema,
            canonical_bytes=body.canonical_bytes,
            cache_hit=cache_hit,
            elapsed_ns=elapsed_ns,
        )

    return TypeSchemaPositiveReaderCapability(
        request_ref=request_ref,
        read_body=read_body,
    )


def _ingest(
    bodies: dict[str, PersistentBodyAuthority],
    values: tuple[PersistentBodyAuthority, ...],
) -> None:
    bodies.update((value.coordinate.body_ref, value) for value in values)


def test_private_prevalidated_node_and_root_are_byte_exact_public_values() -> None:
    public_node = PersistentIndexNode.create(
        keyspace="proof",
        depth=0,
        path="",
        children=(),
    )
    public_body = public_node.to_body()
    public_root = PersistentIndexRoot.create(
        keyspace="proof",
        root_node=public_body.coordinate,
        binding_count=0,
    )
    owner = TypeOwnerBinding.create(
        type_ref="proof.Owner",
        package_ref="package:proof@1.0.0",
    )
    public_owner_body = owner.to_body()
    reader = _reader({public_body.coordinate.body_ref: public_body})
    with _meta_type_schema_operation(
        operation_ref="persistent-index.patch",
        operands=(public_root, ()),
        reader=reader,
        request_ref="request:test",
    ) as context:
        private_node, private_body = _create_prevalidated_index_node_body(
            context,
            keyspace="proof",
            depth=0,
            path="",
            children=(),
        )
        private_root = _create_prevalidated_index_root(
            context,
            keyspace="proof",
            root_node=private_body.coordinate,
            binding_count=0,
        )
        private_owner_body = _create_prevalidated_body_authority(
            context,
            schema=owner.contract,
            ref_field="owner_ref",
            authority_ref=owner.owner_ref,
            wire=owner.to_wire(),
        )
    assert private_node == public_node
    assert private_body == public_body
    assert private_body.canonical_bytes == public_body.canonical_bytes
    assert private_root == public_root
    assert private_root.to_wire() == public_root.to_wire()
    assert private_owner_body == public_owner_body
    assert private_owner_body.canonical_bytes == public_owner_body.canonical_bytes


def _try_inherited_private_context(
    context: _MetaTypeSchemaOperationContext,
    result_queue: multiprocessing.Queue,
) -> None:
    try:
        _create_prevalidated_index_node_body(
            context,
            keyspace="proof",
            depth=0,
            path="",
        )
    except TypeSchemaPersistentIndexError:
        result_queue.put("rejected")
    else:
        result_queue.put("accepted")


def test_private_prevalidated_helpers_require_live_call_context() -> None:
    with pytest.raises(TypeError):
        _create_prevalidated_index_node_body(  # type: ignore[call-arg]
            keyspace="",
            depth=-1,
            path="bad",
        )
    forged = object.__new__(_MetaTypeSchemaOperationContext)
    with pytest.raises(TypeSchemaPersistentIndexError, match="uninitialized"):
        _create_prevalidated_index_node_body(
            forged,
            keyspace="proof",
            depth=0,
            path="",
        )

    root, bodies = create_empty_persistent_index("proof")
    reader = _reader({body.coordinate.body_ref: body for body in bodies})
    operation = {
        "operation_ref": "persistent-index.patch",
        "operands": (root, ()),
        "reader": reader,
        "request_ref": "request:test",
    }
    thread_results: list[str] = []
    with _meta_type_schema_operation(**operation) as context:
        with _meta_type_schema_operation(**operation), pytest.raises(
            TypeSchemaPersistentIndexError, match="out of scope"
        ):
            _create_prevalidated_index_node_body(
                context,
                keyspace="proof",
                depth=0,
                path="",
            )
        _create_prevalidated_index_node_body(
            context,
            keyspace="proof",
            depth=0,
            path="",
        )
        thread = threading.Thread(
            target=lambda: thread_results.append(
                "accepted"
                if _private_context_accepted(context)
                else "rejected"
            )
        )
        thread.start()
        thread.join()
        assert thread_results == ["rejected"]

        fork = multiprocessing.get_context("fork")
        queue = fork.Queue()
        process = fork.Process(
            target=_try_inherited_private_context,
            args=(context, queue),
        )
        process.start()
        process.join(timeout=5)
        assert process.exitcode == 0
        assert queue.get(timeout=1) == "rejected"

        with pytest.raises(TypeSchemaPersistentIndexError):
            _create_prevalidated_index_node_body(
                context,
                keyspace="",
                depth=-1,
                path="bad",
            )

    with pytest.raises(TypeSchemaPersistentIndexError, match="inactive"):
        _create_prevalidated_index_node_body(
            context,
            keyspace="proof",
            depth=0,
            path="",
        )
    with _meta_type_schema_operation(**operation), pytest.raises(
        TypeSchemaPersistentIndexError, match="inactive"
    ):
        _create_prevalidated_index_node_body(
            context,
            keyspace="proof",
            depth=0,
            path="",
        )


def _private_context_accepted(
    context: _MetaTypeSchemaOperationContext,
) -> bool:
    try:
        _create_prevalidated_index_node_body(
            context,
            keyspace="proof",
            depth=0,
            path="",
        )
    except TypeSchemaPersistentIndexError:
        return False
    return True


def test_empty_insert_lookup_update_delete_is_fixed_depth_and_zero_write() -> None:
    root, genesis = create_empty_persistent_index("test:index")
    bodies = {value.coordinate.body_ref: value for value in genesis}
    first = _value("first")
    second = _value("second")
    original_store_size = len(bodies)

    inserted = patch_persistent_index(
        root,
        movements=(IndexBindingMovement("key:a", None, first.coordinate),),
        reader=_reader(bodies),
        request_ref="request:test",
    )

    assert len(bodies) == original_store_size
    assert inserted.root.binding_count == 1
    assert len(inserted.emitted_bodies) == PERSISTENT_INDEX_DEPTH + 1
    assert inserted.observation.enumeration_attempts == 0
    _ingest(bodies, inserted.emitted_bodies)
    found, observation = lookup_index_value(
        inserted.root,
        key="key:a",
        reader=_reader(bodies),
        request_ref="request:test",
    )
    assert found == first.coordinate
    assert observation.read_count == PERSISTENT_INDEX_DEPTH + 1
    assert observation.max_lookup_depth == PERSISTENT_INDEX_DEPTH

    updated = patch_persistent_index(
        inserted.root,
        movements=(IndexBindingMovement("key:a", first.coordinate, second.coordinate),),
        reader=_reader(bodies),
        request_ref="request:test",
    )
    assert updated.root.binding_count == 1
    assert updated.root.root_ref != inserted.root.root_ref
    _ingest(bodies, updated.emitted_bodies)
    deleted = patch_persistent_index(
        updated.root,
        movements=(IndexBindingMovement("key:a", second.coordinate, None),),
        reader=_reader(bodies),
        request_ref="request:test",
    )
    assert deleted.root.binding_count == 0


def test_reordered_movements_produce_identical_root_and_body_coordinates() -> None:
    root, genesis = create_empty_persistent_index("test:index")
    bodies = {value.coordinate.body_ref: value for value in genesis}
    first = _value("first")
    second = _value("second")
    movements = (
        IndexBindingMovement("key:a", None, first.coordinate),
        IndexBindingMovement("key:b", None, second.coordinate),
    )

    forward = patch_persistent_index(
        root,
        movements=movements,
        reader=_reader(bodies),
        request_ref="request:test",
    )
    reverse = patch_persistent_index(
        root,
        movements=tuple(reversed(movements)),
        reader=_reader(bodies),
        request_ref="request:test",
    )

    assert forward.root == reverse.root
    assert tuple(value.coordinate for value in forward.emitted_bodies) == tuple(
        value.coordinate for value in reverse.emitted_bodies
    )


def test_empty_patch_is_exact_current_with_zero_reads_and_bodies() -> None:
    root, _ = create_empty_persistent_index("test:index")
    result = patch_persistent_index(
        root,
        movements=(),
        reader=_reader({}),
        request_ref="request:test",
    )
    assert result.root == root
    assert result.emitted_bodies == ()
    assert result.observation.read_count == 0


def test_node_and_body_authorities_reject_substitution() -> None:
    root, bodies = create_empty_persistent_index("test:index")
    body = bodies[0]
    node = decode_persistent_index_node(body.canonical_bytes)
    assert node.depth == 0
    with pytest.raises(TypeSchemaPersistentIndexError, match="node_ref"):
        _ = replace(node, node_ref="sha256:" + "0" * 64)
    with pytest.raises(TypeSchemaPersistentIndexError, match="digest"):
        _ = PersistentBodyAuthority(
            PersistentBodyCoordinate.create(
                schema=root.root_node.schema,
                ref_field=root.root_node.ref_field,
                authority_ref=root.root_node.authority_ref,
                body_digest="sha256:" + "0" * 64,
                size_bytes=root.root_node.size_bytes,
            ),
            body.canonical_bytes,
        )


def test_body_coordinate_rejects_coherently_restamped_noncanonical_roles() -> None:
    value = _value("canonical")
    coordinate = value.coordinate

    with pytest.raises(
        TypeSchemaPersistentIndexError, match="body_ref is not canonical"
    ):
        _restamped_coordinate(coordinate, body_ref="file:///tmp/not-cas-authority.json")
    with pytest.raises(TypeSchemaPersistentIndexError, match="schema/ref-field role"):
        _restamped_coordinate(coordinate, ref_field="fragment_ref")
    with pytest.raises(TypeSchemaPersistentIndexError, match="schema/ref-field role"):
        _restamped_coordinate(coordinate, schema="test.value.v1")
    with pytest.raises(TypeSchemaPersistentIndexError, match="SHA-256 digest"):
        _restamped_coordinate(
            coordinate,
            body_digest="sha256:" + coordinate.body_digest[7:].upper(),
            body_ref=(
                "cas://aware-meta-type-schema/" + coordinate.body_digest[7:].upper()
            ),
        )

    wire = coordinate.to_wire()
    wire["body_ref"] = "file:///tmp/not-cas-authority.json"
    semantic = {key: value for key, value in wire.items() if key != "coordinate_ref"}
    wire["coordinate_ref"] = digest_payload(coordinate.contract, semantic)
    with pytest.raises(
        TypeSchemaPersistentIndexError, match="body_ref is not canonical"
    ):
        persistent_body_coordinate_from_wire(wire)


def test_prior_binding_and_reader_request_fail_closed() -> None:
    root, genesis = create_empty_persistent_index("test:index")
    bodies = {value.coordinate.body_ref: value for value in genesis}
    value = _value("value")
    with pytest.raises(TypeSchemaPositiveReadError, match="prior binding"):
        patch_persistent_index(
            root,
            movements=(IndexBindingMovement("missing", value.coordinate, None),),
            reader=_reader(bodies),
            request_ref="request:test",
        )
    with pytest.raises(TypeSchemaPositiveReadError, match="another request"):
        lookup_index_value(
            root,
            key="missing",
            reader=_reader(bodies),
            request_ref="request:foreign",
        )


def test_index_node_requires_immutable_sorted_children() -> None:
    root, bodies = create_empty_persistent_index("test:index")
    node = decode_persistent_index_node(bodies[0].canonical_bytes)
    with pytest.raises(TypeSchemaPersistentIndexError, match="immutable tuple"):
        _ = PersistentIndexNode(
            node.keyspace,
            node.depth,
            node.path,
            [],  # type: ignore[arg-type]
            node.key,
            node.value,
            node.node_ref,
        )
    assert root.binding_count == 0
