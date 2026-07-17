from __future__ import annotations

import json
import os
from pathlib import Path
from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_history_ontology.commit.commit import Commit
from aware_history_ontology.commit.commit_parent import CommitParent
from aware_history_ontology.commit.commit_enums import CommitStatus
from aware_history_ontology.stable_ids import stable_commit_parent_id
from aware_meta.class_.instance.builder import build_class_instance
from aware_meta.graph.instance.builder import (
    build_object_instance_graph_from_class_instances,
)
from aware_meta.graph.instance.commit.body_codec import build_oig_commit_body
from aware_meta.graph.instance.commit.contract import (
    LaneHeadCommitReceipt,
    ObjectInstanceGraphCommitBodyRecord,
)
from aware_meta.graph.instance.commit import (
    fs_commit_store as fs_commit_store_module,
    fs_snapshot_store as fs_snapshot_store_module,
)
from aware_meta.graph.instance.commit.fs_commit_store import (
    FSCommitStore,
    OigCommitRecordUnavailableError,
)
from aware_meta.graph.instance.commit.fs_runtime_state import (
    _SESSION_JSON_FILE_CACHE,
    _clear_fs_store_session_read_cache_for_tests,
    _snapshot_fs_store_session_read_cache_metrics,
)
from aware_meta.graph.instance.commit.fs_snapshot_store import FSSnapshotStore
from aware_meta.graph.instance.commit.perf_trace import (
    CommitPerfTraceRecorder,
    active_commit_perf_trace,
)
from aware_meta.graph.instance.commit.snapshot_state_rows import (
    _snapshot_state_rows_payload_hash,
    _snapshot_state_rows_payload_write,
)
from aware_meta.graph.instance.commit.state_snapshot_segments import (
    ObjectInstanceGraphSnapshotStateRawClassSegment,
)
from aware_meta.graph.instance.commit.state_index import (
    build_commit_state_index,
    compute_commit_state_rows_hash,
)
from aware_meta.graph.instance.commit.state_witness import (
    build_commit_state_witness_cursor,
    build_commit_state_witness_ref,
    replace_commit_state_witness_cursor_chunk_segments,
    replace_existing_commit_state_witness_cursor_segments,
    replace_existing_commit_state_witness_cursor_summary_chunks,
    replace_existing_commit_state_witness_ref_segments,
)
from aware_meta.graph.instance.commit.stored_commit_records import (
    object_instance_graph_commit_envelope_from_commit,
)
from aware_meta.test_support import (
    make_attribute_config,
    make_class_attribute_edge,
    make_class_config,
    test_class_fqn,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as Kind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_enums import (
    ObjectProjectionGraphNodeSelection,
)
from aware_meta_ontology.graph.projection.object_projection_graph_node import (
    ObjectProjectionGraphNode,
)
from aware_meta_ontology.stable_ids import stable_object_instance_graph_commit_id
from aware_orm.models.base_model import BaseORMModel


def test_commit_store_requires_explicit_root_or_aware_root_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AWARE_ROOT", raising=False)

    with pytest.raises(
        RuntimeError,
        match="FSCommitStore requires explicit root_dir or AWARE_ROOT",
    ):
        FSCommitStore()


@pytest.mark.asyncio
async def test_lineage_records_raise_typed_unavailable_error(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = FSCommitStore(root_dir=tmp_path)
    branch_id = uuid4()
    commit_id = uuid4()
    projection_hash = "ObjectInstanceGraphIdentity"

    async def _missing_record(**_: object):
        return None

    async def _missing_domain_commit(**_: object):
        return None

    monkeypatch.setattr(store, "get_commit_record", _missing_record)
    monkeypatch.setattr(
        store,
        "domain_commit_id_for_object_instance_graph_commit_id",
        _missing_domain_commit,
    )

    with pytest.raises(OigCommitRecordUnavailableError) as exc_info:
        async for _ in store.iter_lineage_forward_records(
            branch_id=branch_id,
            projection_hash=projection_hash,
            head_commit_id=commit_id,
            stop_at_commit_id=None,
        ):
            pass

    error = exc_info.value
    assert error.branch_id == branch_id
    assert error.projection_hash == projection_hash
    assert error.commit_id == commit_id
    assert error.lookup_commit_id == commit_id
    assert str(error) == (
        f"Missing commit record for {commit_id} in lane "
        f"({branch_id}, {projection_hash}); resolved_lookup_commit_id={commit_id}"
    )


def test_snapshot_store_requires_explicit_root_or_aware_root_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AWARE_ROOT", raising=False)

    with pytest.raises(
        RuntimeError,
        match="FSCommitStore requires explicit root_dir or AWARE_ROOT",
    ):
        FSSnapshotStore()


def test_commit_store_uses_aware_root_env(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWARE_ROOT", str(tmp_path))

    assert FSCommitStore().aware_root == tmp_path.resolve()
    assert FSSnapshotStore().aware_root == tmp_path.resolve()


def _metadata_int(metadata: dict[str, object], key: str) -> int:
    value = metadata[key]
    assert isinstance(value, int)
    return value


def test_snapshot_store_selects_cursor_chunks_by_exact_segment_key() -> None:
    payload = {
        "state_witness_cursor_chunks": [
            {
                "index": 24,
                "segment_keys": [
                    "class:fcbf7c7e-bca0-50d1-b1bd-bdf15119475f",
                    "class:2b9cf1ba-65d6-5848-98d8-db20956827d4",
                    "class:07f64e29-0859-5669-8af7-8b9b9c3b6ce0",
                ],
            },
            {
                "index": 77,
                "segment_keys": [
                    "class:2b514b4d-5f5b-5a4f-8138-7ce99866fb9c",
                    "class:35197666-f064-5cd0-992f-f98ac0f57374",
                ],
            },
        ],
    }

    selected = (
        FSSnapshotStore._state_witness_cursor_selected_chunk_indexes_from_index_payload(
            payload=payload,
            selected_segment_keys={"class:2b9cf1ba-65d6-5848-98d8-db20956827d4"},
        )
    )

    assert selected == {24}


@pytest.mark.asyncio
async def test_snapshot_store_writes_validated_state_row_sidecar(
    tmp_path: Path,
) -> None:
    branch_id = uuid4()
    projection_hash = "state-row-sidecar"
    commit_id = uuid4()
    graph = _make_snapshot_state_row_graph()
    store = FSSnapshotStore(root_dir=tmp_path)

    await store.put(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        oig=graph,
        indexes={},
    )

    rows = await store.get_snapshot_state_rows(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        expected_object_instance_graph_id=graph.id,
        expected_graph_hash=str(graph.hash),
    )
    evidence = await store.get_snapshot_state_index_evidence(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        expected_object_instance_graph_id=graph.id,
        expected_graph_hash=str(graph.hash),
    )
    sidecar_graph = await store.get_snapshot_state_graph(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        expected_object_instance_graph_id=graph.id,
        expected_graph_hash=str(graph.hash),
    )
    sidecar_selection = await store.get_snapshot_state_selection(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        class_instance_ids=(graph.class_instances[0].id,),
        expected_object_instance_graph_id=graph.id,
        expected_graph_hash=str(graph.hash),
    )

    assert rows is not None
    assert evidence is not None
    assert evidence.payload == rows
    assert evidence.graph_hash == graph.hash
    assert evidence.state_index.compute_hash() == graph.hash
    source_object_id = graph.class_instances[0].source_object_id
    selected = evidence.select_class_instances_by_source_object_id(
        source_object_ids=frozenset({source_object_id}),
    )
    assert selected is not None
    assert selected[source_object_id].id == graph.class_instances[0].id
    assert rows["schema"] == "aware.oig.snapshot_state_rows.v2"
    assert rows["payload_hash_algorithm"] == "sha256"
    assert rows["payload_sha256"]
    assert rows["object_instance_graph_id"] == str(graph.id)
    assert rows["graph_hash"] == graph.hash
    assert rows["node_count"] == 1
    assert rows["attribute_count"] == 1
    assert rows["edge_count"] == 0
    assert sidecar_graph is not None
    assert sidecar_graph[0].id == graph.id
    assert sidecar_graph[0].hash == graph.hash
    assert len(sidecar_graph[0].class_instances) == 1
    assert sidecar_graph[0].class_instances[0].source_object_id == (
        graph.class_instances[0].source_object_id
    )
    assert sidecar_selection is not None
    assert sidecar_selection.state_rows
    assert set(sidecar_selection.class_instances_by_id) == {
        graph.class_instances[0].id,
    }

    sidecar_path = (
        tmp_path
        / ".aware"
        / "oig"
        / str(branch_id)
        / projection_hash
        / "indexes"
        / "snapshot_state_rows"
        / f"{commit_id}.json"
    )
    payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
    corrupted_payload = dict(payload)
    corrupted_payload["class_instances"] = [
        dict(payload["class_instances"][0], source_object_id=str(uuid4()))
    ]
    sidecar_path.write_text(json.dumps(corrupted_payload), encoding="utf-8")
    _clear_fs_store_session_read_cache_for_tests()

    assert (
        await store.get_snapshot_state_selection(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            class_instance_ids=(graph.class_instances[0].id,),
            expected_object_instance_graph_id=graph.id,
            expected_graph_hash=str(graph.hash),
        )
        is None
    )

    sidecar_path.write_text(json.dumps(payload), encoding="utf-8")
    _clear_fs_store_session_read_cache_for_tests()

    state_row_lines = str(payload["state_rows_text"]).splitlines()
    raw_kind, raw_key, _raw_value = state_row_lines[0].split("\t")
    state_row_lines[0] = "\t".join((raw_kind, raw_key, str(uuid4())))
    payload["state_rows_text"] = "\n".join(state_row_lines) + "\n"
    sidecar_path.write_text(json.dumps(payload), encoding="utf-8")
    _clear_fs_store_session_read_cache_for_tests()

    assert (
        await store.get_snapshot_state_rows(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            expected_object_instance_graph_id=graph.id,
            expected_graph_hash=str(graph.hash),
        )
        is None
    )


@pytest.mark.asyncio
async def test_snapshot_store_writes_validated_state_only_snapshot(
    tmp_path: Path,
) -> None:
    branch_id = uuid4()
    projection_hash = "state-only-sidecar"
    commit_id = uuid4()
    graph = _make_snapshot_state_row_graph()
    store = FSSnapshotStore(root_dir=tmp_path)

    await store.put_state_snapshot(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        oig=graph,
    )

    assert not store.has_snapshot(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
    )
    rows = await store.get_snapshot_state_rows(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        expected_object_instance_graph_id=graph.id,
        expected_graph_hash=str(graph.hash),
    )
    sidecar_graph = await store.get_snapshot_state_graph(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        expected_object_instance_graph_id=graph.id,
        expected_graph_hash=str(graph.hash),
    )

    assert rows is not None
    assert rows["payload_sha256"]
    assert "snapshot_file_size" not in rows
    assert sidecar_graph is not None
    assert sidecar_graph[0].id == graph.id
    assert sidecar_graph[0].hash == graph.hash


@pytest.mark.asyncio
async def test_snapshot_store_writes_validated_state_rows_from_parts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch_id = uuid4()
    projection_hash = "state-row-parts-sidecar"
    commit_id = uuid4()
    graph = _make_snapshot_state_row_graph()
    state_index = build_commit_state_index(graph)
    store = FSSnapshotStore(root_dir=tmp_path)

    def _unexpected_fsync(_fd: int) -> None:
        raise AssertionError(
            "state-row sidecar writes are rebuildable and must not fsync"
        )

    monkeypatch.setattr(os, "fsync", _unexpected_fsync)

    payload = await store.put_state_snapshot_rows(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        object_instance_graph_id=graph.id,
        graph_hash=str(graph.hash),
        graph_meta={
            "id": graph.id,
            "key": graph.key,
            "name": graph.name,
            "description": graph.description,
            "object_projection_graph_id": graph.object_projection_graph_id,
            "root_class_instance_id": graph.root_class_instance_id,
            "root_source_object_id": graph.root_class_instance.source_object_id,
            "hash": graph.hash,
        },
        class_instances=tuple(graph.class_instances),
        class_instance_relationships=tuple(graph.class_instance_relationships),
        state_index=state_index,
    )

    rows = await store.get_snapshot_state_rows(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        expected_object_instance_graph_id=graph.id,
        expected_graph_hash=str(graph.hash),
    )
    sidecar_graph = await store.get_snapshot_state_graph(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        expected_object_instance_graph_id=graph.id,
        expected_graph_hash=str(graph.hash),
    )
    sidecar_selection = await store.get_snapshot_state_selection(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        class_instance_ids=(graph.class_instances[0].id,),
        expected_object_instance_graph_id=graph.id,
        expected_graph_hash=str(graph.hash),
    )

    assert not store.has_snapshot(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
    )
    assert payload["state_hash"] == state_index.compute_hash()
    assert isinstance(payload["state_rows_text"], str)
    assert payload["state_rows_text"].count("\n") == len(state_index.rows)
    assert "state_rows" not in payload
    class_instance_payloads = payload["class_instances"]
    assert isinstance(class_instance_payloads, list)
    class_instance_payload = cast(dict[str, object], class_instance_payloads[0])
    attribute_link_payloads = class_instance_payload["class_instance_attributes"]
    assert isinstance(attribute_link_payloads, list)
    attribute_link_payload = cast(dict[str, object], attribute_link_payloads[0])
    attribute_payload = cast(dict[str, object], attribute_link_payload["attribute"])
    assert "class_config" not in class_instance_payload
    assert "class_instance_changes" not in class_instance_payload
    assert "class_instance" not in attribute_link_payload
    assert "attribute_config" not in attribute_payload
    assert "attribute_changes" not in attribute_payload
    value_root_payload = cast(dict[str, object], attribute_payload["value_root"])
    type_descriptor_payload = cast(
        dict[str, object],
        value_root_payload["type_descriptor"],
    )
    assert type_descriptor_payload["kind"]
    assert "class_config" not in type_descriptor_payload
    assert "enum_config" not in type_descriptor_payload
    assert "primitive_config" not in type_descriptor_payload
    assert rows is not None
    assert rows["payload_sha256"]
    assert "snapshot_file_size" not in rows
    assert sidecar_graph is not None
    assert sidecar_graph[0].id == graph.id
    assert sidecar_graph[0].hash == graph.hash
    assert sidecar_selection is not None
    assert set(sidecar_selection.class_instances_by_id) == {
        graph.class_instances[0].id,
    }

    reused_commit_id = uuid4()
    reused_class_payload = cast(dict[str, object], class_instance_payloads[0])
    reused_payload = await store.put_state_snapshot_rows_from_payloads(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=reused_commit_id,
        object_instance_graph_id=graph.id,
        graph_hash=str(graph.hash),
        graph_meta={
            "id": graph.id,
            "key": graph.key,
            "name": graph.name,
            "description": graph.description,
            "object_projection_graph_id": graph.object_projection_graph_id,
            "root_class_instance_id": graph.root_class_instance_id,
            "root_source_object_id": graph.root_class_instance.source_object_id,
            "hash": graph.hash,
        },
        class_instance_payloads=(reused_class_payload,),
        class_instances=(),
        class_instance_relationships=tuple(graph.class_instance_relationships),
        state_index=state_index,
    )
    reused_rows = await store.get_snapshot_state_rows(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=reused_commit_id,
        expected_object_instance_graph_id=graph.id,
        expected_graph_hash=str(graph.hash),
    )
    reused_selection = await store.get_snapshot_state_selection(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=reused_commit_id,
        class_instance_ids=(graph.class_instances[0].id,),
        expected_object_instance_graph_id=graph.id,
        expected_graph_hash=str(graph.hash),
    )

    assert reused_payload["payload_sha256"]
    assert reused_rows is not None
    assert reused_rows["state_hash"] == state_index.compute_hash()
    assert reused_selection is not None
    assert set(reused_selection.class_instances_by_id) == {
        graph.class_instances[0].id,
    }


def test_snapshot_state_rows_payload_write_matches_hash_contract() -> None:
    payload: dict[str, object] = {
        "v": 2,
        "schema": "aware.oig.snapshot_state_rows.v2",
        "branch_id": str(uuid4()),
        "projection_hash": "state-row-single-pass-json",
        "commit_id": str(uuid4()),
        "object_instance_graph_id": str(uuid4()),
        "graph_hash": "hash:graph",
        "graph": {"id": str(uuid4()), "hash": "hash:graph"},
        "class_instances": [
            {
                "id": str(uuid4()),
                "object_instance_graph_id": str(uuid4()),
                "source_object_id": str(uuid4()),
            }
        ],
        "class_instance_relationships": [],
        "state_rows_text": f"NODE\t{uuid4()}\t{uuid4()}\n",
        "state_hash": "hash:state",
        "node_count": 1,
        "attribute_count": 0,
        "edge_count": 0,
    }
    expected_hash = _snapshot_state_rows_payload_hash(payload)

    write_payload = _snapshot_state_rows_payload_write(payload)
    written_payload = cast(dict[str, object], json.loads(write_payload.data))

    assert write_payload.payload["payload_sha256"] == expected_hash
    assert written_payload == write_payload.payload
    assert _snapshot_state_rows_payload_hash(written_payload) == expected_hash


@pytest.mark.asyncio
async def test_snapshot_store_witnessed_state_selection_skips_full_payload_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch_id = uuid4()
    projection_hash = "state-row-witness-sidecar"
    commit_id = uuid4()
    graph = _make_snapshot_state_row_graph()
    state_index = build_commit_state_index(graph)
    store = FSSnapshotStore(root_dir=tmp_path)

    payload = await store.put_state_snapshot_rows(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        object_instance_graph_id=graph.id,
        graph_hash=str(graph.hash),
        graph_meta={
            "id": graph.id,
            "key": graph.key,
            "name": graph.name,
            "description": graph.description,
            "object_projection_graph_id": graph.object_projection_graph_id,
            "root_class_instance_id": graph.root_class_instance_id,
            "root_source_object_id": graph.root_class_instance.source_object_id,
            "hash": graph.hash,
        },
        class_instances=tuple(graph.class_instances),
        class_instance_relationships=tuple(graph.class_instance_relationships),
        state_index=state_index,
    )
    metadata = store.snapshot_state_rows_file_metadata(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
    )
    assert metadata is not None

    def _unexpected_payload_hash(_payload: object) -> str:
        raise AssertionError("witnessed reads must not recompute full payload hash")

    def _unexpected_json_read(*_args: object, **_kwargs: object) -> object:
        raise AssertionError(
            "same-process witnessed state-row reads must use the structured cache"
        )

    monkeypatch.setattr(
        fs_snapshot_store_module,
        "_snapshot_state_rows_payload_hash",
        _unexpected_payload_hash,
    )
    monkeypatch.setattr(
        _SESSION_JSON_FILE_CACHE,
        "try_read_json_object",
        _unexpected_json_read,
    )

    selection = await store.get_snapshot_state_selection_by_file_witness(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        class_instance_ids=(graph.class_instances[0].id,),
        expected_file_size=_metadata_int(metadata, "state_snapshot_file_size"),
        expected_file_mtime_ns=_metadata_int(
            metadata,
            "state_snapshot_file_mtime_ns",
        ),
        expected_file_ctime_ns=_metadata_int(
            metadata,
            "state_snapshot_file_ctime_ns",
        ),
        expected_payload_sha256=str(payload["payload_sha256"]),
        expected_state_hash=str(payload["state_hash"]),
        expected_object_instance_graph_id=graph.id,
        expected_graph_hash=str(graph.hash),
        include_state_row_maps=True,
    )
    rejected = await store.get_snapshot_state_selection_by_file_witness(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        class_instance_ids=(graph.class_instances[0].id,),
        expected_file_size=_metadata_int(metadata, "state_snapshot_file_size") + 1,
        expected_file_mtime_ns=_metadata_int(
            metadata,
            "state_snapshot_file_mtime_ns",
        ),
        expected_file_ctime_ns=_metadata_int(
            metadata,
            "state_snapshot_file_ctime_ns",
        ),
        expected_payload_sha256=str(payload["payload_sha256"]),
        expected_state_hash=str(payload["state_hash"]),
        expected_object_instance_graph_id=graph.id,
        expected_graph_hash=str(graph.hash),
    )

    assert selection is not None
    assert selection.payload["payload_sha256"] == payload["payload_sha256"]
    assert selection.state_rows
    assert selection.state_row_maps is not None
    assert selection.state_row_maps.class_state_rows_by_raw_id
    assert set(selection.class_instances_by_id) == {graph.class_instances[0].id}
    assert rejected is None
    metrics = _snapshot_fs_store_session_read_cache_metrics()
    assert metrics["state_rows_hit_count"] >= 1
    assert metrics["state_rows_map_upgrade_count"] >= 1


@pytest.mark.asyncio
async def test_snapshot_store_writes_compact_state_witness_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch_id = uuid4()
    projection_hash = "compact-state-witness"
    commit_id = uuid4()
    graph = _make_snapshot_state_row_graph()
    state_index = build_commit_state_index(graph)
    expected_witness_ref = build_commit_state_witness_ref(state_index)
    store = FSSnapshotStore(root_dir=tmp_path)

    payload = await store.put_state_snapshot_rows(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        object_instance_graph_id=graph.id,
        graph_hash=str(graph.hash),
        graph_meta={
            "id": graph.id,
            "key": graph.key,
            "name": graph.name,
            "description": graph.description,
            "object_projection_graph_id": graph.object_projection_graph_id,
            "root_class_instance_id": graph.root_class_instance_id,
            "root_source_object_id": graph.root_class_instance.source_object_id,
            "hash": graph.hash,
        },
        class_instances=tuple(graph.class_instances),
        class_instance_relationships=tuple(graph.class_instance_relationships),
        state_index=state_index,
        write_state_witness=True,
    )
    metadata = store.snapshot_state_rows_file_metadata(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
    )
    assert metadata is not None

    def _unexpected_rows_parse(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("compact witness reads must not parse state rows")

    def _unexpected_payload_hash(_payload: object) -> str:
        raise AssertionError("compact witness reads must not hash replay payload")

    monkeypatch.setattr(
        fs_snapshot_store_module,
        "_commit_state_rows_read_from_snapshot_payload",
        _unexpected_rows_parse,
    )
    monkeypatch.setattr(
        fs_snapshot_store_module,
        "_commit_state_rows_from_snapshot_payload",
        _unexpected_rows_parse,
    )
    monkeypatch.setattr(
        fs_snapshot_store_module,
        "_snapshot_state_rows_payload_hash",
        _unexpected_payload_hash,
    )

    witness_metadata = (
        await store.get_snapshot_state_witness_metadata_by_state_rows_file_witness(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            expected_state_rows_file_size=_metadata_int(
                metadata,
                "state_snapshot_file_size",
            ),
            expected_state_rows_file_mtime_ns=_metadata_int(
                metadata,
                "state_snapshot_file_mtime_ns",
            ),
            expected_state_rows_file_ctime_ns=_metadata_int(
                metadata,
                "state_snapshot_file_ctime_ns",
            ),
            expected_state_rows_payload_sha256=str(payload["payload_sha256"]),
            expected_state_hash=state_index.compute_hash(),
            expected_witness_hash=expected_witness_ref.witness_hash,
            expected_object_instance_graph_id=graph.id,
            expected_graph_hash=str(graph.hash),
        )
    )
    rejected = (
        await store.get_snapshot_state_witness_metadata_by_state_rows_file_witness(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            expected_state_rows_file_size=(
                _metadata_int(metadata, "state_snapshot_file_size") + 1
            ),
            expected_state_rows_file_mtime_ns=_metadata_int(
                metadata,
                "state_snapshot_file_mtime_ns",
            ),
            expected_state_rows_file_ctime_ns=_metadata_int(
                metadata,
                "state_snapshot_file_ctime_ns",
            ),
            expected_state_rows_payload_sha256=str(payload["payload_sha256"]),
            expected_state_hash=state_index.compute_hash(),
            expected_witness_hash=expected_witness_ref.witness_hash,
            expected_object_instance_graph_id=graph.id,
            expected_graph_hash=str(graph.hash),
        )
    )

    assert witness_metadata is not None
    assert witness_metadata.state_hash == state_index.compute_hash()
    assert witness_metadata.witness_hash == expected_witness_ref.witness_hash
    assert witness_metadata.row_count == len(state_index.rows)
    assert witness_metadata.node_count == state_index.node_count
    assert witness_metadata.attribute_count == state_index.attribute_count
    assert witness_metadata.edge_count == state_index.edge_count
    assert witness_metadata.state_rows_payload_sha256 == payload["payload_sha256"]
    assert witness_metadata.witness_ref == expected_witness_ref
    assert rejected is None


@pytest.mark.asyncio
async def test_snapshot_store_reads_selected_class_segments_without_full_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch_id = uuid4()
    projection_hash = "compact-state-class-segments"
    commit_id = uuid4()
    graph = _make_snapshot_state_row_graph()
    state_index = build_commit_state_index(graph)
    class_instance_id = graph.class_instances[0].id
    assert class_instance_id is not None
    store = FSSnapshotStore(root_dir=tmp_path)

    payload = await store.put_state_snapshot_rows(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        object_instance_graph_id=graph.id,
        graph_hash=str(graph.hash),
        graph_meta={
            "id": graph.id,
            "key": graph.key,
            "name": graph.name,
            "description": graph.description,
            "object_projection_graph_id": graph.object_projection_graph_id,
            "root_class_instance_id": graph.root_class_instance_id,
            "root_source_object_id": graph.root_class_instance.source_object_id,
            "hash": graph.hash,
        },
        class_instances=tuple(graph.class_instances),
        class_instance_relationships=tuple(graph.class_instance_relationships),
        state_index=state_index,
        write_state_witness=True,
        write_state_class_segments=True,
        write_state_class_segment_index=True,
    )
    metadata = store.snapshot_state_rows_file_metadata(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
    )
    assert metadata is not None

    def _unexpected_rows_parse(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("selected segment reads must not parse full state rows")

    def _unexpected_payload_hash(_payload: object) -> str:
        raise AssertionError("selected segment reads must not hash replay payload")

    monkeypatch.setattr(
        fs_snapshot_store_module,
        "_commit_state_rows_read_from_snapshot_payload",
        _unexpected_rows_parse,
    )
    monkeypatch.setattr(
        fs_snapshot_store_module,
        "_commit_state_rows_from_snapshot_payload",
        _unexpected_rows_parse,
    )
    monkeypatch.setattr(
        fs_snapshot_store_module,
        "_snapshot_state_rows_payload_hash",
        _unexpected_payload_hash,
    )

    selection = await store.get_snapshot_state_class_segments_by_file_witness(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        class_instance_ids=(class_instance_id,),
        expected_state_rows_file_size=_metadata_int(
            metadata,
            "state_snapshot_file_size",
        ),
        expected_state_rows_file_mtime_ns=_metadata_int(
            metadata,
            "state_snapshot_file_mtime_ns",
        ),
        expected_state_rows_file_ctime_ns=_metadata_int(
            metadata,
            "state_snapshot_file_ctime_ns",
        ),
        expected_state_rows_payload_sha256=str(payload["payload_sha256"]),
        expected_state_hash=state_index.compute_hash(),
        expected_object_instance_graph_id=graph.id,
        expected_graph_hash=str(graph.hash),
    )
    rejected = await store.get_snapshot_state_class_segments_by_file_witness(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        class_instance_ids=(uuid4(),),
        expected_state_rows_file_size=_metadata_int(
            metadata,
            "state_snapshot_file_size",
        ),
        expected_state_rows_file_mtime_ns=_metadata_int(
            metadata,
            "state_snapshot_file_mtime_ns",
        ),
        expected_state_rows_file_ctime_ns=_metadata_int(
            metadata,
            "state_snapshot_file_ctime_ns",
        ),
        expected_state_rows_payload_sha256=str(payload["payload_sha256"]),
        expected_state_hash=state_index.compute_hash(),
        expected_object_instance_graph_id=graph.id,
        expected_graph_hash=str(graph.hash),
    )

    assert selection is not None
    assert set(selection.class_segments_by_id) == {class_instance_id}
    assert set(selection.class_instances_by_id) == {class_instance_id}
    assert (
        selection.class_segments_by_id[class_instance_id].rows
        == state_index.rows[
            : len(selection.class_segments_by_id[class_instance_id].rows)
        ]
    )
    assert selection.witness_metadata.state_hash == state_index.compute_hash()
    assert rejected is None

    def _unexpected_class_instance_hydration(
        *_args: object, **_kwargs: object
    ) -> object:
        raise AssertionError("raw segment reads must not hydrate ClassInstance")

    monkeypatch.setattr(
        ClassInstance,
        "model_validate",
        _unexpected_class_instance_hydration,
    )

    raw_selection = await store.get_snapshot_state_raw_class_segments_by_file_witness(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        class_instance_ids=(class_instance_id,),
        expected_state_rows_file_size=_metadata_int(
            metadata,
            "state_snapshot_file_size",
        ),
        expected_state_rows_file_mtime_ns=_metadata_int(
            metadata,
            "state_snapshot_file_mtime_ns",
        ),
        expected_state_rows_file_ctime_ns=_metadata_int(
            metadata,
            "state_snapshot_file_ctime_ns",
        ),
        expected_state_rows_payload_sha256=str(payload["payload_sha256"]),
        expected_state_hash=state_index.compute_hash(),
        expected_object_instance_graph_id=graph.id,
        expected_graph_hash=str(graph.hash),
    )
    raw_rejected = await store.get_snapshot_state_raw_class_segments_by_file_witness(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        class_instance_ids=(uuid4(),),
        expected_state_rows_file_size=_metadata_int(
            metadata,
            "state_snapshot_file_size",
        ),
        expected_state_rows_file_mtime_ns=_metadata_int(
            metadata,
            "state_snapshot_file_mtime_ns",
        ),
        expected_state_rows_file_ctime_ns=_metadata_int(
            metadata,
            "state_snapshot_file_ctime_ns",
        ),
        expected_state_rows_payload_sha256=str(payload["payload_sha256"]),
        expected_state_hash=state_index.compute_hash(),
        expected_object_instance_graph_id=graph.id,
        expected_graph_hash=str(graph.hash),
    )

    assert raw_selection is not None
    assert set(raw_selection.class_segments_by_id) == {class_instance_id}
    raw_segment = raw_selection.class_segments_by_id[class_instance_id]
    assert raw_segment.rows_text
    assert raw_segment.row_count == len(
        selection.class_segments_by_id[class_instance_id].rows,
    )
    assert raw_segment.row_hash == raw_segment.segment_ref.row_hash
    assert raw_segment.row_count == raw_segment.segment_ref.row_count
    assert raw_segment.snapshot_payload["id"] == str(class_instance_id)
    assert raw_selection.witness_metadata.state_hash == state_index.compute_hash()
    assert raw_rejected is None

    store._snapshot_state_class_segments_index_path(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
    ).unlink()

    indexed_selection = (
        await store.get_snapshot_state_indexed_raw_class_segments_by_file_witness(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            class_instance_ids=(class_instance_id,),
            expected_state_rows_file_size=_metadata_int(
                metadata,
                "state_snapshot_file_size",
            ),
            expected_state_rows_file_mtime_ns=_metadata_int(
                metadata,
                "state_snapshot_file_mtime_ns",
            ),
            expected_state_rows_file_ctime_ns=_metadata_int(
                metadata,
                "state_snapshot_file_ctime_ns",
            ),
            expected_state_rows_payload_sha256=str(payload["payload_sha256"]),
            expected_state_hash=state_index.compute_hash(),
            expected_object_instance_graph_id=graph.id,
            expected_graph_hash=str(graph.hash),
        )
    )
    indexed_rejected = (
        await store.get_snapshot_state_indexed_raw_class_segments_by_file_witness(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            class_instance_ids=(uuid4(),),
            expected_state_rows_file_size=_metadata_int(
                metadata,
                "state_snapshot_file_size",
            ),
            expected_state_rows_file_mtime_ns=_metadata_int(
                metadata,
                "state_snapshot_file_mtime_ns",
            ),
            expected_state_rows_file_ctime_ns=_metadata_int(
                metadata,
                "state_snapshot_file_ctime_ns",
            ),
            expected_state_rows_payload_sha256=str(payload["payload_sha256"]),
            expected_state_hash=state_index.compute_hash(),
            expected_object_instance_graph_id=graph.id,
            expected_graph_hash=str(graph.hash),
        )
    )

    assert indexed_selection is not None
    indexed_segment = indexed_selection.class_segments_by_id[class_instance_id]
    assert indexed_segment.rows_text == raw_segment.rows_text
    assert indexed_segment.row_hash == raw_segment.row_hash
    assert indexed_segment.snapshot_payload["id"] == str(class_instance_id)
    assert indexed_rejected is None


@pytest.mark.asyncio
async def test_snapshot_store_composes_indexed_class_segments_from_previous(
    tmp_path: Path,
) -> None:
    branch_id = uuid4()
    projection_hash = "composed-state-class-segments"
    previous_commit_id = uuid4()
    commit_id = uuid4()
    graph_id = uuid4()
    source_ids = (uuid4(), uuid4())
    name_cfg = make_attribute_config(
        owner_key=_SNAPSHOT_TEST_FQN,
        name="name",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    ocg, opg, user_cc = _make_snapshot_ocg_opg(name_cfg=name_cfg)
    previous_graph = _make_snapshot_state_row_graph_with_users(
        ocg=ocg,
        opg=opg,
        user_cc=user_cc,
        graph_id=graph_id,
        source_ids=source_ids,
        names=("Ada", "Alan"),
    )
    post_graph = _make_snapshot_state_row_graph_with_users(
        ocg=ocg,
        opg=opg,
        user_cc=user_cc,
        graph_id=graph_id,
        source_ids=source_ids,
        names=("Grace", "Alan"),
    )
    previous_state_index = build_commit_state_index(previous_graph)
    post_state_index = build_commit_state_index(post_graph)
    changed_class_instance = post_graph.class_instances[0]
    unchanged_class_instance = post_graph.class_instances[1]
    assert changed_class_instance.id is not None
    assert changed_class_instance.class_config_id is not None
    assert changed_class_instance.source_object_id is not None
    assert unchanged_class_instance.id is not None

    store = FSSnapshotStore(root_dir=tmp_path)
    await store.put_state_snapshot_rows(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=previous_commit_id,
        object_instance_graph_id=previous_graph.id,
        graph_hash=str(previous_graph.hash),
        graph_meta=_snapshot_graph_meta(previous_graph),
        class_instances=tuple(previous_graph.class_instances),
        class_instance_relationships=tuple(previous_graph.class_instance_relationships),
        state_index=previous_state_index,
        write_state_class_segment_index=True,
    )

    previous_witness_ref = build_commit_state_witness_ref(previous_state_index)
    previous_witness_cursor = build_commit_state_witness_cursor(
        previous_witness_ref,
        chunk_size=1,
    )
    previous_metadata = store.snapshot_state_class_segment_index_metadata(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=previous_commit_id,
        expected_object_instance_graph_id=previous_graph.id,
        expected_graph_hash=str(previous_graph.hash),
    )
    assert previous_metadata is not None
    assert previous_metadata.state_hash == previous_state_index.compute_hash()
    assert previous_metadata.witness_ref == previous_witness_ref

    post_witness_ref = build_commit_state_witness_ref(post_state_index)
    changed_rows = post_state_index.row_maps(
        include_relationship_keys=False,
    ).class_state_rows_by_id[changed_class_instance.id]
    changed_segment_ref = next(
        segment
        for segment in post_witness_ref.segments
        if segment.key == f"class:{changed_class_instance.id}"
    )
    replacement_segment = ObjectInstanceGraphSnapshotStateRawClassSegment(
        class_instance_id=changed_class_instance.id,
        class_config_id=changed_class_instance.class_config_id,
        source_object_id=changed_class_instance.source_object_id,
        rows_text="".join(
            f"{row.kind}\t{row.key}\t{row.value}\n" for row in changed_rows
        ),
        row_count=len(changed_rows),
        row_hash=compute_commit_state_rows_hash(changed_rows),
        snapshot_payload=cast(
            dict[str, object],
            changed_class_instance.model_dump(mode="json", exclude_none=True),
        ),
        segment_ref=changed_segment_ref,
    )
    witness_only_post_ref = replace_existing_commit_state_witness_ref_segments(
        pre_witness_ref=previous_witness_ref,
        replacement_segments_by_key={
            f"class:{changed_class_instance.id}": changed_segment_ref,
        },
    )
    witness_only_cursor = replace_existing_commit_state_witness_cursor_segments(
        cursor=previous_witness_cursor,
        replacement_segments_by_key={
            f"class:{changed_class_instance.id}": changed_segment_ref,
        },
    )
    assert witness_only_post_ref.state_hash is None
    assert witness_only_post_ref.witness_hash == post_witness_ref.witness_hash
    assert witness_only_cursor.state_hash is None
    assert witness_only_cursor.legacy_witness_hash == post_witness_ref.witness_hash

    composed_payload = await store.put_state_snapshot_class_segment_index_from_previous(
        branch_id=branch_id,
        projection_hash=projection_hash,
        previous_commit_id=previous_commit_id,
        commit_id=commit_id,
        object_instance_graph_id=post_graph.id,
        graph_hash=witness_only_post_ref.witness_hash,
        post_witness_ref=witness_only_post_ref,
        replacement_class_segments=(replacement_segment,),
        graph_meta=_snapshot_graph_meta(post_graph),
        graph_hash_source="witness_hash",
        state_witness_cursor_summary=witness_only_cursor.summary(),
    )

    assert composed_payload is not None
    assert (
        composed_payload["schema"] == "aware.oig.snapshot_state_class_segment_index.v4"
    )
    assert composed_payload["base_commit_id"] == str(previous_commit_id)
    assert composed_payload["replacement_class_segment_count"] == 1
    assert "class_segment_count" not in composed_payload
    assert "class_segments" not in composed_payload
    assert "segments" not in composed_payload
    assert (
        cast(dict[str, object], composed_payload["state_witness_cursor"])["cursor_hash"]
        == witness_only_cursor.cursor_hash
    )
    assert (
        store.snapshot_state_rows_file_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        is None
    )
    composed_metadata = store.snapshot_state_class_segment_index_metadata(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        expected_object_instance_graph_id=post_graph.id,
        expected_graph_hash=witness_only_post_ref.witness_hash,
    )
    assert composed_metadata is not None
    assert composed_metadata.state_hash is None
    assert composed_metadata.witness_ref == witness_only_post_ref
    assert composed_metadata.witness_cursor_summary == witness_only_cursor.summary()

    previous_manifest = json.loads(
        store._snapshot_state_class_segment_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=previous_commit_id,
        ).read_text(encoding="utf-8")
    )
    composed_manifest = json.loads(
        store._snapshot_state_class_segment_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        ).read_text(encoding="utf-8")
    )
    previous_refs = {
        item["class_instance_id"]: item for item in previous_manifest["class_segments"]
    }
    composed_replacement_refs = {
        item["class_instance_id"]: item
        for item in composed_manifest["replacement_class_segments"]
    }
    assert str(unchanged_class_instance.id) not in composed_replacement_refs
    assert composed_replacement_refs[str(changed_class_instance.id)][
        "record_sha256"
    ] != (previous_refs[str(changed_class_instance.id)]["record_sha256"])
    assert composed_replacement_refs[str(changed_class_instance.id)][
        "blob_commit_id"
    ] == str(commit_id)
    assert composed_replacement_refs[str(changed_class_instance.id)]["byte_offset"] == 0
    assert (
        composed_manifest["segment_blob"]["byte_size"]
        == composed_replacement_refs[str(changed_class_instance.id)]["byte_length"]
    )

    selection = (
        await store.get_snapshot_state_indexed_raw_class_segments_by_witness_ref(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            class_instance_ids=(changed_class_instance.id, unchanged_class_instance.id),
            expected_witness_ref=witness_only_post_ref,
            expected_object_instance_graph_id=post_graph.id,
            expected_graph_hash=witness_only_post_ref.witness_hash,
        )
    )

    assert selection is not None
    assert selection.witness_metadata.witness_ref == witness_only_post_ref
    assert selection.witness_metadata.state_hash is None
    assert set(selection.class_segments_by_id) == {
        changed_class_instance.id,
        unchanged_class_instance.id,
    }
    assert selection.class_segments_by_id[changed_class_instance.id].snapshot_payload[
        "id"
    ] == str(changed_class_instance.id)
    assert (
        selection.class_segments_by_id[unchanged_class_instance.id].row_hash
        == previous_refs[str(unchanged_class_instance.id)]["segment"]["row_hash"]
    )

    previous_manifest_path = store._snapshot_state_class_segment_index_path(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=previous_commit_id,
    )
    corrupted_manifest = json.loads(previous_manifest_path.read_text(encoding="utf-8"))
    for item in corrupted_manifest["class_segments"]:
        if item["class_instance_id"] == str(unchanged_class_instance.id):
            del item["record_sha256"]
            break
    previous_manifest_path.write_text(
        json.dumps(corrupted_manifest),
        encoding="utf-8",
    )

    selected_only = (
        await store.get_snapshot_state_indexed_raw_class_segments_by_witness_ref(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            class_instance_ids=(changed_class_instance.id,),
            expected_witness_ref=witness_only_post_ref,
            expected_object_instance_graph_id=post_graph.id,
            expected_graph_hash=witness_only_post_ref.witness_hash,
        )
    )
    assert selected_only is not None
    assert set(selected_only.class_segments_by_id) == {changed_class_instance.id}

    corrupted_selected = (
        await store.get_snapshot_state_indexed_raw_class_segments_by_witness_ref(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            class_instance_ids=(unchanged_class_instance.id,),
            expected_witness_ref=witness_only_post_ref,
            expected_object_instance_graph_id=post_graph.id,
            expected_graph_hash=witness_only_post_ref.witness_hash,
        )
    )
    assert corrupted_selected is None


@pytest.mark.asyncio
async def test_snapshot_store_reads_cursor_hash_direct_from_chunk_sidecar(
    tmp_path: Path,
) -> None:
    branch_id = uuid4()
    projection_hash = "cursor-hash-direct-sidecar-state-class-segments"
    commit_id = uuid4()
    graph = _make_snapshot_state_row_graph()
    class_instance = graph.class_instances[0]
    assert class_instance.id is not None
    state_index = build_commit_state_index(graph)
    witness_ref = build_commit_state_witness_ref(state_index)
    witness_cursor = build_commit_state_witness_cursor(witness_ref, chunk_size=1)
    store = FSSnapshotStore(root_dir=tmp_path)

    await store.put_state_snapshot_class_segment_index(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        object_instance_graph_id=graph.id,
        graph_hash=witness_cursor.cursor_hash,
        post_witness_ref=witness_ref,
        class_segments=_raw_class_segments_for_graph(
            graph=graph,
            state_index=state_index,
            witness_ref=witness_ref,
        ),
        graph_meta=_snapshot_graph_meta(graph),
        graph_hash_source="witness_cursor_hash",
        state_witness_cursor_summary=witness_cursor.summary(),
        state_witness_cursor_chunks=witness_cursor.chunks,
    )

    manifest_path = store._snapshot_state_class_segment_index_path(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
    )
    manifest_path.write_text("{not-json", encoding="utf-8")
    _SESSION_JSON_FILE_CACHE.invalidate_path(manifest_path)

    trace = CommitPerfTraceRecorder(default_category="test")
    with active_commit_perf_trace(trace):
        selection = (
            await store.get_snapshot_state_indexed_raw_class_segments_by_witness_cursor(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                class_instance_ids=(class_instance.id,),
                expected_witness_cursor_summary=witness_cursor.summary(),
                expected_object_instance_graph_id=graph.id,
                expected_graph_hash=witness_cursor.cursor_hash,
            )
        )

    phases = {str(event["phase"]) for event in trace.snapshot_json()}
    assert "oig_snapshot_store.state_class_segment_cursor.chunk_sidecar_read" in phases
    assert "oig_snapshot_store.state_class_segment_cursor.read_manifest" not in phases
    assert selection is not None
    assert set(selection.class_segments_by_id) == {class_instance.id}
    assert selection.class_segments_by_id[class_instance.id].snapshot_payload[
        "id"
    ] == str(class_instance.id)


@pytest.mark.asyncio
async def test_snapshot_store_reads_cursor_hash_overlay_without_witness_ref(
    tmp_path: Path,
) -> None:
    branch_id = uuid4()
    projection_hash = "cursor-hash-state-class-segments"
    previous_commit_id = uuid4()
    commit_id = uuid4()
    graph_id = uuid4()
    source_ids = (uuid4(), uuid4())
    name_cfg = make_attribute_config(
        owner_key=_SNAPSHOT_TEST_FQN,
        name="name",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    ocg, opg, user_cc = _make_snapshot_ocg_opg(name_cfg=name_cfg)
    previous_graph = _make_snapshot_state_row_graph_with_users(
        ocg=ocg,
        opg=opg,
        user_cc=user_cc,
        graph_id=graph_id,
        source_ids=source_ids,
        names=("Ada", "Alan"),
    )
    post_graph = _make_snapshot_state_row_graph_with_users(
        ocg=ocg,
        opg=opg,
        user_cc=user_cc,
        graph_id=graph_id,
        source_ids=source_ids,
        names=("Grace", "Alan"),
    )
    previous_state_index = build_commit_state_index(previous_graph)
    post_state_index = build_commit_state_index(post_graph)
    previous_witness_ref = build_commit_state_witness_ref(previous_state_index)
    previous_cursor = build_commit_state_witness_cursor(
        previous_witness_ref,
        chunk_size=1,
    )
    post_witness_ref = build_commit_state_witness_ref(post_state_index)
    changed_class_instance = post_graph.class_instances[0]
    unchanged_class_instance = post_graph.class_instances[1]
    assert changed_class_instance.id is not None
    assert unchanged_class_instance.id is not None

    store = FSSnapshotStore(root_dir=tmp_path)
    await store.put_state_snapshot_class_segment_index(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=previous_commit_id,
        object_instance_graph_id=previous_graph.id,
        graph_hash=previous_cursor.cursor_hash,
        post_witness_ref=previous_witness_ref,
        class_segments=_raw_class_segments_for_graph(
            graph=previous_graph,
            state_index=previous_state_index,
            witness_ref=previous_witness_ref,
        ),
        graph_meta=_snapshot_graph_meta(previous_graph),
        graph_hash_source="witness_cursor_hash",
        state_witness_cursor_summary=previous_cursor.summary(),
        state_witness_cursor_chunks=previous_cursor.chunks,
    )
    replacement_segment = next(
        segment
        for segment in _raw_class_segments_for_graph(
            graph=post_graph,
            state_index=post_state_index,
            witness_ref=post_witness_ref,
        )
        if segment.class_instance_id == changed_class_instance.id
    )
    replacement_ref = replacement_segment.segment_ref
    previous_changed_chunk = next(
        chunk
        for chunk in previous_cursor.chunks
        if replacement_ref.key in chunk.segment_keys
    )
    post_changed_chunk = replace_commit_state_witness_cursor_chunk_segments(
        chunk=previous_changed_chunk,
        replacement_segments_by_key={replacement_ref.key: replacement_ref},
    )
    post_cursor_summary = replace_existing_commit_state_witness_cursor_summary_chunks(
        summary=previous_cursor.summary(),
        replacement_chunks_by_index={post_changed_chunk.index: post_changed_chunk},
    )

    payload = await store.put_state_snapshot_class_segment_index_from_previous(
        branch_id=branch_id,
        projection_hash=projection_hash,
        previous_commit_id=previous_commit_id,
        commit_id=commit_id,
        object_instance_graph_id=post_graph.id,
        graph_hash=post_cursor_summary.cursor_hash,
        post_witness_ref=None,
        replacement_class_segments=(replacement_segment,),
        graph_meta=_snapshot_graph_meta(post_graph),
        graph_hash_source="witness_cursor_hash",
        state_witness_cursor_summary=post_cursor_summary,
        state_witness_cursor_chunks=(post_changed_chunk,),
    )

    assert payload is not None
    assert payload["graph_hash_source"] == "witness_cursor_hash"
    assert "commit_state_witness_schema" not in payload
    assert payload["graph_hash"] == post_cursor_summary.cursor_hash

    metadata = store.snapshot_state_class_segment_index_metadata(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        expected_object_instance_graph_id=post_graph.id,
        expected_graph_hash=post_cursor_summary.cursor_hash,
    )
    assert metadata is not None
    assert metadata.graph_hash == post_cursor_summary.cursor_hash
    assert metadata.witness_cursor_summary == post_cursor_summary

    trace = CommitPerfTraceRecorder(default_category="test")
    with active_commit_perf_trace(trace):
        selection = (
            await store.get_snapshot_state_indexed_raw_class_segments_by_witness_cursor(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                class_instance_ids=(
                    changed_class_instance.id,
                    unchanged_class_instance.id,
                ),
                expected_witness_cursor_summary=post_cursor_summary,
                expected_object_instance_graph_id=post_graph.id,
                expected_graph_hash=post_cursor_summary.cursor_hash,
            )
        )

    phases = {str(event["phase"]) for event in trace.snapshot_json()}
    assert {
        "oig_snapshot_store.state_class_segment_cursor.validate_summary",
        "oig_snapshot_store.state_class_segment_cursor.blob_metadata",
        "oig_snapshot_store.state_class_segment_cursor.extract_refs",
        "oig_snapshot_store.state_class_segment_cursor.select_chunk_indexes",
        "oig_snapshot_store.state_class_segment_cursor.parse_selected_chunks",
        "oig_snapshot_store.state_class_segment_cursor.overlay_selected_refs",
        "oig_snapshot_store.state_class_segment_cursor.read_overlay_records",
        "oig_snapshot_store.state_class_segment_cursor.base_manifest_read",
        "oig_snapshot_store.state_class_segment_cursor.base_recursion",
        "oig_snapshot_store.state_class_segment_cursor.merge_base_selection",
        "oig_snapshot_store.state_class_segment_records.blob_read",
        "oig_snapshot_store.state_class_segment_records.json_decode",
        "oig_snapshot_store.state_class_segment_records.payload_decode",
    } <= phases

    assert selection is not None
    assert selection.witness_cursor_summary == post_cursor_summary
    assert set(selection.class_segments_by_id) == {
        changed_class_instance.id,
        unchanged_class_instance.id,
    }
    assert selection.class_segments_by_id[changed_class_instance.id].snapshot_payload[
        "id"
    ] == str(changed_class_instance.id)
    assert selection.class_segments_by_id[unchanged_class_instance.id].snapshot_payload[
        "id"
    ] == str(unchanged_class_instance.id)


@pytest.mark.asyncio
async def test_snapshot_store_writes_direct_witness_hash_segment_index(
    tmp_path: Path,
) -> None:
    branch_id = uuid4()
    projection_hash = "direct-witness-state-class-segments"
    commit_id = uuid4()
    graph = _make_snapshot_state_row_graph()
    class_instance = graph.class_instances[0]
    assert class_instance.id is not None
    assert class_instance.class_config_id is not None
    assert class_instance.source_object_id is not None
    state_index = build_commit_state_index(graph)
    witness_ref = build_commit_state_witness_ref(state_index)
    witness_cursor = build_commit_state_witness_cursor(witness_ref, chunk_size=1)
    rows = state_index.row_maps(
        include_relationship_keys=False,
    ).class_state_rows_by_id[class_instance.id]
    segment_ref = next(
        segment
        for segment in witness_ref.segments
        if segment.key == f"class:{class_instance.id}"
    )
    raw_segment = ObjectInstanceGraphSnapshotStateRawClassSegment(
        class_instance_id=class_instance.id,
        class_config_id=class_instance.class_config_id,
        source_object_id=class_instance.source_object_id,
        rows_text="".join(f"{row.kind}\t{row.key}\t{row.value}\n" for row in rows),
        row_count=len(rows),
        row_hash=compute_commit_state_rows_hash(rows),
        snapshot_payload=cast(
            dict[str, object],
            class_instance.model_dump(mode="json", exclude_none=True),
        ),
        segment_ref=segment_ref,
    )
    store = FSSnapshotStore(root_dir=tmp_path)

    payload = await store.put_state_snapshot_class_segment_index(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        object_instance_graph_id=graph.id,
        graph_hash=witness_ref.witness_hash,
        post_witness_ref=witness_ref,
        class_segments=(raw_segment,),
        graph_meta=_snapshot_graph_meta(graph),
        graph_hash_source="witness_hash",
        state_witness_cursor_summary=witness_cursor.summary(),
    )

    assert payload["schema"] == "aware.oig.snapshot_state_class_segment_index.v3"
    assert payload["graph_hash_source"] == "witness_hash"
    assert payload["graph_hash"] == witness_ref.witness_hash
    assert (
        cast(dict[str, object], payload["state_witness_cursor"])["cursor_hash"]
        == witness_cursor.cursor_hash
    )
    payload_class_segments = cast(list[dict[str, object]], payload["class_segments"])
    assert payload_class_segments[0]["blob_commit_id"] == str(commit_id)
    assert (
        store.snapshot_state_rows_file_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        is None
    )
    metadata = store.snapshot_state_class_segment_index_metadata(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        expected_object_instance_graph_id=graph.id,
        expected_graph_hash=witness_ref.witness_hash,
    )
    assert metadata is not None
    assert metadata.payload["graph_hash_source"] == "witness_hash"
    assert metadata.state_hash == state_index.compute_hash()
    assert metadata.witness_ref == witness_ref
    assert metadata.witness_cursor_summary == witness_cursor.summary()

    selection = (
        await store.get_snapshot_state_indexed_raw_class_segments_by_witness_ref(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            class_instance_ids=(class_instance.id,),
            expected_witness_ref=witness_ref,
            expected_object_instance_graph_id=graph.id,
            expected_graph_hash=witness_ref.witness_hash,
        )
    )

    assert selection is not None
    assert selection.witness_metadata.payload["graph_hash_source"] == "witness_hash"
    assert selection.witness_metadata.witness_cursor_summary == (
        witness_cursor.summary()
    )
    assert set(selection.class_segments_by_id) == {class_instance.id}
    assert selection.class_segments_by_id[class_instance.id].snapshot_payload[
        "id"
    ] == str(class_instance.id)

    manifest_path = store._snapshot_state_class_segment_index_path(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
    )
    corrupted_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    corrupted_payload["state_witness_cursor"]["cursor_hash"] = "bad-cursor-hash"
    manifest_path.write_text(json.dumps(corrupted_payload), encoding="utf-8")
    _SESSION_JSON_FILE_CACHE.invalidate_path(manifest_path)

    assert (
        store.snapshot_state_class_segment_index_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            expected_object_instance_graph_id=graph.id,
            expected_graph_hash=witness_ref.witness_hash,
        )
        is None
    )


@pytest.mark.asyncio
async def test_commit_store_finds_oig_commit_ref_across_branches(tmp_path) -> None:
    store = FSCommitStore(root_dir=tmp_path)
    projection_hash = "ServicePackage"
    branch_id = uuid4()
    other_branch_id = uuid4()
    commit = _make_commit(projection_hash=projection_hash)
    other_commit = _make_commit(projection_hash=projection_hash)
    await store.put_commit_file(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit=commit,
    )
    await store.put_commit_file(
        branch_id=other_branch_id,
        projection_hash=projection_hash,
        commit=other_commit,
    )
    object_instance_graph_commit_id = stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
        commit_id=commit.commit.id,
    )

    refs = await store.domain_commit_refs_for_object_instance_graph_commit_id(
        projection_hash=projection_hash,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
    )

    assert len(refs) == 1
    assert refs[0].branch_id == branch_id
    assert refs[0].projection_hash == projection_hash
    assert refs[0].object_instance_graph_commit_id == object_instance_graph_commit_id
    assert refs[0].domain_commit_id == commit.commit.id


@pytest.mark.asyncio
async def test_commit_store_resolves_oig_commit_refs_in_one_index_pass(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = FSCommitStore(root_dir=tmp_path)
    projection_hash = "CodePackage"
    first_branch_id = uuid4()
    second_branch_id = uuid4()
    first_commit = _make_commit(projection_hash=projection_hash)
    second_commit = _make_commit(projection_hash=projection_hash)
    await store.put_commit_file(
        branch_id=first_branch_id,
        projection_hash=projection_hash,
        commit=first_commit,
    )
    await store.put_commit_file(
        branch_id=second_branch_id,
        projection_hash=projection_hash,
        commit=second_commit,
    )
    first_oig_commit_id = stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=first_commit.object_instance_graph_identity_id,
        commit_id=first_commit.commit.id,
    )
    second_oig_commit_id = stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=second_commit.object_instance_graph_identity_id,
        commit_id=second_commit.commit.id,
    )

    async def _boom(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("indexed batch ref resolution must not read lane HEAD")

    monkeypatch.setattr(FSCommitStore, "head_commit", _boom, raising=True)

    refs_by_id = await store.domain_commit_refs_for_object_instance_graph_commit_ids(
        projection_hash=projection_hash,
        object_instance_graph_commit_ids=(first_oig_commit_id, second_oig_commit_id),
    )

    assert refs_by_id[first_oig_commit_id][0].branch_id == first_branch_id
    assert refs_by_id[first_oig_commit_id][0].domain_commit_id == first_commit.commit.id
    assert refs_by_id[second_oig_commit_id][0].branch_id == second_branch_id
    assert (
        refs_by_id[second_oig_commit_id][0].domain_commit_id == second_commit.commit.id
    )


@pytest.mark.asyncio
async def test_commit_store_batch_ref_resolution_can_disable_head_fallback(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = FSCommitStore(root_dir=tmp_path)
    projection_hash = "CodePackage"
    missing_oig_commit_id = uuid4()

    async def _boom(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("strict indexed resolution must not read lane HEAD")

    monkeypatch.setattr(FSCommitStore, "head_commit", _boom, raising=True)

    refs_by_id = await store.domain_commit_refs_for_object_instance_graph_commit_ids(
        projection_hash=projection_hash,
        object_instance_graph_commit_ids=(missing_oig_commit_id,),
        allow_head_fallback=False,
    )

    assert refs_by_id == {missing_oig_commit_id: ()}


@pytest.mark.asyncio
async def test_commit_store_append_records_writes_single_final_head(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    head_write_paths: list[Path] = []
    original_durable_write = fs_commit_store_module._atomic_write

    def _record_head_write(path: Path, data: str) -> None:
        if path.name == "HEAD.json":
            head_write_paths.append(path)
        original_durable_write(path, data)

    monkeypatch.setattr(
        fs_commit_store_module,
        "_atomic_write",
        _record_head_write,
    )

    store = FSCommitStore(root_dir=tmp_path)
    branch_id = uuid4()
    projection_hash = "CodePackage"
    object_instance_graph_identity_id = uuid4()
    object_instance_graph_id = uuid4()
    first = _make_commit(
        projection_hash=projection_hash,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
        graph_hash_post="sha256:test:batch:first",
    )
    second = _make_commit(
        projection_hash=projection_hash,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
        parent_commit_id=first.commit.id,
        graph_hash_pre=first.graph_hash_post,
        graph_hash_post="sha256:test:batch:second",
    )
    watcher_receipts: list[LaneHeadCommitReceipt] = []

    def _watcher(receipt: LaneHeadCommitReceipt) -> None:
        watcher_receipts.append(receipt)

    FSCommitStore.register_lane_head_watcher(_watcher)
    try:
        perf = await store.append_records(
            branch_id=branch_id,
            projection_hash=projection_hash,
            records=(
                _record_from_commit(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    commit=first,
                ),
                _record_from_commit(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    commit=second,
                ),
            ),
        )
    finally:
        FSCommitStore.unregister_lane_head_watcher(_watcher)

    head = await store.head(branch_id=branch_id, projection_hash=projection_hash)
    assert head is not None
    assert head["commit_id"] == str(second.commit.id)
    assert head["graph_hash_post"] == second.graph_hash_post
    assert await store.get_commit(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=first.commit.id,
    )
    assert await store.get_commit(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=second.commit.id,
    )
    assert perf["append_record_count"] == 2
    assert perf["batch_append_record_count"] == 2
    assert perf["durable_head_write_count"] == 1
    assert perf["batch_final_head_write_count"] == 1
    assert perf["durable_body_write_count"] == 2
    assert perf["durable_envelope_write_count"] == 2
    assert perf["durable_write_count"] == 5
    assert perf["grouped_durable_transaction_write_count"] == 5
    assert perf["independent_durable_write_count"] == 0
    assert perf["grouped_durable_transaction_count"] == 1
    assert perf["grouped_durable_transaction_syncfs_count"] in (0, 1)
    if perf["grouped_durable_transaction_syncfs_count"] == 0:
        assert perf["grouped_durable_transaction_file_fsync_count"] == 5
    assert len(head_write_paths) == 1
    assert len(watcher_receipts) == 1
    assert watcher_receipts[0].commit_id == second.commit.id


@pytest.mark.asyncio
async def test_commit_store_reports_ambiguous_oig_commit_ref_matches(tmp_path) -> None:
    store = FSCommitStore(root_dir=tmp_path)
    projection_hash = "ServicePackage"
    first_branch_id = uuid4()
    second_branch_id = uuid4()
    commit = _make_commit(projection_hash=projection_hash)
    await store.put_commit_file(
        branch_id=first_branch_id,
        projection_hash=projection_hash,
        commit=commit,
    )
    await store.put_commit_file(
        branch_id=second_branch_id,
        projection_hash=projection_hash,
        commit=commit,
    )
    object_instance_graph_commit_id = stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
        commit_id=commit.commit.id,
    )

    refs = await store.domain_commit_refs_for_object_instance_graph_commit_id(
        projection_hash=projection_hash,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
    )

    assert {ref.branch_id for ref in refs} == {first_branch_id, second_branch_id}


@pytest.mark.asyncio
async def test_put_commit_file_rejects_existing_envelope_identity_mismatch(
    tmp_path,
) -> None:
    store = FSCommitStore(root_dir=tmp_path)
    branch_id = uuid4()
    projection_hash = "ObjectConfigGraphPackage"
    commit_id = uuid4()
    object_instance_graph_id = uuid4()
    legacy_oigi_id = uuid4()
    canonical_oigi_id = uuid4()
    graph_hash_post = "sha256:graph-post"
    legacy_commit = _make_commit(
        projection_hash=projection_hash,
        commit_id=commit_id,
        object_instance_graph_identity_id=legacy_oigi_id,
        object_instance_graph_id=object_instance_graph_id,
        graph_hash_post=graph_hash_post,
    )
    canonical_commit = _make_commit(
        projection_hash=projection_hash,
        commit_id=commit_id,
        object_instance_graph_identity_id=canonical_oigi_id,
        object_instance_graph_id=object_instance_graph_id,
        graph_hash_post=graph_hash_post,
    )

    assert await store.put_commit_file(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit=legacy_commit,
    )

    with pytest.raises(ValueError, match="Existing OIG commit body differs"):
        await store.put_commit_file(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit=canonical_commit,
        )
    legacy_ref_id = stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=legacy_oigi_id,
        commit_id=commit_id,
    )
    assert await store.domain_commit_refs_for_object_instance_graph_commit_id(
        projection_hash=projection_hash,
        object_instance_graph_commit_id=legacy_ref_id,
    )
    canonical_ref_id = stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=canonical_oigi_id,
        commit_id=commit_id,
    )
    assert (
        await store.domain_commit_refs_for_object_instance_graph_commit_id(
            projection_hash=projection_hash,
            object_instance_graph_commit_id=canonical_ref_id,
        )
        == ()
    )


_SNAPSHOT_TEST_FQN = test_class_fqn("SnapshotStoreUser")


def _primitive_desc() -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(kind=Kind.primitive, child_links=[])


def _make_snapshot_ocg_opg(
    *,
    name_cfg: AttributeConfig,
) -> tuple[ObjectConfigGraph, ObjectProjectionGraph, ClassConfig]:
    user_cc = make_class_config(
        "SnapshotStoreUser",
        class_fqn=_SNAPSHOT_TEST_FQN,
        class_config_attribute_configs=[],
    )
    user_cc.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=user_cc.id,
            attribute_config=name_cfg,
            name=name_cfg.name,
            position=0,
        )
    ]
    ocg = ObjectConfigGraph(
        name="snapshot-store-test",
        description=None,
        hash="0",
        fqn_prefix="tests.meta",
        language=CodeLanguage.python,
        object_config_graph_nodes=[],
    )
    ocg.object_config_graph_nodes = [
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.class_,
            node_key=user_cc.class_fqn,
            class_config=user_cc,
            object_config_graph_id=ocg.id,
        )
    ]
    opg = ObjectProjectionGraph(
        name="snapshot-store-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash="state-row-sidecar",
        supports_virtual_build=True,
        object_config_graph_id=ocg.id,
        object_projection_graph_nodes=[],
        object_projection_graph_edges=[],
        object_projection_graph_relationships=[],
    )
    opg.object_projection_graph_nodes = [
        ObjectProjectionGraphNode(
            class_config_id=user_cc.id,
            object_projection_graph_id=opg.id,
            is_root=True,
            selection=ObjectProjectionGraphNodeSelection.one,
        )
    ]
    return ocg, opg, user_cc


