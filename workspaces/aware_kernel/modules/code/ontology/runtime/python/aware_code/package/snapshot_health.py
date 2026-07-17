from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from uuid import UUID

from aware_code.package.artifact_delta_plan import (
    CodePackageArtifactCurrentStateIndex,
)
from aware_code.package.snapshot_contract import (
    CODE_PACKAGE_ARTIFACT_STATE_INDEX_SCHEMA,
)
from aware_code.package.snapshot_index import (
    load_code_package_text_snapshot_source_object_state_index_selected,
    load_current_code_package_text_snapshot_index_payload_with_head,
)
from aware_code.package.snapshot_json import head_uuid, payload_int
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.fs_snapshot_store import FSSnapshotStore
from aware_meta.graph.instance.commit.state_snapshot_segments import (
    commit_state_witness_cursor_summary_from_payload,
)


@dataclass(frozen=True)
class CodePackageSelectedSnapshotHealthEvidence:
    code_package_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    graph_hash_post: str
    snapshot_fingerprint: str | None
    source_snapshot_fingerprint: str | None
    artifact_current_state: CodePackageArtifactCurrentStateIndex
    required_relative_paths: tuple[str, ...]


async def load_code_package_selected_snapshot_health_evidence(
    *,
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
    expected_head_commit_id: UUID | None = None,
    expected_object_instance_graph_commit_id: UUID | None = None,
    required_relative_paths: Iterable[str] = (),
    store: FSCommitStore | None = None,
) -> CodePackageSelectedSnapshotHealthEvidence | None:
    """Load exact-head health while hydrating only requested source paths."""

    commit_store = store or FSCommitStore()
    _head, payload = (
        await load_current_code_package_text_snapshot_index_payload_with_head(
            store=commit_store,
            branch_id=branch_id,
            projection_hash=projection_hash,
            code_package_id=code_package_id,
            include_sections=True,
            include_source_object_index=False,
        )
    )
    if payload is None:
        return None
    head_commit_id = head_uuid(payload, "head_commit_id")
    object_instance_graph_commit_id = head_uuid(
        payload,
        "object_instance_graph_commit_id",
    )
    if head_commit_id is None or object_instance_graph_commit_id is None:
        return None
    if (
        expected_head_commit_id is not None
        and head_commit_id != expected_head_commit_id
    ):
        return None
    if (
        expected_object_instance_graph_commit_id is not None
        and object_instance_graph_commit_id != expected_object_instance_graph_commit_id
    ):
        return None
    graph_hash_post = payload.get("graph_hash_post")
    if not isinstance(graph_hash_post, str) or not graph_hash_post:
        return None
    if not _snapshot_state_witness_is_healthy(
        payload=payload,
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=head_commit_id,
    ):
        return None
    artifact_state = payload.get("artifact_state_index")
    if not isinstance(artifact_state, Mapping):
        return None
    if artifact_state.get("schema") != CODE_PACKAGE_ARTIFACT_STATE_INDEX_SCHEMA:
        return None
    if artifact_state.get("code_package_id") != str(code_package_id):
        return None
    required_paths = tuple(
        sorted(
            {
                normalized
                for path in required_relative_paths
                for normalized in (str(path).strip().strip("/"),)
                if normalized
            }
        )
    )
    if required_paths and not _required_source_paths_are_healthy(
        store=commit_store,
        branch_id=branch_id,
        projection_hash=projection_hash,
        code_package_id=code_package_id,
        payload=payload,
        required_paths=required_paths,
    ):
        return None
    snapshot_fingerprint = _optional_text(payload.get("snapshot_fingerprint"))
    source_snapshot_fingerprint = _optional_text(
        payload.get("source_snapshot_fingerprint")
    )
    artifact_current_state = CodePackageArtifactCurrentStateIndex.from_payload(
        {
            **artifact_state,
            "current_state_status": "selected_snapshot_health",
            "code_package_id": str(code_package_id),
            "snapshot_fingerprint": snapshot_fingerprint,
            "source_snapshot_fingerprint": source_snapshot_fingerprint,
            "head_commit_id": str(head_commit_id),
            "object_instance_graph_commit_id": str(object_instance_graph_commit_id),
            "graph_hash_post": graph_hash_post,
        }
    )
    if artifact_current_state is None:
        return None
    return CodePackageSelectedSnapshotHealthEvidence(
        code_package_id=code_package_id,
        head_commit_id=head_commit_id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
        graph_hash_post=graph_hash_post,
        snapshot_fingerprint=snapshot_fingerprint,
        source_snapshot_fingerprint=source_snapshot_fingerprint,
        artifact_current_state=artifact_current_state,
        required_relative_paths=required_paths,
    )


