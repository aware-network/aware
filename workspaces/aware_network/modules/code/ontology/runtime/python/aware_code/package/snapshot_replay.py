from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import cast
from uuid import UUID

from aware_meta_ontology.class_.class_instance import ClassInstance

from aware_meta.graph.instance.commit.fs_snapshot_store import FSSnapshotStore
from aware_meta.graph.instance.commit.snapshot_state_rows import (
    ObjectInstanceGraphSnapshotStateSelection,
)
from aware_meta.graph.instance.commit.state_index import (
    CommitStateIndex,
    CommitStateRow,
    CommitStateRowKind,
)


async def load_code_package_text_snapshot_payload_at_commit(
    *,
    root_dir: Path | None = None,
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
    commit_id: UUID,
    object_instance_graph_id: UUID | None = None,
    graph_hash_post: str | None = None,
) -> dict[str, object] | None:
    """Load a CodePackage text snapshot from the committed state-row contract."""

    snapshot_store = FSSnapshotStore(root_dir=root_dir)
    payload = await snapshot_store.get_snapshot_state_rows(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        expected_object_instance_graph_id=object_instance_graph_id,
        expected_graph_hash=graph_hash_post,
    )
    if payload is None:
        payload = await _load_segmented_code_package_text_snapshot_payload(
            snapshot_store=snapshot_store,
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            expected_object_instance_graph_id=object_instance_graph_id,
            expected_graph_hash=graph_hash_post,
        )
    if payload is None:
        return None
    graph = _mapping(payload.get("graph"))
    if graph is None:
        return None
    try:
        root_source_object_id = UUID(str(graph["root_source_object_id"]))
        root_class_instance_id = UUID(str(graph["root_class_instance_id"]))
    except (KeyError, TypeError, ValueError):
        return None
    if root_source_object_id != code_package_id:
        return None
    root_class_instance = _root_class_instance(
        payload=payload,
        root_class_instance_id=root_class_instance_id,
        code_package_id=code_package_id,
    )
    if root_class_instance is None:
        return None
    return {
        str(key): value for key, value in payload.items() if isinstance(key, str)
    } | {"root_class_instance": root_class_instance}


