from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from uuid import UUID

from aware_meta.graph.instance.commit.fs_snapshot_store import FSSnapshotStore


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


__all__ = ("load_code_package_text_snapshot_payload_at_commit",)