def _required_source_paths_are_healthy(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
    payload: Mapping[str, object],
    required_paths: tuple[str, ...],
) -> bool:
    source_text_hash_index = payload.get("source_text_hash_index")
    if not isinstance(source_text_hash_index, Mapping):
        return False
    committed_paths: set[str] = set()
    for section_key in ("source_texts", "unparsed_texts"):
        rows = source_text_hash_index.get(section_key)
        if not isinstance(rows, list):
            return False
        for row in rows:
            if not isinstance(row, Mapping):
                return False
            relative_path = row.get("relative_path")
            if isinstance(relative_path, str) and relative_path:
                committed_paths.add(relative_path.strip().strip("/"))
    if not set(required_paths).issubset(committed_paths):
        return False
    selected_index = load_code_package_text_snapshot_source_object_state_index_selected(
        store=store,
        branch_id=branch_id,
        projection_hash=projection_hash,
        code_package_id=code_package_id,
        snapshot_index_payload=payload,
        relative_paths=frozenset(required_paths),
    )
    if selected_index is None:
        return False
    object_ids = {
        str(row.get("source_object_id"))
        for row in selected_index.get("objects", [])
        if isinstance(row, Mapping) and row.get("source_object_id") is not None
    }
    selected_paths: set[str] = set()
    for row in selected_index.get("path_source_object_index", []):
        if not isinstance(row, Mapping):
            return False
        relative_path = row.get("relative_path")
        source_object_ids = row.get("source_object_ids")
        if not isinstance(relative_path, str) or not isinstance(
            source_object_ids,
            list,
        ):
            return False
        if not source_object_ids or any(
            str(item) not in object_ids for item in source_object_ids
        ):
            return False
        selected_paths.add(relative_path.strip().strip("/"))
    return selected_paths == set(required_paths)


def _snapshot_state_witness_is_healthy(
    *,
    payload: Mapping[str, object],
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID,
) -> bool:
    raw_metadata = payload.get("state_snapshot")
    if not isinstance(raw_metadata, Mapping):
        return False
    metadata = {
        str(key): value for key, value in raw_metadata.items() if isinstance(key, str)
    }
    snapshot_store = FSSnapshotStore()
    if metadata.get("state_snapshot_kind") == "class_segment_index":
        expected_graph_hash = payload.get("graph_hash_post")
        if not isinstance(expected_graph_hash, str) or not expected_graph_hash:
            return False
        if _witness_cursor_metadata_matches(
            metadata=metadata,
            expected_graph_hash=expected_graph_hash,
        ):
            return True
        return (
            snapshot_store.snapshot_state_class_segment_index_metadata(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                expected_graph_hash=expected_graph_hash,
            )
            is not None
        )
    if not isinstance(metadata.get("state_snapshot_payload_sha256"), str):
        return False
    if not isinstance(metadata.get("state_snapshot_state_hash"), str):
        return False
    file_size = payload_int(metadata, "state_snapshot_file_size")
    file_mtime_ns = payload_int(metadata, "state_snapshot_file_mtime_ns")
    file_ctime_ns = payload_int(metadata, "state_snapshot_file_ctime_ns")
    if file_size is None or file_mtime_ns is None or file_ctime_ns is None:
        return False
    return snapshot_store.has_snapshot_state_rows_file_metadata(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        expected_file_size=file_size,
        expected_file_mtime_ns=file_mtime_ns,
        expected_file_ctime_ns=file_ctime_ns,
    )


def _witness_cursor_metadata_matches(
    *,
    metadata: Mapping[str, object],
    expected_graph_hash: str,
) -> bool:
    if metadata.get("state_snapshot_graph_hash_source") != "witness_cursor_hash":
        return False
    if metadata.get("state_snapshot_graph_hash") != expected_graph_hash:
        return False
    raw_cursor = metadata.get("state_snapshot_witness_cursor")
    if not isinstance(raw_cursor, Mapping):
        return False
    cursor = commit_state_witness_cursor_summary_from_payload(
        {str(key): value for key, value in raw_cursor.items() if isinstance(key, str)}
    )
    if cursor is None or cursor.cursor_hash != expected_graph_hash:
        return False
    row_count = payload_int(metadata, "state_snapshot_row_count")
    if row_count is not None and row_count != cursor.row_count:
        return False
    segment_count = payload_int(metadata, "state_snapshot_segment_count")
    return segment_count is None or segment_count == cursor.segment_count


def _optional_text(value: object) -> str | None:
    return value if isinstance(value, str) and value else None