async def load_code_package_text_snapshot_state_selection_at_commit(
    *,
    root_dir: Path | None = None,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID,
    class_instance_ids: Iterable[UUID],
    object_instance_graph_id: UUID | None = None,
    graph_hash_post: str | None = None,
    include_state_row_maps: bool = False,
) -> ObjectInstanceGraphSnapshotStateSelection | None:
    """Reconstruct a normal state selection from canonical segmented evidence."""

    snapshot_store = FSSnapshotStore(root_dir=root_dir)
    metadata = snapshot_store.snapshot_state_class_segment_index_metadata(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        expected_object_instance_graph_id=object_instance_graph_id,
        expected_graph_hash=graph_hash_post,
    )
    if metadata is None:
        return None
    all_class_instance_ids = tuple(
        UUID(segment.key.removeprefix("class:"))
        for segment in metadata.witness_ref.segments
        if segment.kind == "CLASS" and segment.key.startswith("class:")
    )
    if not all_class_instance_ids:
        return None
    if metadata.witness_cursor_summary is not None:
        raw_selection = await snapshot_store.get_snapshot_state_indexed_raw_class_segments_by_witness_cursor(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            class_instance_ids=all_class_instance_ids,
            expected_witness_cursor_summary=metadata.witness_cursor_summary,
            expected_object_instance_graph_id=metadata.object_instance_graph_id,
            expected_graph_hash=metadata.graph_hash,
        )
    else:
        raw_selection = await snapshot_store.get_snapshot_state_indexed_raw_class_segments_by_witness_ref(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            class_instance_ids=all_class_instance_ids,
            expected_witness_ref=metadata.witness_ref,
            expected_object_instance_graph_id=metadata.object_instance_graph_id,
            expected_graph_hash=metadata.graph_hash,
        )
    if raw_selection is None or set(raw_selection.class_segments_by_id) != set(
        all_class_instance_ids
    ):
        return None

    state_rows: list[CommitStateRow] = []
    relationships: list[dict[str, str]] = []
    for segment_ref in metadata.witness_ref.segments:
        if segment_ref.kind == "CLASS":
            if not segment_ref.key.startswith("class:"):
                return None
            class_instance_id = UUID(segment_ref.key.removeprefix("class:"))
            rows = _state_rows_from_text(
                raw_selection.class_segments_by_id[class_instance_id].rows_text
            )
            if rows is None:
                return None
            state_rows.extend(rows)
            continue
        if segment_ref.kind != "EDGE":
            continue
        relationship = _segmented_snapshot_relationship_payload(segment_ref.key)
        if relationship is None:
            return None
        relationships.append(relationship)
        state_rows.append(
            CommitStateRow(
                kind="EDGE",
                key=relationship["class_config_relationship_id"],
                value=(
                    f"{relationship['source_class_instance_id']}"
                    f"->{relationship['target_class_instance_id']}"
                ),
            )
        )
    rows = tuple(state_rows)
    state_index = CommitStateIndex(rows=rows)
    if (
        metadata.state_hash is not None
        and state_index.compute_hash() != metadata.state_hash
    ):
        return None

    class_instance_payloads = [
        dict(raw_selection.class_segments_by_id[class_instance_id].snapshot_payload)
        for class_instance_id in all_class_instance_ids
    ]
    selected_ids = set(class_instance_ids)
    class_instances_by_id: dict[UUID, ClassInstance] = {}
    try:
        for payload in class_instance_payloads:
            raw_id = payload.get("id")
            if not isinstance(raw_id, str) or UUID(raw_id) not in selected_ids:
                continue
            class_instance = ClassInstance.model_validate(payload)
            class_instances_by_id[class_instance.id] = class_instance
    except (TypeError, ValueError):
        return None

    payload = dict(metadata.payload)
    payload.update(
        {
            "branch_id": str(branch_id),
            "projection_hash": projection_hash,
            "commit_id": str(commit_id),
            "object_instance_graph_id": str(metadata.object_instance_graph_id),
            "graph_hash": metadata.graph_hash,
            "state_hash": state_index.compute_hash(),
            "class_instances": class_instance_payloads,
            "class_instance_relationships": relationships,
        }
    )
    return ObjectInstanceGraphSnapshotStateSelection(
        payload=payload,
        state_rows=rows,
        class_instances_by_id=class_instances_by_id,
        state_row_maps=state_index.row_maps() if include_state_row_maps else None,
    )


async def _load_segmented_code_package_text_snapshot_payload(
    *,
    snapshot_store: FSSnapshotStore,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID,
    expected_object_instance_graph_id: UUID | None,
    expected_graph_hash: str | None,
) -> dict[str, object] | None:
    metadata = snapshot_store.snapshot_state_class_segment_index_metadata(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        expected_object_instance_graph_id=expected_object_instance_graph_id,
        expected_graph_hash=expected_graph_hash,
    )
    if metadata is None:
        return None
    class_instance_ids = tuple(
        UUID(segment.key.removeprefix("class:"))
        for segment in metadata.witness_ref.segments
        if segment.kind == "CLASS" and segment.key.startswith("class:")
    )
    if not class_instance_ids:
        return None
    if metadata.witness_cursor_summary is not None:
        selection = await snapshot_store.get_snapshot_state_indexed_raw_class_segments_by_witness_cursor(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            class_instance_ids=class_instance_ids,
            expected_witness_cursor_summary=metadata.witness_cursor_summary,
            expected_object_instance_graph_id=metadata.object_instance_graph_id,
            expected_graph_hash=metadata.graph_hash,
        )
    else:
        selection = await snapshot_store.get_snapshot_state_indexed_raw_class_segments_by_witness_ref(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            class_instance_ids=class_instance_ids,
            expected_witness_ref=metadata.witness_ref,
            expected_object_instance_graph_id=metadata.object_instance_graph_id,
            expected_graph_hash=metadata.graph_hash,
        )
    if selection is None or set(selection.class_segments_by_id) != set(
        class_instance_ids
    ):
        return None
    graph = _mapping(metadata.payload.get("graph"))
    if graph is None:
        return None
    relationships = _segmented_snapshot_relationship_payloads(
        segment_keys=(segment.key for segment in metadata.witness_ref.segments),
    )
    if relationships is None:
        return None
    return {
        "branch_id": str(branch_id),
        "projection_hash": projection_hash,
        "commit_id": str(commit_id),
        "object_instance_graph_id": str(metadata.object_instance_graph_id),
        "graph_hash": metadata.graph_hash,
        "graph": dict(graph),
        "class_instances": [
            dict(selection.class_segments_by_id[class_instance_id].snapshot_payload)
            for class_instance_id in sorted(class_instance_ids, key=str)
        ],
        "class_instance_relationships": relationships,
    }