def _make_snapshot_state_row_graph() -> ObjectInstanceGraph:
    name_cfg = make_attribute_config(
        owner_key=_SNAPSHOT_TEST_FQN,
        name="name",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    ocg, opg, user_cc = _make_snapshot_ocg_opg(name_cfg=name_cfg)
    return _make_snapshot_state_row_graph_with_users(
        ocg=ocg,
        opg=opg,
        user_cc=user_cc,
        graph_id=uuid4(),
        source_ids=(uuid4(),),
        names=("Ada",),
    )


def _make_snapshot_state_row_graph_with_users(
    *,
    ocg: ObjectConfigGraph,
    opg: ObjectProjectionGraph,
    user_cc: ClassConfig,
    graph_id: UUID,
    source_ids: tuple[UUID, ...],
    names: tuple[str, ...],
) -> ObjectInstanceGraph:
    assert len(source_ids) == len(names)

    class User(BaseORMModel):
        name: str

    class_instances = [
        build_class_instance(
            object_instance_graph_id=graph_id,
            class_config=user_cc,
            source=User(id=source_id, name=name),
        )
        for source_id, name in zip(source_ids, names, strict=True)
    ]
    graph = build_object_instance_graph_from_class_instances(
        name="snapshot-store-test",
        description="state row sidecar",
        object_config_graph_id=ocg.id,
        object_projection_graph_id=opg.id,
        root_class_instance=class_instances[0],
        class_instances=class_instances,
        class_instance_relationships=[],
        oig_id=graph_id,
    )
    graph.hash = build_commit_state_index(graph).compute_hash()
    return graph


def _raw_class_segments_for_graph(
    *,
    graph: ObjectInstanceGraph,
    state_index,
    witness_ref,
) -> tuple[ObjectInstanceGraphSnapshotStateRawClassSegment, ...]:
    class_rows_by_id = state_index.row_maps(
        include_relationship_keys=False,
    ).class_state_rows_by_id
    segment_refs_by_key = {
        segment.key: segment
        for segment in witness_ref.segments
        if segment.kind == "CLASS"
    }
    segments: list[ObjectInstanceGraphSnapshotStateRawClassSegment] = []
    for class_instance in graph.class_instances:
        assert class_instance.id is not None
        assert class_instance.class_config_id is not None
        rows = class_rows_by_id[class_instance.id]
        segment_ref = segment_refs_by_key[f"class:{class_instance.id}"]
        segments.append(
            ObjectInstanceGraphSnapshotStateRawClassSegment(
                class_instance_id=class_instance.id,
                class_config_id=class_instance.class_config_id,
                source_object_id=class_instance.source_object_id,
                rows_text="".join(
                    f"{row.kind}\t{row.key}\t{row.value}\n" for row in rows
                ),
                row_count=len(rows),
                row_hash=compute_commit_state_rows_hash(rows),
                snapshot_payload=cast(
                    dict[str, object],
                    class_instance.model_dump(mode="json", exclude_none=True),
                ),
                segment_ref=segment_ref,
            )
        )
    return tuple(segments)


def _snapshot_graph_meta(graph: ObjectInstanceGraph) -> dict[str, object]:
    root_source_object_id = graph.root_class_instance.source_object_id
    assert root_source_object_id is not None
    return {
        "id": graph.id,
        "key": graph.key,
        "name": graph.name,
        "description": graph.description,
        "object_projection_graph_id": graph.object_projection_graph_id,
        "root_class_instance_id": graph.root_class_instance_id,
        "root_source_object_id": root_source_object_id,
        "hash": graph.hash,
    }


def _make_commit(
    *,
    projection_hash: str,
    commit_id: UUID | None = None,
    object_instance_graph_identity_id: UUID | None = None,
    object_instance_graph_id: UUID | None = None,
    parent_commit_id: UUID | None = None,
    graph_hash_pre: str | None = None,
    graph_hash_post: str | None = None,
) -> ObjectInstanceGraphCommit:
    commit_id = commit_id or uuid4()
    object_instance_graph_identity_id = object_instance_graph_identity_id or uuid4()
    commit_parents = []
    if parent_commit_id is not None:
        commit_parents.append(
            CommitParent.model_construct(
                id=stable_commit_parent_id(
                    commit_id=commit_id,
                    parent_commit_id=parent_commit_id,
                ),
                commit_id=commit_id,
                parent_commit_id=parent_commit_id,
            )
        )
    return ObjectInstanceGraphCommit.model_construct(
        id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            commit_id=commit_id,
        ),
        commit=Commit.model_construct(
            id=commit_id,
            author_id=uuid4(),
            key=str(commit_id),
            created_at=datetime.now(UTC),
            status=CommitStatus.local,
            lane_id=uuid4(),
            commit_parents=commit_parents,
        ),
        object_instance_graph_key="service-package",
        object_instance_graph_name="service-package",
        object_instance_graph_description=None,
        root_class_config_id=uuid4(),
        root_source_object_id=uuid4(),
        graph_hash_post=graph_hash_post or f"sha256:{uuid4().hex}",
        graph_hash_pre=graph_hash_pre or "",
        projection_hash=projection_hash,
        source_language=CodeLanguage.python,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id or uuid4(),
        commit_id=commit_id,
        object_instance_graph_changes=[],
    )


def _record_from_commit(
    *,
    branch_id: UUID,
    projection_hash: str,
    commit: ObjectInstanceGraphCommit,
) -> ObjectInstanceGraphCommitBodyRecord:
    return ObjectInstanceGraphCommitBodyRecord(
        envelope=object_instance_graph_commit_envelope_from_commit(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit=commit,
        ),
        body=build_oig_commit_body(commit),
    )