def _segmented_snapshot_relationship_payloads(
    *,
    segment_keys: Iterable[str],
) -> list[dict[str, str]] | None:
    relationships: list[dict[str, str]] = []
    for raw_key in segment_keys:
        key = str(raw_key)
        if not key.startswith("edge:"):
            continue
        relationship = _segmented_snapshot_relationship_payload(key)
        if relationship is None:
            return None
        relationships.append(relationship)
    return relationships


def _segmented_snapshot_relationship_payload(
    key: str,
) -> dict[str, str] | None:
    relationship_id, separator, endpoints = key.removeprefix("edge:").partition(":")
    source_id, arrow, target_id = endpoints.partition("->")
    if not key.startswith("edge:") or not separator or not arrow:
        return None
    try:
        UUID(relationship_id)
        UUID(source_id)
        UUID(target_id)
    except ValueError:
        return None
    return {
        "class_config_relationship_id": relationship_id,
        "source_class_instance_id": source_id,
        "target_class_instance_id": target_id,
    }


def _state_rows_from_text(rows_text: str) -> tuple[CommitStateRow, ...] | None:
    rows: list[CommitStateRow] = []
    try:
        for line in rows_text.splitlines():
            if not line:
                continue
            kind, key, value = line.split("\t", 2)
            if kind not in {"NODE", "ATTR", "EDGE"}:
                return None
            rows.append(
                CommitStateRow(
                    kind=cast(CommitStateRowKind, kind),
                    key=key,
                    value=value,
                )
            )
    except (TypeError, ValueError):
        return None
    return tuple(rows)


def _root_class_instance(
    *,
    payload: Mapping[str, object],
    root_class_instance_id: UUID,
    code_package_id: UUID,
) -> Mapping[str, object] | None:
    raw_instances = payload.get("class_instances")
    if not isinstance(raw_instances, list):
        return None
    for raw_instance in raw_instances:
        instance = _mapping(raw_instance)
        if instance is None:
            continue
        try:
            instance_id = UUID(str(instance.get("id")))
        except (TypeError, ValueError):
            continue
        if instance_id != root_class_instance_id:
            continue
        raw_source_object_id = instance.get("source_object_id")
        if raw_source_object_id is not None:
            try:
                if UUID(str(raw_source_object_id)) != code_package_id:
                    return None
            except (TypeError, ValueError):
                return None
        return instance
    return None


def _mapping(value: object) -> Mapping[str, object] | None:
    if not isinstance(value, Mapping):
        return None
    return {str(key): item for key, item in value.items() if isinstance(key, str)}


__all__ = (
    "load_code_package_text_snapshot_payload_at_commit",
    "load_code_package_text_snapshot_state_selection_at_commit",
)
