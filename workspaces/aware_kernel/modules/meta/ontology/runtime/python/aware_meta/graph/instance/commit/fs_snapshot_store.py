from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from uuid import UUID

from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_instance_relationship import (
    ClassInstanceRelationship,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_utils.logging import logger

from aware_meta.graph.instance.commit.contract import (
    JsonObject,
    ObjectInstanceGraphCommitGraphHashSource,
    ObjectInstanceGraphSnapshotHealthMetadata,
)
from aware_meta.graph.instance.commit.fs_backend import (
    _atomic_write,
    _atomic_write_rebuildable_sidecar,
    _coerce_json_object,
    _coerce_json_object_view,
    _dump_json,
    _file_sha256,
    _file_stat_payload,
    _resolve_aware_root,
    _resolve_oig_root,
    _try_read_json_object,
)
from aware_meta.graph.instance.commit.fs_session_cache import (
    _SnapshotStateRowsRead,
)
from aware_meta.graph.instance.commit.json_payload import (
    _json_mapping,
    _json_optional_int,
    _json_optional_string,
    _json_optional_uuid,
    _json_required_int,
    _json_required_list,
    _json_required_string,
    _json_required_uuid,
)
from aware_meta.graph.instance.commit.snapshot_state_rows import (
    OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_ROWS_PAYLOAD_HASH_ALGORITHM,
    ObjectInstanceGraphSnapshotStateSelection,
    _class_instance_relationship_snapshot_state_payload,
    _class_instance_snapshot_state_payload,
    _commit_state_rows_from_snapshot_payload,
    _commit_state_rows_read_from_snapshot_payload,
    _commit_state_rows_read_from_text,
    _snapshot_state_json_value,
    _snapshot_state_rows_payload_hash,
    _snapshot_state_rows_payload_write,
    _trusted_class_instance_from_snapshot_state_payload,
    _trusted_relationship_from_snapshot_state_payload,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.fs_runtime_state import (
    _SESSION_JSON_FILE_CACHE,
    _SESSION_SNAPSHOT_STATE_ROWS_READ_CACHE,
)
from aware_meta.graph.instance.commit.perf_trace import commit_perf_span
from aware_meta.graph.instance.commit.state_index import (
    CommitStateIndex,
    CommitStateRowMaps,
    build_commit_state_index,
    compute_commit_state_rows_hash,
)
from aware_meta.graph.instance.commit.state_snapshot_segments import (
    OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENTS_INDEX_VERSION,
    OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENTS_SCHEMA,
    OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_INDEX_SCHEMA,
    OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_INDEX_VERSION,
    OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_OVERLAY_INDEX_SCHEMA,
    OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_OVERLAY_INDEX_VERSION,
    OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_RECORD_SCHEMA,
    OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_RECORD_VERSION,
    OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_REF_INDEX_SCHEMA,
    OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_REF_INDEX_VERSION,
    ObjectInstanceGraphSnapshotStateClassSegment,
    ObjectInstanceGraphSnapshotStateClassSegmentSelection,
    ObjectInstanceGraphSnapshotStateRawClassSegment,
    ObjectInstanceGraphSnapshotStateRawClassSegmentCursorSelection,
    ObjectInstanceGraphSnapshotStateRawClassSegmentIndexSelection,
    ObjectInstanceGraphSnapshotStateRawClassSegmentSelection,
    ObjectInstanceGraphSnapshotStateSegmentIndexMetadata,
    ObjectInstanceGraphSnapshotStateWitnessMetadata,
    commit_state_witness_cursor_chunk_from_payload as _commit_state_witness_cursor_chunk_from_payload,
    commit_state_witness_cursor_chunk_payload as _commit_state_witness_cursor_chunk_payload,
    commit_state_witness_cursor_summary_from_payload as _commit_state_witness_cursor_summary_from_payload,
    commit_state_witness_cursor_summary_payload as _commit_state_witness_cursor_summary_payload,
    commit_state_class_rows_by_raw_id as _commit_state_class_rows_by_raw_id,
    commit_state_rows_snapshot_state_text as _commit_state_rows_snapshot_state_text,
    commit_state_rows_text_hash_and_count as _commit_state_rows_text_hash_and_count,
    commit_state_segment_ref_from_payload as _commit_state_segment_ref_from_payload,
    commit_state_segment_ref_payload as _commit_state_segment_ref_payload,
    commit_state_witness_ref_payload as _commit_state_witness_ref_payload,
    commit_state_witness_ref_summary_payload as _commit_state_witness_ref_summary_payload,
    raw_class_segment_from_payload as _raw_class_segment_from_payload,
    raw_class_segment_record_data as _raw_class_segment_record_data,
    snapshot_state_segment_index_metadata_from_payload as _snapshot_state_segment_index_metadata_from_payload,
)
from aware_meta.graph.instance.commit.state_witness import (
    COMMIT_STATE_WITNESS_SCHEMA,
    CommitStateWitnessCursorChunk,
    CommitStateWitnessCursorChunkSummary,
    CommitStateSegmentRef,
    CommitStateWitnessCursorSummary,
    CommitStateWitnessRef,
    build_commit_state_witness_ref,
    replace_existing_commit_state_witness_ref_segments,
    validate_commit_state_witness_ref,
)

OBJECT_INSTANCE_GRAPH_SNAPSHOT_HEALTH_INDEX_VERSION = 1
OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_ROWS_INDEX_VERSION = 2
OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_ROWS_SCHEMA = "aware.oig.snapshot_state_rows.v2"
OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_WITNESS_INDEX_VERSION = 1
OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_WITNESS_SCHEMA = (
    "aware.oig.snapshot_state_witness.v1"
)
_OIG_SNAPSHOT_STORE_TRACE_CATEGORY = "meta.oig_snapshot_store"
_SNAPSHOT_STATE_CLASS_SEGMENT_OVERLAY_MAX_DEPTH = 64
_SNAPSHOT_STATE_CLASS_SEGMENT_CURSOR_CHUNK_SIDECAR_VERSION = 1
_SNAPSHOT_STATE_CLASS_SEGMENT_CURSOR_CHUNK_SIDECAR_SCHEMA = (
    "aware.oig.snapshot_state_class_segment_cursor_chunk_sidecar.v1"
)
_SNAPSHOT_STATE_CLASS_SEGMENT_CURSOR_KEY_INDEX_SIDECAR_VERSION = 1
_SNAPSHOT_STATE_CLASS_SEGMENT_CURSOR_KEY_INDEX_SIDECAR_SCHEMA = (
    "aware.oig.snapshot_state_class_segment_cursor_key_index_sidecar.v1"
)
_SNAPSHOT_STATE_CLASS_SEGMENT_ENVELOPE_SIDECAR_VERSION = 1
_SNAPSHOT_STATE_CLASS_SEGMENT_ENVELOPE_SIDECAR_SCHEMA = (
    "aware.oig.snapshot_state_class_segment_envelope_sidecar.v1"
)


@dataclass(frozen=True, slots=True)
class _CursorSelectedSegmentRead:
    payload: JsonObject
    object_instance_graph_id: UUID
    graph_hash: str
    cursor_summary: CommitStateWitnessCursorSummary
    class_segments_by_id: Mapping[UUID, ObjectInstanceGraphSnapshotStateRawClassSegment]
    cursor_chunks_by_index: Mapping[int, CommitStateWitnessCursorChunk]
    segment_refs_by_key: Mapping[str, CommitStateSegmentRef]
    chunk_summaries_by_segment_key: Mapping[str, CommitStateWitnessCursorChunkSummary]


def _snapshot_trace_metadata(
    *,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID | None,
    walk_depth: int | None = None,
) -> dict[str, object]:
    metadata: dict[str, object] = {
        "branch_id": str(branch_id),
        "projection_hash": projection_hash,
        "commit_id": str(commit_id) if commit_id is not None else None,
    }
    if walk_depth is not None:
        metadata["walk_depth"] = walk_depth
    return metadata


def _snapshot_state_class_segment_cursor_key_index_bucket(raw_id: str) -> str | None:
    try:
        UUID(raw_id)
    except Exception:
        return None
    return raw_id[0].lower()


def _snapshot_state_witness_metadata_from_payload(
    payload: JsonObject,
) -> ObjectInstanceGraphSnapshotStateWitnessMetadata | None:
    try:
        state_hash = _json_required_string(payload, "state_hash")
        segments = tuple(
            _commit_state_segment_ref_from_payload(item)
            for item in _json_required_list(payload, "segments")
        )
        witness_ref = CommitStateWitnessRef(
            schema=_json_required_string(payload, "commit_state_witness_schema"),
            state_hash=state_hash,
            witness_hash=_json_required_string(payload, "witness_hash"),
            row_count=_json_required_int(payload, "row_count"),
            segments=segments,
        )
        if not validate_commit_state_witness_ref(witness_ref):
            return None
        return ObjectInstanceGraphSnapshotStateWitnessMetadata(
            payload=payload,
            object_instance_graph_id=_json_required_uuid(
                payload,
                "object_instance_graph_id",
            ),
            graph_hash=_json_required_string(payload, "graph_hash"),
            state_hash=state_hash,
            witness_hash=witness_ref.witness_hash,
            row_count=witness_ref.row_count,
            node_count=_json_required_int(payload, "node_count"),
            attribute_count=_json_required_int(payload, "attribute_count"),
            edge_count=_json_required_int(payload, "edge_count"),
            state_rows_payload_sha256=_json_required_string(
                payload,
                "state_rows_payload_sha256",
            ),
            state_rows_file_size=_json_required_int(
                payload,
                "state_rows_file_size",
            ),
            state_rows_file_mtime_ns=_json_required_int(
                payload,
                "state_rows_file_mtime_ns",
            ),
            state_rows_file_ctime_ns=_json_required_int(
                payload,
                "state_rows_file_ctime_ns",
            ),
            witness_ref=witness_ref,
        )
    except Exception:
        return None


class FSSnapshotStore:
    """Filesystem-backed snapshot + index store per `(branch_id, projection_hash, commit_id)`."""

    _aware_root: Path
    _oig_root: Path

    def __init__(self, *, root_dir: Path | None = None) -> None:
        self._aware_root = _resolve_aware_root(root_dir)
        self._oig_root = _resolve_oig_root(root_dir)

    @property
    def aware_root(self) -> Path:
        return self._aware_root

    def _lane_dir(self, branch_id: UUID, projection_hash: str) -> Path:
        return self._oig_root / str(branch_id) / projection_hash

    def _snapshot_health_index_path(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> Path:
        return (
            self._lane_dir(branch_id, projection_hash)
            / "indexes"
            / "snapshot_health"
            / f"{commit_id}.json"
        )

    def _snapshot_state_rows_index_path(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> Path:
        return (
            self._lane_dir(branch_id, projection_hash)
            / "indexes"
            / "snapshot_state_rows"
            / f"{commit_id}.json"
        )

    def _snapshot_state_witness_index_path(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> Path:
        return (
            self._lane_dir(branch_id, projection_hash)
            / "indexes"
            / "snapshot_state_witness"
            / f"{commit_id}.json"
        )

    def _snapshot_state_class_segments_index_path(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> Path:
        return (
            self._lane_dir(branch_id, projection_hash)
            / "indexes"
            / "snapshot_state_class_segments"
            / f"{commit_id}.json"
        )

    def _snapshot_state_class_segment_index_dir(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> Path:
        return (
            self._lane_dir(branch_id, projection_hash)
            / "indexes"
            / "snapshot_state_class_segment_index"
            / str(commit_id)
        )

    def _snapshot_state_class_segment_index_path(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> Path:
        return (
            self._snapshot_state_class_segment_index_dir(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
            )
            / "manifest.json"
        )

    def _snapshot_state_class_segment_blob_path(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> Path:
        return (
            self._snapshot_state_class_segment_index_dir(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
            )
            / "segments.jsonl"
        )

    def _snapshot_state_class_segment_envelope_sidecar_path(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> Path:
        return (
            self._snapshot_state_class_segment_index_dir(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
            )
            / "envelope.json"
        )

    def _snapshot_state_class_segment_cursor_chunk_sidecar_path(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        chunk_index: int,
    ) -> Path:
        return (
            self._snapshot_state_class_segment_index_dir(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
            )
            / "cursor_chunks"
            / f"{chunk_index}.json"
        )

    def _snapshot_state_class_segment_cursor_key_index_sidecar_path(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        bucket_key: str,
    ) -> Path:
        return (
            self._snapshot_state_class_segment_index_dir(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
            )
            / "cursor_key_index"
            / f"{bucket_key}.json"
        )

    def has_snapshot(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> bool:
        return (
            self._lane_dir(branch_id, projection_hash)
            / "snapshots"
            / f"{commit_id}.json"
        ).exists()

    def snapshot_state_rows_file_metadata(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> JsonObject | None:
        path = self._snapshot_state_rows_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        if not path.exists():
            return None
        file_size, file_mtime_ns, file_ctime_ns = _file_stat_payload(path)
        return {
            "state_snapshot_file_size": file_size,
            "state_snapshot_file_mtime_ns": file_mtime_ns,
            "state_snapshot_file_ctime_ns": file_ctime_ns,
        }

    def has_snapshot_state_rows_file_metadata(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        expected_file_size: int | None,
        expected_file_mtime_ns: int | None,
        expected_file_ctime_ns: int | None,
    ) -> bool:
        metadata = self.snapshot_state_rows_file_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        if metadata is None:
            return False
        return (
            metadata.get("state_snapshot_file_size") == expected_file_size
            and metadata.get("state_snapshot_file_mtime_ns") == expected_file_mtime_ns
            and metadata.get("state_snapshot_file_ctime_ns") == expected_file_ctime_ns
        )

    def _write_snapshot_health_index(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        oig: ObjectInstanceGraph,
    ) -> None:
        snapshot_path = (
            self._lane_dir(branch_id, projection_hash)
            / "snapshots"
            / f"{commit_id}.json"
        )
        if not snapshot_path.exists():
            return
        file_size, file_mtime_ns, file_ctime_ns = _file_stat_payload(snapshot_path)
        payload: JsonObject = {
            "v": OBJECT_INSTANCE_GRAPH_SNAPSHOT_HEALTH_INDEX_VERSION,
            "branch_id": str(branch_id),
            "projection_hash": projection_hash,
            "commit_id": str(commit_id),
            "object_instance_graph_id": str(oig.id),
            "graph_hash": str(oig.hash or ""),
            "file_size": file_size,
            "file_mtime_ns": file_mtime_ns,
            "file_ctime_ns": file_ctime_ns,
            "file_sha256": _file_sha256(snapshot_path),
        }
        path = self._snapshot_health_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        if path.exists():
            existing_payload = _try_read_json_object(
                path,
                log_prefix=f"Existing OIG snapshot health index is unreadable: {path}",
            )
            if existing_payload == payload:
                return
        _atomic_write(path, _dump_json(payload))
        _SESSION_JSON_FILE_CACHE.invalidate_path(path)

    def _snapshot_state_rows_payload(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        oig: ObjectInstanceGraph,
        snapshot_payload: JsonObject | None = None,
        include_snapshot_file_metadata: bool = True,
    ) -> JsonObject | None:
        snapshot_path = (
            self._lane_dir(branch_id, projection_hash)
            / "snapshots"
            / f"{commit_id}.json"
        )
        graph_payload = snapshot_payload
        if graph_payload is None:
            graph_payload = _coerce_json_object(
                oig.model_dump(mode="json", exclude_none=True),
                error_message=(
                    "ObjectInstanceGraph snapshot did not serialize to a JSON object"
                ),
            )
        class_instances = graph_payload.get("class_instances")
        relationships = graph_payload.get("class_instance_relationships")
        if not isinstance(class_instances, list) or not isinstance(
            relationships,
            list,
        ):
            return None
        snapshot_file_metadata: JsonObject = {}
        if include_snapshot_file_metadata and snapshot_path.exists():
            file_size, file_mtime_ns, file_ctime_ns = _file_stat_payload(snapshot_path)
            snapshot_file_metadata = {
                "snapshot_file_size": file_size,
                "snapshot_file_mtime_ns": file_mtime_ns,
                "snapshot_file_ctime_ns": file_ctime_ns,
            }
        state_index = build_commit_state_index(oig)
        graph_meta_keys = (
            "id",
            "key",
            "name",
            "description",
            "object_projection_graph_id",
            "root_class_instance_id",
            "root_source_object_id",
            "hash",
        )
        graph_meta: JsonObject = {
            key: value
            for key in graph_meta_keys
            if (value := graph_payload.get(key)) is not None
        }
        root_source_object_id = getattr(oig, "root_source_object_id", None)
        if root_source_object_id is None:
            root_class_instance = getattr(oig, "root_class_instance", None)
            root_source_object_id = getattr(
                root_class_instance,
                "source_object_id",
                None,
            )
        if isinstance(root_source_object_id, UUID):
            graph_meta["root_source_object_id"] = str(root_source_object_id)
        payload: JsonObject = {
            "v": OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_ROWS_INDEX_VERSION,
            "schema": OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_ROWS_SCHEMA,
            "branch_id": str(branch_id),
            "projection_hash": projection_hash,
            "commit_id": str(commit_id),
            "object_instance_graph_id": str(oig.id),
            "graph_hash": str(oig.hash or ""),
            "graph": graph_meta,
            "class_instances": class_instances,
            "class_instance_relationships": relationships,
            "state_rows_text": _commit_state_rows_snapshot_state_text(
                state_index.rows,
            ),
            "state_hash": state_index.compute_hash(),
            "node_count": state_index.node_count,
            "attribute_count": state_index.attribute_count,
            "edge_count": state_index.edge_count,
            **snapshot_file_metadata,
        }
        return payload

    def _snapshot_state_rows_payload_from_parts(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        object_instance_graph_id: UUID,
        graph_hash: str,
        graph_meta: Mapping[str, object],
        class_instances: Iterable[ClassInstance],
        class_instance_relationships: Iterable[ClassInstanceRelationship],
        state_index: CommitStateIndex,
    ) -> JsonObject:
        state_hash = state_index.compute_hash()
        if graph_hash != state_hash:
            raise ValueError(
                "OIG state snapshot rows require graph_hash to match "
                f"state rows hash: graph_hash={graph_hash} state_hash={state_hash}"
            )
        graph_payload: JsonObject = {
            str(key): _snapshot_state_json_value(value)
            for key, value in graph_meta.items()
            if value is not None
        }
        graph_payload["id"] = str(object_instance_graph_id)
        graph_payload["hash"] = graph_hash
        class_instance_payloads = [
            _class_instance_snapshot_state_payload(class_instance)
            for class_instance in sorted(
                class_instances,
                key=lambda item: str(getattr(item, "id", "")),
            )
        ]
        relationship_payloads = [
            _class_instance_relationship_snapshot_state_payload(relationship)
            for relationship in sorted(
                class_instance_relationships,
                key=lambda item: (
                    str(getattr(item, "class_config_relationship_id", "")),
                    str(getattr(item, "source_class_instance_id", "")),
                    str(getattr(item, "target_class_instance_id", "")),
                ),
            )
        ]
        payload: JsonObject = {
            "v": OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_ROWS_INDEX_VERSION,
            "schema": OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_ROWS_SCHEMA,
            "branch_id": str(branch_id),
            "projection_hash": projection_hash,
            "commit_id": str(commit_id),
            "object_instance_graph_id": str(object_instance_graph_id),
            "graph_hash": graph_hash,
            "graph": graph_payload,
            "class_instances": class_instance_payloads,
            "class_instance_relationships": relationship_payloads,
            "state_rows_text": _commit_state_rows_snapshot_state_text(
                state_index.rows,
            ),
            "state_hash": state_hash,
            "node_count": state_index.node_count,
            "attribute_count": state_index.attribute_count,
            "edge_count": state_index.edge_count,
        }
        return payload

    def _snapshot_state_rows_payload_from_payloads(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        object_instance_graph_id: UUID,
        graph_hash: str,
        graph_meta: Mapping[str, object],
        class_instance_payloads: Iterable[Mapping[str, object]],
        class_instances: Iterable[ClassInstance],
        class_instance_relationships: Iterable[ClassInstanceRelationship],
        state_index: CommitStateIndex,
    ) -> JsonObject:
        state_hash = state_index.compute_hash()
        if graph_hash != state_hash:
            raise ValueError(
                "OIG state snapshot rows require graph_hash to match "
                f"state rows hash: graph_hash={graph_hash} state_hash={state_hash}"
            )
        graph_payload: JsonObject = {
            str(key): _snapshot_state_json_value(value)
            for key, value in graph_meta.items()
            if value is not None
        }
        graph_payload["id"] = str(object_instance_graph_id)
        graph_payload["hash"] = graph_hash

        class_payloads_by_id: dict[str, JsonObject] = {}
        expected_object_instance_graph_id = str(object_instance_graph_id)
        for raw_payload in class_instance_payloads:
            class_payload = _coerce_json_object_view(
                raw_payload,
                error_message="ClassInstance state snapshot payload must be a JSON object",
            )
            class_instance_id = _json_required_string(class_payload, "id")
            payload_graph_id = _json_required_string(
                class_payload,
                "object_instance_graph_id",
            )
            if payload_graph_id != expected_object_instance_graph_id:
                raise ValueError(
                    "ClassInstance state snapshot payload graph mismatch: "
                    f"class_instance_id={class_instance_id} "
                    f"expected={expected_object_instance_graph_id} "
                    f"actual={payload_graph_id}"
                )
            class_payloads_by_id[class_instance_id] = class_payload
        for class_instance in class_instances:
            class_payload = _class_instance_snapshot_state_payload(class_instance)
            class_instance_id = _json_required_string(class_payload, "id")
            payload_graph_id = _json_required_uuid(
                class_payload,
                "object_instance_graph_id",
            )
            if payload_graph_id != object_instance_graph_id:
                raise ValueError(
                    "ClassInstance state snapshot payload graph mismatch: "
                    f"class_instance_id={class_instance_id} "
                    f"expected={object_instance_graph_id} actual={payload_graph_id}"
                )
            class_payloads_by_id[class_instance_id] = class_payload

        relationship_payloads = [
            _class_instance_relationship_snapshot_state_payload(relationship)
            for relationship in sorted(
                class_instance_relationships,
                key=lambda item: (
                    str(getattr(item, "class_config_relationship_id", "")),
                    str(getattr(item, "source_class_instance_id", "")),
                    str(getattr(item, "target_class_instance_id", "")),
                ),
            )
        ]
        payload: JsonObject = {
            "v": OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_ROWS_INDEX_VERSION,
            "schema": OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_ROWS_SCHEMA,
            "branch_id": str(branch_id),
            "projection_hash": projection_hash,
            "commit_id": str(commit_id),
            "object_instance_graph_id": str(object_instance_graph_id),
            "graph_hash": graph_hash,
            "graph": graph_payload,
            "class_instances": [
                payload
                for _class_instance_id, payload in sorted(
                    class_payloads_by_id.items(),
                )
            ],
            "class_instance_relationships": relationship_payloads,
            "state_rows_text": _commit_state_rows_snapshot_state_text(
                state_index.rows,
            ),
            "state_hash": state_hash,
            "node_count": state_index.node_count,
            "attribute_count": state_index.attribute_count,
            "edge_count": state_index.edge_count,
        }
        return payload

    def _snapshot_state_witness_payload(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        object_instance_graph_id: UUID,
        graph_hash: str,
        state_index: CommitStateIndex,
        state_rows_payload: JsonObject,
        state_rows_path: Path,
    ) -> JsonObject:
        state_rows_payload_sha256 = _json_required_string(
            state_rows_payload,
            "payload_sha256",
        )
        file_size, file_mtime_ns, file_ctime_ns = _file_stat_payload(state_rows_path)
        witness_ref = build_commit_state_witness_ref(state_index)
        if graph_hash != witness_ref.state_hash:
            raise ValueError(
                "OIG snapshot state witness requires graph_hash to match "
                f"state hash: graph_hash={graph_hash} "
                f"state_hash={witness_ref.state_hash}"
            )
        return {
            "v": OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_WITNESS_INDEX_VERSION,
            "schema": OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_WITNESS_SCHEMA,
            "branch_id": str(branch_id),
            "projection_hash": projection_hash,
            "commit_id": str(commit_id),
            "object_instance_graph_id": str(object_instance_graph_id),
            "graph_hash": graph_hash,
            "commit_state_witness_schema": COMMIT_STATE_WITNESS_SCHEMA,
            "state_hash": witness_ref.state_hash,
            "witness_hash": witness_ref.witness_hash,
            "row_count": witness_ref.row_count,
            "node_count": state_index.node_count,
            "attribute_count": state_index.attribute_count,
            "edge_count": state_index.edge_count,
            "state_rows_payload_sha256": state_rows_payload_sha256,
            "state_rows_file_size": file_size,
            "state_rows_file_mtime_ns": file_mtime_ns,
            "state_rows_file_ctime_ns": file_ctime_ns,
            "segment_count": len(witness_ref.segments),
            "segments": [
                _commit_state_segment_ref_payload(segment)
                for segment in witness_ref.segments
            ],
        }

    def _write_snapshot_state_witness_index(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        object_instance_graph_id: UUID,
        graph_hash: str,
        state_index: CommitStateIndex,
        state_rows_payload: JsonObject,
        state_rows_path: Path,
    ) -> None:
        trace_metadata = _snapshot_trace_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        with commit_perf_span(
            phase="oig_snapshot_store.state_witness.build_payload",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            payload = self._snapshot_state_witness_payload(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                object_instance_graph_id=object_instance_graph_id,
                graph_hash=graph_hash,
                state_index=state_index,
                state_rows_payload=state_rows_payload,
                state_rows_path=state_rows_path,
            )
        path = self._snapshot_state_witness_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        with commit_perf_span(
            phase="oig_snapshot_store.state_witness.write_payload",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            if path.exists():
                existing_payload = _try_read_json_object(
                    path,
                    log_prefix=(
                        "Existing OIG snapshot state witness index is unreadable: "
                        f"{path}"
                    ),
                )
                if existing_payload == payload:
                    return
            _atomic_write_rebuildable_sidecar(path, _dump_json(payload))
            _SESSION_JSON_FILE_CACHE.invalidate_path(path)

    def _write_snapshot_state_witness_index_from_rows_payload(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        state_rows_payload: JsonObject,
        state_rows_path: Path,
    ) -> None:
        state_rows = _commit_state_rows_from_snapshot_payload(state_rows_payload)
        if state_rows is None:
            return
        object_instance_graph_id = _json_optional_uuid(
            state_rows_payload,
            "object_instance_graph_id",
        )
        graph_hash = _json_optional_string(state_rows_payload, "graph_hash")
        if object_instance_graph_id is None or graph_hash is None:
            return
        self._write_snapshot_state_witness_index(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            object_instance_graph_id=object_instance_graph_id,
            graph_hash=graph_hash,
            state_index=CommitStateIndex(rows=state_rows),
            state_rows_payload=state_rows_payload,
            state_rows_path=state_rows_path,
        )

    def _snapshot_state_class_segments_payload(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        object_instance_graph_id: UUID,
        graph_hash: str,
        state_index: CommitStateIndex,
        state_rows_payload: JsonObject,
        state_rows_path: Path,
    ) -> JsonObject:
        witness_payload = self._snapshot_state_witness_payload(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            object_instance_graph_id=object_instance_graph_id,
            graph_hash=graph_hash,
            state_index=state_index,
            state_rows_payload=state_rows_payload,
            state_rows_path=state_rows_path,
        )
        witness_metadata = _snapshot_state_witness_metadata_from_payload(
            witness_payload
        )
        if witness_metadata is None:
            raise ValueError("OIG snapshot class segments require valid witness")
        segment_refs_by_key = {
            segment.key: segment for segment in witness_metadata.witness_ref.segments
        }
        class_payloads = state_rows_payload.get("class_instances")
        if not isinstance(class_payloads, list):
            raise ValueError("OIG snapshot class segments require class payloads")
        class_payloads_by_id: dict[str, JsonObject] = {}
        for raw_payload in class_payloads:
            class_payload = _coerce_json_object_view(
                raw_payload,
                error_message="Class segment payload must be a JSON object",
            )
            class_instance_id = _json_required_string(class_payload, "id")
            class_payloads_by_id[class_instance_id] = class_payload

        class_segments: list[JsonObject] = []
        for raw_class_instance_id, rows in sorted(
            _commit_state_class_rows_by_raw_id(state_index.rows).items(),
        ):
            if not rows or rows[0].kind != "NODE":
                raise ValueError(
                    "OIG snapshot class segment missing NODE row: "
                    f"class_instance_id={raw_class_instance_id}"
                )
            segment_key = f"class:{raw_class_instance_id}"
            segment_ref = segment_refs_by_key.get(segment_key)
            if segment_ref is None:
                raise ValueError(
                    "OIG snapshot class segment missing witness segment: "
                    f"class_instance_id={raw_class_instance_id}"
                )
            class_payload = class_payloads_by_id.get(raw_class_instance_id)
            if class_payload is None:
                raise ValueError(
                    "OIG snapshot class segment missing class payload: "
                    f"class_instance_id={raw_class_instance_id}"
                )
            class_segments.append(
                {
                    "class_instance_id": raw_class_instance_id,
                    "class_config_id": rows[0].key,
                    "source_object_id": class_payload.get("source_object_id"),
                    "rows_text": _commit_state_rows_snapshot_state_text(rows),
                    "segment": _commit_state_segment_ref_payload(segment_ref),
                    "snapshot_payload": class_payload,
                }
            )

        return {
            "v": OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENTS_INDEX_VERSION,
            "schema": OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENTS_SCHEMA,
            "branch_id": str(branch_id),
            "projection_hash": projection_hash,
            "commit_id": str(commit_id),
            "object_instance_graph_id": str(object_instance_graph_id),
            "graph_hash": graph_hash,
            "state_witness": witness_payload,
            "class_segment_count": len(class_segments),
            "class_segments": class_segments,
        }

    def _write_snapshot_state_class_segments_index(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        object_instance_graph_id: UUID,
        graph_hash: str,
        state_index: CommitStateIndex,
        state_rows_payload: JsonObject,
        state_rows_path: Path,
    ) -> None:
        trace_metadata = _snapshot_trace_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        with commit_perf_span(
            phase="oig_snapshot_store.state_class_segments.build_payload",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            payload = self._snapshot_state_class_segments_payload(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                object_instance_graph_id=object_instance_graph_id,
                graph_hash=graph_hash,
                state_index=state_index,
                state_rows_payload=state_rows_payload,
                state_rows_path=state_rows_path,
            )
        path = self._snapshot_state_class_segments_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        with commit_perf_span(
            phase="oig_snapshot_store.state_class_segments.write_payload",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            if path.exists():
                existing_payload = _try_read_json_object(
                    path,
                    log_prefix=(
                        "Existing OIG snapshot state class segment index is "
                        f"unreadable: {path}"
                    ),
                )
                if existing_payload == payload:
                    return
            _atomic_write_rebuildable_sidecar(path, _dump_json(payload))
            _SESSION_JSON_FILE_CACHE.invalidate_path(path)

    def _snapshot_state_class_segment_index_payload(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        object_instance_graph_id: UUID,
        graph_hash: str,
        state_index: CommitStateIndex,
        state_rows_payload: JsonObject,
        state_rows_path: Path,
    ) -> tuple[JsonObject, str]:
        witness_payload = self._snapshot_state_witness_payload(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            object_instance_graph_id=object_instance_graph_id,
            graph_hash=graph_hash,
            state_index=state_index,
            state_rows_payload=state_rows_payload,
            state_rows_path=state_rows_path,
        )
        witness_metadata = _snapshot_state_witness_metadata_from_payload(
            witness_payload
        )
        if witness_metadata is None:
            raise ValueError("OIG snapshot class segment index requires valid witness")
        class_payloads = state_rows_payload.get("class_instances")
        if not isinstance(class_payloads, list):
            raise ValueError("OIG snapshot class segment index requires class payloads")
        class_payloads_by_id: dict[str, JsonObject] = {}
        for raw_payload in class_payloads:
            class_payload = _coerce_json_object_view(
                raw_payload,
                error_message="Class segment record payload must be a JSON object",
            )
            class_instance_id = _json_required_string(class_payload, "id")
            class_payloads_by_id[class_instance_id] = class_payload

        class_segment_refs: list[JsonObject] = []
        segment_records: list[str] = []
        byte_offset = 0
        class_rows_by_raw_id = _commit_state_class_rows_by_raw_id(state_index.rows)
        for segment_ref in witness_metadata.witness_ref.segments:
            if segment_ref.kind != "CLASS":
                continue
            raw_class_instance_id = segment_ref.key.removeprefix("class:")
            rows = class_rows_by_raw_id.get(raw_class_instance_id)
            if not rows or rows[0].kind != "NODE":
                raise ValueError(
                    "OIG snapshot class segment record missing NODE row: "
                    f"class_instance_id={raw_class_instance_id}"
                )
            class_payload = class_payloads_by_id.get(raw_class_instance_id)
            if class_payload is None:
                raise ValueError(
                    "OIG snapshot class segment record missing class payload: "
                    f"class_instance_id={raw_class_instance_id}"
                )
            record_payload: JsonObject = {
                "v": OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_RECORD_VERSION,
                "schema": (
                    OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_RECORD_SCHEMA
                ),
                "class_instance_id": raw_class_instance_id,
                "class_config_id": rows[0].key,
                "source_object_id": class_payload.get("source_object_id"),
                "rows_text": _commit_state_rows_snapshot_state_text(rows),
                "segment": _commit_state_segment_ref_payload(segment_ref),
                "snapshot_payload": class_payload,
            }
            record_data = _dump_json(record_payload) + "\n"
            record_bytes = record_data.encode("utf-8")
            record_sha256 = hashlib.sha256(record_bytes).hexdigest()
            class_segment_refs.append(
                {
                    "class_instance_id": raw_class_instance_id,
                    "class_config_id": rows[0].key,
                    "source_object_id": class_payload.get("source_object_id"),
                    "segment": _commit_state_segment_ref_payload(segment_ref),
                    "byte_offset": byte_offset,
                    "byte_length": len(record_bytes),
                    "record_sha256": record_sha256,
                }
            )
            segment_records.append(record_data)
            byte_offset += len(record_bytes)

        segment_blob = "".join(segment_records)
        graph_payload = state_rows_payload.get("graph")
        graph_summary: JsonObject = {}
        if isinstance(graph_payload, Mapping):
            for key in (
                "id",
                "root_class_instance_id",
                "root_source_object_id",
                "hash",
            ):
                value = graph_payload.get(key)
                if value is not None:
                    graph_summary[key] = _snapshot_state_json_value(value)
        return (
            {
                "v": OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_INDEX_VERSION,
                "schema": (
                    OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_INDEX_SCHEMA
                ),
                "branch_id": str(branch_id),
                "projection_hash": projection_hash,
                "commit_id": str(commit_id),
                "object_instance_graph_id": str(object_instance_graph_id),
                "graph_hash": graph_hash,
                "graph": graph_summary,
                "state_witness": witness_payload,
                "segment_blob": {
                    "file_name": "segments.jsonl",
                    "byte_size": len(segment_blob.encode("utf-8")),
                    "sha256": hashlib.sha256(segment_blob.encode("utf-8")).hexdigest(),
                },
                "class_segment_count": len(class_segment_refs),
                "class_segments": class_segment_refs,
            },
            segment_blob,
        )

    def _write_snapshot_state_class_segment_index(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        object_instance_graph_id: UUID,
        graph_hash: str,
        state_index: CommitStateIndex,
        state_rows_payload: JsonObject,
        state_rows_path: Path,
    ) -> None:
        trace_metadata = _snapshot_trace_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        with commit_perf_span(
            phase="oig_snapshot_store.state_class_segment_index.build_payload",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            payload, segment_blob = self._snapshot_state_class_segment_index_payload(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                object_instance_graph_id=object_instance_graph_id,
                graph_hash=graph_hash,
                state_index=state_index,
                state_rows_payload=state_rows_payload,
                state_rows_path=state_rows_path,
            )
        manifest_path = self._snapshot_state_class_segment_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        blob_path = self._snapshot_state_class_segment_blob_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        with commit_perf_span(
            phase="oig_snapshot_store.state_class_segment_index.write_payload",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            if manifest_path.exists() and blob_path.exists():
                existing_payload = _try_read_json_object(
                    manifest_path,
                    log_prefix=(
                        "Existing OIG snapshot state class segment index is "
                        f"unreadable: {manifest_path}"
                    ),
                )
                try:
                    existing_blob = blob_path.read_text(encoding="utf-8")
                except Exception:
                    existing_blob = None
                if existing_payload == payload and existing_blob == segment_blob:
                    return
            _atomic_write_rebuildable_sidecar(blob_path, segment_blob)
            _atomic_write_rebuildable_sidecar(manifest_path, _dump_json(payload))
            _SESSION_JSON_FILE_CACHE.invalidate_path(manifest_path)

    async def put_state_snapshot_class_segment_index(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        object_instance_graph_id: UUID,
        graph_hash: str,
        post_witness_ref: CommitStateWitnessRef,
        class_segments: Iterable[ObjectInstanceGraphSnapshotStateRawClassSegment],
        graph_meta: Mapping[str, object] | None = None,
        graph_hash_source: ObjectInstanceGraphCommitGraphHashSource = "state_hash",
        state_witness_cursor_summary: CommitStateWitnessCursorSummary | None = None,
        state_witness_cursor_chunks: (
            Iterable[CommitStateWitnessCursorChunk] | None
        ) = None,
    ) -> JsonObject:
        if graph_hash_source == "state_hash":
            if post_witness_ref.state_hash is None:
                raise ValueError(
                    "OIG snapshot class segment index requires state_hash "
                    + "when graph_hash_source is state_hash"
                )
            expected_graph_hash = post_witness_ref.state_hash
        elif graph_hash_source == "witness_hash":
            expected_graph_hash = post_witness_ref.witness_hash
        elif graph_hash_source == "witness_cursor_hash":
            if state_witness_cursor_summary is None:
                raise ValueError(
                    "OIG snapshot class segment index requires "
                    + "state_witness_cursor_summary when graph_hash_source is "
                    + "witness_cursor_hash"
                )
            expected_graph_hash = state_witness_cursor_summary.cursor_hash
        else:
            raise ValueError(
                f"Unsupported graph_hash_source for class segment index: {graph_hash_source!r}"
            )
        if graph_hash != expected_graph_hash:
            raise ValueError(
                "OIG snapshot class segment index requires graph_hash to match "
                f"{graph_hash_source}: graph_hash={graph_hash} "
                f"expected={expected_graph_hash}"
            )
        if not validate_commit_state_witness_ref(post_witness_ref):
            raise ValueError("Invalid post-state witness ref")

        trace_metadata = _snapshot_trace_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        with commit_perf_span(
            phase="oig_snapshot_store.state_class_segment_ref_index.build_payload",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            segments_by_raw_id: dict[
                str,
                ObjectInstanceGraphSnapshotStateRawClassSegment,
            ] = {}
            for segment in class_segments:
                raw_class_instance_id = str(segment.class_instance_id)
                if raw_class_instance_id in segments_by_raw_id:
                    raise ValueError(
                        "Duplicate class segment: " f"{raw_class_instance_id}"
                    )
                segments_by_raw_id[raw_class_instance_id] = segment

            class_segment_refs: list[JsonObject] = []
            segment_blob_parts: list[bytes] = []
            byte_offset = 0
            for segment_ref in post_witness_ref.segments:
                if segment_ref.kind != "CLASS":
                    continue
                raw_class_instance_id = segment_ref.key.removeprefix("class:")
                segment = segments_by_raw_id.pop(raw_class_instance_id, None)
                if segment is None:
                    raise ValueError(
                        "OIG snapshot class segment index missing class segment: "
                        f"{raw_class_instance_id}"
                    )
                if segment.segment_ref != segment_ref:
                    raise ValueError(
                        "OIG snapshot class segment index witness ref mismatch: "
                        f"{raw_class_instance_id}"
                    )
                record_bytes = _raw_class_segment_record_data(segment).encode("utf-8")
                record_sha256 = hashlib.sha256(record_bytes).hexdigest()
                class_segment_refs.append(
                    {
                        "class_instance_id": raw_class_instance_id,
                        "class_config_id": str(segment.class_config_id),
                        "source_object_id": (
                            str(segment.source_object_id)
                            if segment.source_object_id is not None
                            else None
                        ),
                        "segment": _commit_state_segment_ref_payload(segment_ref),
                        "blob_commit_id": str(commit_id),
                        "byte_offset": byte_offset,
                        "byte_length": len(record_bytes),
                        "record_sha256": record_sha256,
                    }
                )
                segment_blob_parts.append(record_bytes)
                byte_offset += len(record_bytes)
            if segments_by_raw_id:
                raise ValueError(
                    "OIG snapshot class segment index received unused class segments: "
                    + ",".join(sorted(segments_by_raw_id))
                )
            if state_witness_cursor_summary is not None:
                self._validate_state_witness_cursor_summary_for_ref(
                    summary=state_witness_cursor_summary,
                    witness_ref=post_witness_ref,
                )
            cursor_chunks = tuple(state_witness_cursor_chunks or ())
            if cursor_chunks:
                self._validate_state_witness_cursor_chunks_for_summary(
                    chunks=cursor_chunks,
                    summary=state_witness_cursor_summary,
                )

            segment_blob_bytes = b"".join(segment_blob_parts)
            graph_summary = self._snapshot_state_class_segment_graph_summary(
                graph_meta=graph_meta,
                object_instance_graph_id=object_instance_graph_id,
                graph_hash=graph_hash,
            )
            payload: JsonObject = {
                "v": OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_REF_INDEX_VERSION,
                "schema": (
                    OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_REF_INDEX_SCHEMA
                ),
                "branch_id": str(branch_id),
                "projection_hash": projection_hash,
                "commit_id": str(commit_id),
                "object_instance_graph_id": str(object_instance_graph_id),
                "graph_hash": graph_hash,
                "graph_hash_source": graph_hash_source,
                "graph": graph_summary,
                **_commit_state_witness_ref_payload(post_witness_ref),
                "segment_blob": {
                    "file_name": "segments.jsonl",
                    "byte_size": len(segment_blob_bytes),
                    "sha256": hashlib.sha256(segment_blob_bytes).hexdigest(),
                },
                "class_segment_count": len(class_segment_refs),
                "class_segments": class_segment_refs,
            }
            if state_witness_cursor_summary is not None:
                payload["state_witness_cursor"] = (
                    _commit_state_witness_cursor_summary_payload(
                        state_witness_cursor_summary,
                    )
                )
            if cursor_chunks:
                payload["state_witness_cursor_chunks"] = [
                    _commit_state_witness_cursor_chunk_payload(chunk)
                    for chunk in cursor_chunks
                ]

        manifest_path = self._snapshot_state_class_segment_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        blob_path = self._snapshot_state_class_segment_blob_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        with commit_perf_span(
            phase="oig_snapshot_store.state_class_segment_ref_index.write_payload",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            segment_blob = segment_blob_bytes.decode("utf-8")
            if manifest_path.exists() and blob_path.exists():
                existing_payload = _try_read_json_object(
                    manifest_path,
                    log_prefix=(
                        "Existing OIG snapshot state class segment ref index is "
                        f"unreadable: {manifest_path}"
                    ),
                )
                try:
                    existing_blob = blob_path.read_text(encoding="utf-8")
                except Exception:
                    existing_blob = None
                if existing_payload == payload and existing_blob == segment_blob:
                    self._write_snapshot_state_class_segment_envelope_sidecar(
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        commit_id=commit_id,
                        payload=payload,
                    )
                    self._write_snapshot_state_class_segment_cursor_chunk_sidecars(
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        commit_id=commit_id,
                        payload=payload,
                        cursor_chunks=cursor_chunks,
                        class_segment_refs=class_segment_refs,
                    )
                    return payload
            _atomic_write_rebuildable_sidecar(blob_path, segment_blob)
            _atomic_write_rebuildable_sidecar(manifest_path, _dump_json(payload))
            _SESSION_JSON_FILE_CACHE.invalidate_path(manifest_path)
            self._write_snapshot_state_class_segment_envelope_sidecar(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                payload=payload,
            )
            self._write_snapshot_state_class_segment_cursor_chunk_sidecars(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                payload=payload,
                cursor_chunks=cursor_chunks,
                class_segment_refs=class_segment_refs,
            )
        return payload

    async def put_state_snapshot_class_segment_index_from_previous(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        previous_commit_id: UUID,
        commit_id: UUID,
        object_instance_graph_id: UUID,
        graph_hash: str,
        post_witness_ref: CommitStateWitnessRef | None,
        replacement_class_segments: Iterable[
            ObjectInstanceGraphSnapshotStateRawClassSegment
        ],
        graph_meta: Mapping[str, object] | None = None,
        graph_hash_source: ObjectInstanceGraphCommitGraphHashSource = "state_hash",
        state_witness_cursor_summary: CommitStateWitnessCursorSummary | None = None,
        state_witness_cursor_chunks: (
            Iterable[CommitStateWitnessCursorChunk] | None
        ) = None,
    ) -> JsonObject | None:
        if graph_hash_source == "state_hash":
            if post_witness_ref is None:
                raise ValueError(
                    "OIG snapshot class segment ref index requires post_witness_ref "
                    + "when graph_hash_source is state_hash"
                )
            if post_witness_ref.state_hash is None:
                raise ValueError(
                    "OIG snapshot class segment ref index requires state_hash "
                    + "when graph_hash_source is state_hash"
                )
            expected_graph_hash = post_witness_ref.state_hash
        elif graph_hash_source == "witness_hash":
            if post_witness_ref is None:
                raise ValueError(
                    "OIG snapshot class segment ref index requires post_witness_ref "
                    + "when graph_hash_source is witness_hash"
                )
            expected_graph_hash = post_witness_ref.witness_hash
        elif graph_hash_source == "witness_cursor_hash":
            if state_witness_cursor_summary is None:
                raise ValueError(
                    "OIG snapshot class segment ref index requires "
                    + "state_witness_cursor_summary when graph_hash_source is "
                    + "witness_cursor_hash"
                )
            expected_graph_hash = state_witness_cursor_summary.cursor_hash
        else:
            raise ValueError(
                f"Unsupported graph_hash_source for class segment ref index: {graph_hash_source!r}"
            )
        if graph_hash != expected_graph_hash:
            raise ValueError(
                "OIG snapshot class segment ref index requires graph_hash to "
                f"match {graph_hash_source}: graph_hash={graph_hash} "
                f"expected={expected_graph_hash}"
            )
        if post_witness_ref is not None and not validate_commit_state_witness_ref(
            post_witness_ref
        ):
            raise ValueError("Invalid post-state witness ref")
        if post_witness_ref is None and graph_hash_source != "witness_cursor_hash":
            raise ValueError(
                "OIG snapshot class segment ref index requires post_witness_ref "
                + f"when graph_hash_source is {graph_hash_source}"
            )

        previous_manifest_path = self._snapshot_state_class_segment_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=previous_commit_id,
        )
        previous_blob_path = self._snapshot_state_class_segment_blob_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=previous_commit_id,
        )
        trace_metadata = _snapshot_trace_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        with commit_perf_span(
            phase="oig_snapshot_store.state_class_segment_ref_index.build_payload",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            with commit_perf_span(
                phase=(
                    "oig_snapshot_store.state_class_segment_ref_index."
                    "previous_envelope_sidecar"
                ),
                category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                metadata=trace_metadata,
            ):
                previous_envelope_valid = (
                    self._snapshot_state_class_segment_envelope_sidecar_matches(
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        commit_id=previous_commit_id,
                        object_instance_graph_id=object_instance_graph_id,
                        blob_path=previous_blob_path,
                    )
                )
            if not previous_envelope_valid:
                with commit_perf_span(
                    phase=(
                        "oig_snapshot_store.state_class_segment_ref_index."
                        "previous_manifest_read"
                    ),
                    category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                    metadata=trace_metadata,
                ):
                    previous_payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
                        previous_manifest_path,
                        log_prefix=(
                            "Existing OIG snapshot state class segment index is "
                            f"unreadable: {previous_manifest_path}"
                        ),
                    )
                if previous_payload is None:
                    return None
                if not self._snapshot_state_class_segment_index_envelope_matches(
                    payload=previous_payload,
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    commit_id=previous_commit_id,
                    object_instance_graph_id=object_instance_graph_id,
                    blob_path=previous_blob_path,
                ):
                    return None
            replacements_by_raw_id: dict[
                str,
                ObjectInstanceGraphSnapshotStateRawClassSegment,
            ] = {}
            for segment in replacement_class_segments:
                raw_class_instance_id = str(segment.class_instance_id)
                if raw_class_instance_id in replacements_by_raw_id:
                    raise ValueError(
                        "Duplicate replacement class segment: "
                        f"{raw_class_instance_id}"
                    )
                replacements_by_raw_id[raw_class_instance_id] = segment

            class_segment_refs: list[JsonObject] = []
            segment_blob_parts: list[bytes] = []
            byte_offset = 0
            for raw_class_instance_id in sorted(replacements_by_raw_id):
                replacement = replacements_by_raw_id[raw_class_instance_id]
                segment_ref = replacement.segment_ref
                if segment_ref.kind != "CLASS":
                    raise ValueError(
                        "Replacement class segment witness ref is not CLASS: "
                        f"{raw_class_instance_id}"
                    )
                if segment_ref.key != f"class:{raw_class_instance_id}":
                    raise ValueError(
                        "Replacement class segment witness ref key mismatch: "
                        f"{raw_class_instance_id}"
                    )
                record_bytes = _raw_class_segment_record_data(replacement).encode(
                    "utf-8"
                )
                record_sha256 = hashlib.sha256(record_bytes).hexdigest()
                class_config_id = str(replacement.class_config_id)
                source_object_id = (
                    str(replacement.source_object_id)
                    if replacement.source_object_id is not None
                    else None
                )
                entry_byte_offset = byte_offset
                entry_byte_length = len(record_bytes)
                segment_blob_parts.append(record_bytes)
                byte_offset += len(record_bytes)
                class_segment_refs.append(
                    {
                        "class_instance_id": raw_class_instance_id,
                        "class_config_id": class_config_id,
                        "source_object_id": source_object_id,
                        "segment": _commit_state_segment_ref_payload(segment_ref),
                        "blob_commit_id": str(commit_id),
                        "byte_offset": entry_byte_offset,
                        "byte_length": entry_byte_length,
                        "record_sha256": record_sha256,
                    }
                )

            if state_witness_cursor_summary is not None:
                if post_witness_ref is not None:
                    self._validate_state_witness_cursor_summary_for_ref(
                        summary=state_witness_cursor_summary,
                        witness_ref=post_witness_ref,
                    )
            cursor_chunks = tuple(state_witness_cursor_chunks or ())
            if cursor_chunks:
                self._validate_state_witness_cursor_chunks_for_summary(
                    chunks=cursor_chunks,
                    summary=state_witness_cursor_summary,
                )

            segment_blob_bytes = b"".join(segment_blob_parts)
            graph_summary = self._snapshot_state_class_segment_graph_summary(
                graph_meta=graph_meta,
                object_instance_graph_id=object_instance_graph_id,
                graph_hash=graph_hash,
            )
            if post_witness_ref is not None:
                witness_ref_summary_payload = _commit_state_witness_ref_summary_payload(
                    post_witness_ref
                )
            else:
                if state_witness_cursor_summary is None:
                    raise ValueError(
                        "OIG snapshot class segment ref index requires "
                        + "state_witness_cursor_summary without post_witness_ref"
                    )
                witness_ref_summary_payload = {
                    "row_count": state_witness_cursor_summary.row_count,
                    "segment_count": state_witness_cursor_summary.segment_count,
                }
            payload: JsonObject = {
                "v": OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_OVERLAY_INDEX_VERSION,
                "schema": (
                    OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_OVERLAY_INDEX_SCHEMA
                ),
                "branch_id": str(branch_id),
                "projection_hash": projection_hash,
                "commit_id": str(commit_id),
                "base_commit_id": str(previous_commit_id),
                "object_instance_graph_id": str(object_instance_graph_id),
                "graph_hash": graph_hash,
                "graph_hash_source": graph_hash_source,
                "graph": graph_summary,
                **witness_ref_summary_payload,
                "segment_blob": {
                    "file_name": "segments.jsonl",
                    "byte_size": len(segment_blob_bytes),
                    "sha256": hashlib.sha256(segment_blob_bytes).hexdigest(),
                },
                "replacement_class_segment_count": len(class_segment_refs),
                "replacement_class_segments": class_segment_refs,
            }
            if state_witness_cursor_summary is not None:
                payload["state_witness_cursor"] = (
                    _commit_state_witness_cursor_summary_payload(
                        state_witness_cursor_summary,
                    )
                )
            if cursor_chunks:
                payload["state_witness_cursor_chunks"] = [
                    _commit_state_witness_cursor_chunk_payload(chunk)
                    for chunk in cursor_chunks
                ]

        manifest_path = self._snapshot_state_class_segment_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        blob_path = self._snapshot_state_class_segment_blob_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        with commit_perf_span(
            phase="oig_snapshot_store.state_class_segment_ref_index.write_payload",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            segment_blob = segment_blob_bytes.decode("utf-8")
            if manifest_path.exists() and blob_path.exists():
                existing_payload = _try_read_json_object(
                    manifest_path,
                    log_prefix=(
                        "Existing OIG snapshot state class segment ref index is "
                        f"unreadable: {manifest_path}"
                    ),
                )
                try:
                    existing_blob = blob_path.read_text(encoding="utf-8")
                except Exception:
                    existing_blob = None
                if existing_payload == payload and existing_blob == segment_blob:
                    self._write_snapshot_state_class_segment_envelope_sidecar(
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        commit_id=commit_id,
                        payload=payload,
                    )
                    self._write_snapshot_state_class_segment_cursor_chunk_sidecars(
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        commit_id=commit_id,
                        payload=payload,
                        cursor_chunks=cursor_chunks,
                        class_segment_refs=class_segment_refs,
                    )
                    return payload
            _atomic_write_rebuildable_sidecar(blob_path, segment_blob)
            _atomic_write_rebuildable_sidecar(manifest_path, _dump_json(payload))
            _SESSION_JSON_FILE_CACHE.invalidate_path(manifest_path)
            self._write_snapshot_state_class_segment_envelope_sidecar(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                payload=payload,
            )
            self._write_snapshot_state_class_segment_cursor_chunk_sidecars(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                payload=payload,
                cursor_chunks=cursor_chunks,
                class_segment_refs=class_segment_refs,
            )
        return payload

    def _snapshot_state_class_segment_refs_from_index_payload(
        self,
        *,
        payload: JsonObject,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        object_instance_graph_id: UUID,
        blob_path: Path,
    ) -> dict[str, JsonObject] | None:
        if payload.get("branch_id") != str(branch_id):
            return None
        if payload.get("projection_hash") != projection_hash:
            return None
        if payload.get("commit_id") != str(commit_id):
            return None
        if payload.get("object_instance_graph_id") != str(object_instance_graph_id):
            return None
        if payload.get("schema") not in {
            OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_INDEX_SCHEMA,
            OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_REF_INDEX_SCHEMA,
        }:
            return None
        raw_blob_metadata = payload.get("segment_blob")
        if not isinstance(raw_blob_metadata, Mapping):
            return None
        blob_metadata = {
            str(key): value
            for key, value in raw_blob_metadata.items()
            if isinstance(key, str)
        }
        if blob_metadata.get("file_name") != "segments.jsonl":
            return None
        blob_byte_size = _json_optional_int(blob_metadata, "byte_size")
        blob_sha256 = _json_optional_string(blob_metadata, "sha256")
        if blob_byte_size is None or blob_byte_size < 0 or not blob_sha256:
            return None
        try:
            blob_size = blob_path.stat().st_size
        except Exception:
            return None
        if blob_size != blob_byte_size:
            return None
        raw_class_segments = payload.get("class_segments")
        if not isinstance(raw_class_segments, list):
            return None
        raw_segment_count = _json_optional_int(payload, "class_segment_count")
        if raw_segment_count != len(raw_class_segments):
            return None
        refs_by_raw_id: dict[str, JsonObject] = {}
        for raw_item in raw_class_segments:
            if not isinstance(raw_item, Mapping):
                return None
            item = {
                str(key): value
                for key, value in raw_item.items()
                if isinstance(key, str)
            }
            raw_class_instance_id = _json_optional_string(
                item,
                "class_instance_id",
            )
            if not raw_class_instance_id:
                return None
            if raw_class_instance_id in refs_by_raw_id:
                return None
            raw_blob_commit_id = _json_optional_string(item, "blob_commit_id") or str(
                commit_id
            )
            try:
                UUID(raw_blob_commit_id)
            except Exception:
                return None
            byte_offset = _json_optional_int(item, "byte_offset")
            byte_length = _json_optional_int(item, "byte_length")
            if (
                byte_offset is None
                or byte_offset < 0
                or byte_length is None
                or byte_length <= 0
                or not _json_optional_string(item, "record_sha256")
            ):
                return None
            refs_by_raw_id[raw_class_instance_id] = item
        return refs_by_raw_id

    def _snapshot_state_class_segment_index_envelope_matches(
        self,
        *,
        payload: JsonObject,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        object_instance_graph_id: UUID,
        blob_path: Path,
    ) -> bool:
        if payload.get("branch_id") != str(branch_id):
            return False
        if payload.get("projection_hash") != projection_hash:
            return False
        if payload.get("commit_id") != str(commit_id):
            return False
        if payload.get("object_instance_graph_id") != str(object_instance_graph_id):
            return False
        schema = payload.get("schema")
        if schema == OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_INDEX_SCHEMA:
            if (
                payload.get("v")
                != OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_INDEX_VERSION
            ):
                return False
        elif (
            schema
            == OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_REF_INDEX_SCHEMA
        ):
            if (
                payload.get("v")
                != OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_REF_INDEX_VERSION
            ):
                return False
        elif (
            schema
            == OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_OVERLAY_INDEX_SCHEMA
        ):
            if (
                payload.get("v")
                != OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_OVERLAY_INDEX_VERSION
            ):
                return False
        else:
            return False
        return self._snapshot_state_class_segment_blob_metadata_valid(
            payload=payload,
            blob_path=blob_path,
        )

    def _snapshot_state_class_segment_overlay_witness_ref_from_payload(
        self,
        *,
        payload: JsonObject,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        expected_object_instance_graph_id: UUID | None,
        visited_commit_ids: set[UUID],
        depth: int,
    ) -> CommitStateWitnessRef | None:
        if depth > _SNAPSHOT_STATE_CLASS_SEGMENT_OVERLAY_MAX_DEPTH:
            return None
        if commit_id in visited_commit_ids:
            return None
        visited_commit_ids.add(commit_id)
        if (
            payload.get("v")
            != OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_OVERLAY_INDEX_VERSION
        ):
            return None
        raw_base_commit_id = _json_optional_string(payload, "base_commit_id")
        if raw_base_commit_id is None:
            return None
        try:
            base_commit_id = UUID(raw_base_commit_id)
        except Exception:
            return None
        base_manifest_path = self._snapshot_state_class_segment_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=base_commit_id,
        )
        base_payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
            base_manifest_path,
            log_prefix=(
                "Failed reading base snapshot state class segment "
                f"index {base_commit_id}"
            ),
        )
        if base_payload is None:
            return None
        base_metadata = self._snapshot_state_class_segment_index_metadata_from_payload(
            payload=base_payload,
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=base_commit_id,
            expected_object_instance_graph_id=expected_object_instance_graph_id,
            expected_graph_hash=None,
            visited_commit_ids=visited_commit_ids,
            depth=depth + 1,
        )
        if base_metadata is None:
            return None
        raw_replacement_segments = payload.get("replacement_class_segments")
        if not isinstance(raw_replacement_segments, list):
            return None
        raw_replacement_count = _json_optional_int(
            payload,
            "replacement_class_segment_count",
        )
        if raw_replacement_count != len(raw_replacement_segments):
            return None
        replacement_segments_by_key: dict[str, CommitStateSegmentRef] = {}
        for raw_item in raw_replacement_segments:
            if not isinstance(raw_item, Mapping):
                return None
            item = {
                str(key): value
                for key, value in raw_item.items()
                if isinstance(key, str)
            }
            raw_class_instance_id = _json_optional_string(
                item,
                "class_instance_id",
            )
            if not raw_class_instance_id:
                return None
            try:
                UUID(raw_class_instance_id)
                UUID(_json_required_string(item, "blob_commit_id"))
                segment_ref = _commit_state_segment_ref_from_payload(
                    item.get("segment")
                )
            except Exception:
                return None
            if (
                segment_ref.kind != "CLASS"
                or segment_ref.key != f"class:{raw_class_instance_id}"
            ):
                return None
            if segment_ref.key in replacement_segments_by_key:
                return None
            byte_offset = _json_optional_int(item, "byte_offset")
            byte_length = _json_optional_int(item, "byte_length")
            if (
                byte_offset is None
                or byte_offset < 0
                or byte_length is None
                or byte_length <= 0
                or not _json_optional_string(item, "record_sha256")
            ):
                return None
            replacement_segments_by_key[segment_ref.key] = segment_ref
        try:
            witness_ref = replace_existing_commit_state_witness_ref_segments(
                pre_witness_ref=base_metadata.witness_ref,
                replacement_segments_by_key=replacement_segments_by_key,
                post_state_hash=_json_optional_string(payload, "state_hash"),
            )
        except Exception:
            return None
        if witness_ref.witness_hash != _json_optional_string(payload, "witness_hash"):
            return None
        if witness_ref.row_count != _json_optional_int(payload, "row_count"):
            return None
        if len(witness_ref.segments) != _json_optional_int(payload, "segment_count"):
            return None
        return witness_ref

    def _snapshot_state_class_segment_index_metadata_from_payload(
        self,
        *,
        payload: JsonObject,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        expected_object_instance_graph_id: UUID | None = None,
        expected_graph_hash: str | None = None,
        visited_commit_ids: set[UUID] | None = None,
        depth: int = 0,
    ) -> ObjectInstanceGraphSnapshotStateSegmentIndexMetadata | None:
        if payload.get("branch_id") != str(branch_id):
            return None
        if payload.get("projection_hash") != projection_hash:
            return None
        if payload.get("commit_id") != str(commit_id):
            return None
        schema = payload.get("schema")
        if (
            schema
            == OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_REF_INDEX_SCHEMA
        ):
            metadata = _snapshot_state_segment_index_metadata_from_payload(payload)
        elif (
            schema
            == OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_OVERLAY_INDEX_SCHEMA
        ):
            witness_ref = (
                self._snapshot_state_class_segment_overlay_witness_ref_from_payload(
                    payload=payload,
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    commit_id=commit_id,
                    expected_object_instance_graph_id=(
                        expected_object_instance_graph_id
                    ),
                    visited_commit_ids=(
                        visited_commit_ids if visited_commit_ids is not None else set()
                    ),
                    depth=depth,
                )
            )
            if witness_ref is None:
                return None
            witness_cursor_summary = (
                self._state_witness_cursor_summary_from_index_payload(
                    payload=payload,
                    witness_ref=witness_ref,
                )
            )
            if (
                payload.get("state_witness_cursor") is not None
                and witness_cursor_summary is None
            ):
                return None
            try:
                metadata = ObjectInstanceGraphSnapshotStateSegmentIndexMetadata(
                    payload=payload,
                    object_instance_graph_id=_json_required_uuid(
                        payload,
                        "object_instance_graph_id",
                    ),
                    graph_hash=_json_required_string(payload, "graph_hash"),
                    state_hash=witness_ref.state_hash,
                    witness_hash=witness_ref.witness_hash,
                    row_count=witness_ref.row_count,
                    witness_ref=witness_ref,
                    witness_cursor_summary=witness_cursor_summary,
                )
            except Exception:
                return None
        elif schema == OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_INDEX_SCHEMA:
            raw_witness_payload = payload.get("state_witness")
            if not isinstance(raw_witness_payload, dict):
                return None
            witness_metadata = _snapshot_state_witness_metadata_from_payload(
                _coerce_json_object_view(
                    raw_witness_payload,
                    error_message="Embedded state witness must be a JSON object",
                )
            )
            if witness_metadata is None:
                return None
            metadata = ObjectInstanceGraphSnapshotStateSegmentIndexMetadata(
                payload=payload,
                object_instance_graph_id=witness_metadata.object_instance_graph_id,
                graph_hash=witness_metadata.graph_hash,
                state_hash=witness_metadata.state_hash,
                witness_hash=witness_metadata.witness_hash,
                row_count=witness_metadata.row_count,
                witness_ref=witness_metadata.witness_ref,
            )
        else:
            return None
        if metadata is None:
            return None
        graph_hash_source = payload.get("graph_hash_source") or "state_hash"
        if graph_hash_source == "witness_hash":
            if metadata.graph_hash != metadata.witness_hash:
                return None
        elif graph_hash_source == "witness_cursor_hash":
            if (
                metadata.witness_cursor_summary is None
                or metadata.graph_hash != metadata.witness_cursor_summary.cursor_hash
            ):
                return None
        elif graph_hash_source == "state_hash":
            if (
                metadata.state_hash is None
                or metadata.graph_hash != metadata.state_hash
            ):
                return None
        else:
            return None
        if (
            expected_object_instance_graph_id is not None
            and metadata.object_instance_graph_id != expected_object_instance_graph_id
        ):
            return None
        if (
            expected_graph_hash is not None
            and metadata.graph_hash != expected_graph_hash
        ):
            return None
        return metadata

    def _snapshot_state_class_segment_blob_metadata_valid(
        self,
        *,
        payload: JsonObject,
        blob_path: Path,
    ) -> bool:
        raw_blob_metadata = payload.get("segment_blob")
        if not isinstance(raw_blob_metadata, Mapping):
            return False
        blob_metadata = {
            str(key): value
            for key, value in raw_blob_metadata.items()
            if isinstance(key, str)
        }
        if blob_metadata.get("file_name") != "segments.jsonl":
            return False
        blob_byte_size = _json_optional_int(blob_metadata, "byte_size")
        blob_sha256 = _json_optional_string(blob_metadata, "sha256")
        if blob_byte_size is None or blob_byte_size < 0 or not blob_sha256:
            return False
        try:
            return blob_path.stat().st_size == blob_byte_size
        except Exception:
            return False

    def _write_snapshot_state_class_segment_envelope_sidecar(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        payload: JsonObject,
    ) -> None:
        raw_blob_metadata = payload.get("segment_blob")
        if not isinstance(raw_blob_metadata, Mapping):
            return
        sidecar_payload: JsonObject = {
            "v": _SNAPSHOT_STATE_CLASS_SEGMENT_ENVELOPE_SIDECAR_VERSION,
            "schema": _SNAPSHOT_STATE_CLASS_SEGMENT_ENVELOPE_SIDECAR_SCHEMA,
            "branch_id": str(branch_id),
            "projection_hash": projection_hash,
            "commit_id": str(commit_id),
            "object_instance_graph_id": str(payload.get("object_instance_graph_id")),
            "graph_hash": str(payload.get("graph_hash")),
            "graph_hash_source": str(payload.get("graph_hash_source") or "state_hash"),
            "segment_blob": {
                str(key): value
                for key, value in raw_blob_metadata.items()
                if isinstance(key, str)
            },
        }
        raw_base_commit_id = _json_optional_string(payload, "base_commit_id")
        if raw_base_commit_id is not None:
            sidecar_payload["base_commit_id"] = raw_base_commit_id
        raw_cursor = payload.get("state_witness_cursor")
        if isinstance(raw_cursor, Mapping):
            cursor_hash = _json_optional_string(
                {str(key): value for key, value in raw_cursor.items()},
                "cursor_hash",
            )
            if cursor_hash is not None:
                sidecar_payload["state_witness_cursor_hash"] = cursor_hash
        sidecar_path = self._snapshot_state_class_segment_envelope_sidecar_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        if sidecar_path.exists():
            existing_payload = _try_read_json_object(
                sidecar_path,
                log_prefix=(
                    "Existing OIG snapshot state class segment envelope sidecar "
                    f"is unreadable: {sidecar_path}"
                ),
            )
            if existing_payload == sidecar_payload:
                return
        _atomic_write_rebuildable_sidecar(sidecar_path, _dump_json(sidecar_payload))
        _SESSION_JSON_FILE_CACHE.invalidate_path(sidecar_path)

    def _snapshot_state_class_segment_envelope_sidecar_matches(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        object_instance_graph_id: UUID,
        blob_path: Path,
    ) -> bool:
        sidecar_path = self._snapshot_state_class_segment_envelope_sidecar_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
            sidecar_path,
            log_prefix=(
                "Failed reading snapshot state class segment envelope sidecar "
                f"{commit_id}"
            ),
        )
        if payload is None:
            return False
        if (
            payload.get("schema")
            != _SNAPSHOT_STATE_CLASS_SEGMENT_ENVELOPE_SIDECAR_SCHEMA
        ):
            return False
        if payload.get("v") != _SNAPSHOT_STATE_CLASS_SEGMENT_ENVELOPE_SIDECAR_VERSION:
            return False
        if payload.get("branch_id") != str(branch_id):
            return False
        if payload.get("projection_hash") != projection_hash:
            return False
        if payload.get("commit_id") != str(commit_id):
            return False
        try:
            payload_object_instance_graph_id = _json_required_uuid(
                payload,
                "object_instance_graph_id",
            )
        except Exception:
            return False
        if payload_object_instance_graph_id != object_instance_graph_id:
            return False
        return self._snapshot_state_class_segment_blob_metadata_valid(
            payload=payload,
            blob_path=blob_path,
        )

    def _write_snapshot_state_class_segment_cursor_chunk_sidecars(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        payload: JsonObject,
        cursor_chunks: tuple[CommitStateWitnessCursorChunk, ...],
        class_segment_refs: Iterable[JsonObject],
    ) -> None:
        if not cursor_chunks:
            return
        raw_blob_metadata = payload.get("segment_blob")
        if not isinstance(raw_blob_metadata, Mapping):
            return
        cursor_summary = _commit_state_witness_cursor_summary_from_payload(
            payload.get("state_witness_cursor"),
        )
        if cursor_summary is None:
            return
        segment_blob_metadata = {
            str(key): value
            for key, value in raw_blob_metadata.items()
            if isinstance(key, str)
        }
        refs_by_segment_key: dict[str, JsonObject] = {}
        for raw_ref in class_segment_refs:
            raw_class_instance_id = raw_ref.get("class_instance_id")
            if not isinstance(raw_class_instance_id, str):
                continue
            refs_by_segment_key[f"class:{raw_class_instance_id}"] = {
                str(key): value
                for key, value in raw_ref.items()
                if isinstance(key, str)
            }
        if not refs_by_segment_key:
            return
        common_payload: JsonObject = {
            "v": _SNAPSHOT_STATE_CLASS_SEGMENT_CURSOR_CHUNK_SIDECAR_VERSION,
            "schema": _SNAPSHOT_STATE_CLASS_SEGMENT_CURSOR_CHUNK_SIDECAR_SCHEMA,
            "branch_id": str(branch_id),
            "projection_hash": projection_hash,
            "commit_id": str(commit_id),
            "object_instance_graph_id": str(payload.get("object_instance_graph_id")),
            "graph_hash": str(payload.get("graph_hash")),
            "graph_hash_source": str(payload.get("graph_hash_source") or "state_hash"),
            "state_witness_cursor_hash": cursor_summary.cursor_hash,
            "segment_blob": segment_blob_metadata,
        }
        raw_base_commit_id = _json_optional_string(payload, "base_commit_id")
        if raw_base_commit_id is not None:
            common_payload["base_commit_id"] = raw_base_commit_id
        chunk_index_by_raw_id: dict[str, int] = {}
        for chunk in cursor_chunks:
            chunk_refs = tuple(
                refs_by_segment_key[key]
                for key in chunk.segment_keys
                if key in refs_by_segment_key
            )
            if not chunk_refs:
                continue
            for raw_ref in chunk_refs:
                raw_class_instance_id = _json_optional_string(
                    raw_ref,
                    "class_instance_id",
                )
                if raw_class_instance_id is not None:
                    chunk_index_by_raw_id[raw_class_instance_id] = chunk.index
            sidecar_payload: JsonObject = {
                **common_payload,
                "chunk_index": chunk.index,
                "state_witness_cursor_chunk": (
                    _commit_state_witness_cursor_chunk_payload(chunk)
                ),
                "class_segment_count": len(chunk_refs),
                "class_segments": list(chunk_refs),
            }
            sidecar_path = self._snapshot_state_class_segment_cursor_chunk_sidecar_path(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                chunk_index=chunk.index,
            )
            existing_payload = None
            if sidecar_path.exists():
                existing_payload = _try_read_json_object(
                    sidecar_path,
                    log_prefix=(
                        "Existing OIG snapshot state class segment cursor chunk "
                        f"sidecar is unreadable: {sidecar_path}"
                    ),
                )
            if existing_payload == sidecar_payload:
                continue
            _atomic_write_rebuildable_sidecar(sidecar_path, _dump_json(sidecar_payload))
            _SESSION_JSON_FILE_CACHE.invalidate_path(sidecar_path)
        chunk_indexes_by_bucket: dict[str, dict[str, int]] = {}
        for raw_class_instance_id, chunk_index in chunk_index_by_raw_id.items():
            bucket = _snapshot_state_class_segment_cursor_key_index_bucket(
                raw_class_instance_id,
            )
            if bucket is None:
                continue
            chunk_indexes_by_bucket.setdefault(bucket, {})[
                raw_class_instance_id
            ] = chunk_index
        for bucket, chunk_indexes in sorted(chunk_indexes_by_bucket.items()):
            sidecar_payload = {
                **common_payload,
                "v": _SNAPSHOT_STATE_CLASS_SEGMENT_CURSOR_KEY_INDEX_SIDECAR_VERSION,
                "schema": _SNAPSHOT_STATE_CLASS_SEGMENT_CURSOR_KEY_INDEX_SIDECAR_SCHEMA,
                "bucket": bucket,
                "class_chunk_index_count": len(chunk_indexes),
                "class_chunk_indexes": dict(sorted(chunk_indexes.items())),
            }
            sidecar_path = (
                self._snapshot_state_class_segment_cursor_key_index_sidecar_path(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    commit_id=commit_id,
                    bucket_key=bucket,
                )
            )
            if sidecar_path.exists():
                existing_payload = _try_read_json_object(
                    sidecar_path,
                    log_prefix=(
                        "Existing OIG snapshot state class segment cursor key "
                        f"index sidecar is unreadable: {sidecar_path}"
                    ),
                )
                if existing_payload == sidecar_payload:
                    continue
            _atomic_write_rebuildable_sidecar(sidecar_path, _dump_json(sidecar_payload))
            _SESSION_JSON_FILE_CACHE.invalidate_path(sidecar_path)

    def _snapshot_state_class_segment_selected_refs_from_payload(
        self,
        *,
        payload: JsonObject,
        selected_ids: set[str],
        field_name: str,
        count_field_name: str,
    ) -> dict[str, JsonObject] | None:
        raw_class_segments = payload.get(field_name)
        if not isinstance(raw_class_segments, list):
            return None
        raw_segment_count = _json_optional_int(payload, count_field_name)
        if raw_segment_count != len(raw_class_segments):
            return None
        selected_refs: dict[str, JsonObject] = {}
        for raw_item in raw_class_segments:
            if not isinstance(raw_item, Mapping):
                return None
            raw_class_instance_id = raw_item.get("class_instance_id")
            if (
                not isinstance(raw_class_instance_id, str)
                or raw_class_instance_id not in selected_ids
            ):
                continue
            if raw_class_instance_id in selected_refs:
                return None
            item = {
                str(key): value
                for key, value in raw_item.items()
                if isinstance(key, str)
            }
            byte_offset = _json_optional_int(item, "byte_offset")
            byte_length = _json_optional_int(item, "byte_length")
            record_sha256 = _json_optional_string(item, "record_sha256")
            raw_blob_commit_id = _json_optional_string(item, "blob_commit_id")
            if (
                byte_offset is None
                or byte_offset < 0
                or byte_length is None
                or byte_length <= 0
                or not record_sha256
            ):
                return None
            if raw_blob_commit_id is not None:
                try:
                    UUID(raw_blob_commit_id)
                except Exception:
                    return None
            selected_refs[raw_class_instance_id] = item
        return selected_refs

    def _snapshot_state_class_segment_graph_summary(
        self,
        *,
        graph_meta: Mapping[str, object] | None,
        object_instance_graph_id: UUID,
        graph_hash: str,
    ) -> JsonObject:
        graph_summary: JsonObject = {
            "id": str(object_instance_graph_id),
            "hash": graph_hash,
        }
        if graph_meta is None:
            return graph_summary
        for key in (
            "key",
            "name",
            "description",
            "object_projection_graph_id",
            "root_class_instance_id",
            "root_source_object_id",
        ):
            value = graph_meta.get(key)
            if value is not None:
                graph_summary[key] = _snapshot_state_json_value(value)
        return graph_summary

    @staticmethod
    def _validate_state_witness_cursor_summary_for_ref(
        *,
        summary: CommitStateWitnessCursorSummary,
        witness_ref: CommitStateWitnessRef,
    ) -> None:
        if (
            _commit_state_witness_cursor_summary_from_payload(
                _commit_state_witness_cursor_summary_payload(summary),
            )
            != summary
        ):
            raise ValueError("Invalid state witness cursor summary")
        if summary.state_hash != witness_ref.state_hash:
            raise ValueError("State witness cursor summary state_hash mismatch")
        if summary.legacy_witness_hash != witness_ref.witness_hash:
            raise ValueError(
                "State witness cursor summary legacy_witness_hash mismatch"
            )
        if summary.row_count != witness_ref.row_count:
            raise ValueError("State witness cursor summary row_count mismatch")
        if summary.segment_count != len(witness_ref.segments):
            raise ValueError("State witness cursor summary segment_count mismatch")

    def _state_witness_cursor_summary_from_index_payload(
        self,
        *,
        payload: JsonObject,
        witness_ref: CommitStateWitnessRef,
    ) -> CommitStateWitnessCursorSummary | None:
        raw_cursor_summary = payload.get("state_witness_cursor")
        if raw_cursor_summary is None:
            return None
        summary = _commit_state_witness_cursor_summary_from_payload(
            raw_cursor_summary,
        )
        if summary is None:
            return None
        try:
            self._validate_state_witness_cursor_summary_for_ref(
                summary=summary,
                witness_ref=witness_ref,
            )
        except ValueError:
            return None
        return summary

    @staticmethod
    def _validate_state_witness_cursor_chunks_for_summary(
        *,
        chunks: tuple[CommitStateWitnessCursorChunk, ...],
        summary: CommitStateWitnessCursorSummary | None,
    ) -> None:
        if summary is None:
            raise ValueError("State witness cursor chunks require a cursor summary")
        summary_chunks_by_index = {chunk.index: chunk for chunk in summary.chunks}
        if len(summary_chunks_by_index) != len(summary.chunks):
            raise ValueError("State witness cursor summary has duplicate chunks")
        chunk_indexes: set[int] = set()
        for chunk in chunks:
            if chunk.index in chunk_indexes:
                raise ValueError("Duplicate state witness cursor chunk detail")
            chunk_indexes.add(chunk.index)
            summary_chunk = summary_chunks_by_index.get(chunk.index)
            if summary_chunk is None:
                raise ValueError("Unknown state witness cursor chunk detail")
            FSSnapshotStore._require_matching_state_witness_cursor_chunk_summary(
                chunk=chunk,
                summary_chunk=summary_chunk,
            )

    @staticmethod
    def _require_matching_state_witness_cursor_chunk_summary(
        *,
        chunk: CommitStateWitnessCursorChunk,
        summary_chunk: CommitStateWitnessCursorChunkSummary,
    ) -> None:
        if not chunk.segment_keys or not chunk.segments:
            raise ValueError("State witness cursor chunk detail is empty")
        if tuple(segment.key for segment in chunk.segments) != chunk.segment_keys:
            raise ValueError("State witness cursor chunk segment key mismatch")
        if chunk.index != summary_chunk.index:
            raise ValueError("State witness cursor chunk index mismatch")
        if chunk.segment_keys[0] != summary_chunk.first_segment_key:
            raise ValueError("State witness cursor chunk first key mismatch")
        if chunk.segment_keys[-1] != summary_chunk.last_segment_key:
            raise ValueError("State witness cursor chunk last key mismatch")
        if len(chunk.segments) != summary_chunk.segment_count:
            raise ValueError("State witness cursor chunk segment count mismatch")
        if chunk.row_count != summary_chunk.row_count:
            raise ValueError("State witness cursor chunk row count mismatch")
        if chunk.digest != summary_chunk.digest:
            raise ValueError("State witness cursor chunk digest mismatch")

    def _state_witness_cursor_chunks_from_index_payload(
        self,
        *,
        payload: JsonObject,
        summary: CommitStateWitnessCursorSummary | None,
        selected_chunk_indexes: set[int] | None = None,
    ) -> tuple[CommitStateWitnessCursorChunk, ...] | None:
        raw_chunks = payload.get("state_witness_cursor_chunks")
        if raw_chunks is None:
            return ()
        if not isinstance(raw_chunks, list):
            return None
        chunks: list[CommitStateWitnessCursorChunk] = []
        for raw_chunk in raw_chunks:
            if selected_chunk_indexes is not None:
                if not isinstance(raw_chunk, Mapping):
                    return None
                raw_index = raw_chunk.get("index")
                if not isinstance(raw_index, int) or isinstance(raw_index, bool):
                    return None
                if raw_index not in selected_chunk_indexes:
                    continue
            chunk = _commit_state_witness_cursor_chunk_from_payload(raw_chunk)
            if chunk is None:
                return None
            chunks.append(chunk)
        try:
            self._validate_state_witness_cursor_chunks_for_summary(
                chunks=tuple(chunks),
                summary=summary,
            )
        except ValueError:
            return None
        return tuple(chunks)

    def snapshot_state_class_segment_index_metadata(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        expected_object_instance_graph_id: UUID | None = None,
        expected_graph_hash: str | None = None,
    ) -> ObjectInstanceGraphSnapshotStateSegmentIndexMetadata | None:
        manifest_path = self._snapshot_state_class_segment_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        blob_path = self._snapshot_state_class_segment_blob_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
            manifest_path,
            log_prefix=(
                "Failed reading snapshot state class segment index metadata "
                f"{commit_id}"
            ),
        )
        if payload is None:
            return None
        metadata = self._snapshot_state_class_segment_index_metadata_from_payload(
            payload=payload,
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            expected_object_instance_graph_id=expected_object_instance_graph_id,
            expected_graph_hash=expected_graph_hash,
        )
        if metadata is None:
            return None
        schema = payload.get("schema")
        if (
            schema
            == OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_OVERLAY_INDEX_SCHEMA
        ):
            if not self._snapshot_state_class_segment_blob_metadata_valid(
                payload=payload,
                blob_path=blob_path,
            ):
                return None
            raw_base_commit_id = _json_optional_string(payload, "base_commit_id")
            if raw_base_commit_id is None:
                return None
            try:
                UUID(raw_base_commit_id)
            except Exception:
                return None
        elif (
            self._snapshot_state_class_segment_refs_from_index_payload(
                payload=payload,
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                object_instance_graph_id=metadata.object_instance_graph_id,
                blob_path=blob_path,
            )
            is None
        ):
            return None
        return metadata

    def _write_snapshot_state_class_segments_index_from_rows_payload(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        state_rows_payload: JsonObject,
        state_rows_path: Path,
    ) -> None:
        state_rows = _commit_state_rows_from_snapshot_payload(state_rows_payload)
        if state_rows is None:
            return
        object_instance_graph_id = _json_optional_uuid(
            state_rows_payload,
            "object_instance_graph_id",
        )
        graph_hash = _json_optional_string(state_rows_payload, "graph_hash")
        if object_instance_graph_id is None or graph_hash is None:
            return
        self._write_snapshot_state_class_segments_index(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            object_instance_graph_id=object_instance_graph_id,
            graph_hash=graph_hash,
            state_index=CommitStateIndex(rows=state_rows),
            state_rows_payload=state_rows_payload,
            state_rows_path=state_rows_path,
        )

    def _write_snapshot_state_rows_index(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        oig: ObjectInstanceGraph,
        snapshot_payload: JsonObject | None = None,
        write_state_witness: bool = False,
    ) -> None:
        payload = self._snapshot_state_rows_payload(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            oig=oig,
            snapshot_payload=snapshot_payload,
        )
        if payload is None:
            return
        write_payload = _snapshot_state_rows_payload_write(payload)
        path = self._snapshot_state_rows_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        if path.exists():
            existing_payload = _try_read_json_object(
                path,
                log_prefix=(
                    f"Existing OIG snapshot state row index is unreadable: {path}"
                ),
            )
            if existing_payload == write_payload.payload:
                if write_state_witness:
                    self._write_snapshot_state_witness_index_from_rows_payload(
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        commit_id=commit_id,
                        state_rows_payload=write_payload.payload,
                        state_rows_path=path,
                    )
                return
        _atomic_write(path, write_payload.data)
        _SESSION_JSON_FILE_CACHE.invalidate_path(path)
        _SESSION_SNAPSHOT_STATE_ROWS_READ_CACHE.invalidate_path(path)
        if write_state_witness:
            self._write_snapshot_state_witness_index_from_rows_payload(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                state_rows_payload=write_payload.payload,
                state_rows_path=path,
            )

    async def put(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        oig: ObjectInstanceGraph,
        indexes: JsonObject,
        write_state_witness: bool = False,
    ) -> None:
        lane_dir = self._lane_dir(branch_id, projection_hash)
        snapshots_dir = lane_dir / "snapshots"
        indexes_dir = lane_dir / "indexes"
        snapshots_dir.mkdir(parents=True, exist_ok=True)
        indexes_dir.mkdir(parents=True, exist_ok=True)

        snapshot_payload: JsonObject | None = None
        try:
            snapshot_payload = _coerce_json_object(
                oig.model_dump(mode="json", exclude_none=True),
                error_message="ObjectInstanceGraph snapshot did not serialize to a JSON object",
            )
            oig_json = _dump_json(snapshot_payload)
        except Exception:
            oig_json = oig.model_dump_json(exclude_none=True)

        snapshot_path = snapshots_dir / f"{commit_id}.json"
        index_path = indexes_dir / f"{commit_id}.json"
        _atomic_write(snapshot_path, oig_json)
        _atomic_write(index_path, _dump_json({"v": 1, **indexes}))
        _SESSION_JSON_FILE_CACHE.invalidate_path(snapshot_path)
        _SESSION_JSON_FILE_CACHE.invalidate_path(index_path)
        self._write_snapshot_state_rows_index(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            oig=oig,
            snapshot_payload=snapshot_payload,
            write_state_witness=write_state_witness,
        )

    async def put_state_snapshot(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        oig: ObjectInstanceGraph,
        write_state_witness: bool = False,
    ) -> JsonObject | None:
        snapshot_payload = _coerce_json_object(
            oig.model_dump(mode="json", exclude_none=True),
            error_message=(
                "ObjectInstanceGraph state snapshot did not serialize to a "
                "JSON object"
            ),
        )
        payload = self._snapshot_state_rows_payload(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            oig=oig,
            snapshot_payload=snapshot_payload,
            include_snapshot_file_metadata=False,
        )
        if payload is None:
            return None
        write_payload = _snapshot_state_rows_payload_write(payload)
        path = self._snapshot_state_rows_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        if path.exists():
            existing_payload = _try_read_json_object(
                path,
                log_prefix=(
                    f"Existing OIG snapshot state row index is unreadable: {path}"
                ),
            )
            if existing_payload == write_payload.payload:
                if write_state_witness:
                    self._write_snapshot_state_witness_index_from_rows_payload(
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        commit_id=commit_id,
                        state_rows_payload=write_payload.payload,
                        state_rows_path=path,
                    )
                return write_payload.payload
        _atomic_write(path, write_payload.data)
        _SESSION_JSON_FILE_CACHE.invalidate_path(path)
        _SESSION_SNAPSHOT_STATE_ROWS_READ_CACHE.invalidate_path(path)
        if write_state_witness:
            self._write_snapshot_state_witness_index_from_rows_payload(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                state_rows_payload=write_payload.payload,
                state_rows_path=path,
            )
        return write_payload.payload

    async def put_state_snapshot_rows(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        object_instance_graph_id: UUID,
        graph_hash: str,
        graph_meta: Mapping[str, object],
        class_instances: Iterable[ClassInstance],
        class_instance_relationships: Iterable[ClassInstanceRelationship],
        state_index: CommitStateIndex,
        write_state_witness: bool = False,
        write_state_class_segments: bool = False,
        write_state_class_segment_index: bool = False,
    ) -> JsonObject:
        payload = self._snapshot_state_rows_payload_from_parts(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            object_instance_graph_id=object_instance_graph_id,
            graph_hash=graph_hash,
            graph_meta=graph_meta,
            class_instances=class_instances,
            class_instance_relationships=class_instance_relationships,
            state_index=state_index,
        )
        write_payload = _snapshot_state_rows_payload_write(payload)
        path = self._snapshot_state_rows_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        if path.exists():
            existing_payload = _try_read_json_object(
                path,
                log_prefix=(
                    f"Existing OIG snapshot state row index is unreadable: {path}"
                ),
            )
            if existing_payload == write_payload.payload:
                if write_state_witness or write_state_class_segment_index:
                    self._write_snapshot_state_witness_index(
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        commit_id=commit_id,
                        object_instance_graph_id=object_instance_graph_id,
                        graph_hash=graph_hash,
                        state_index=state_index,
                        state_rows_payload=write_payload.payload,
                        state_rows_path=path,
                    )
                if write_state_class_segments:
                    self._write_snapshot_state_class_segments_index(
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        commit_id=commit_id,
                        object_instance_graph_id=object_instance_graph_id,
                        graph_hash=graph_hash,
                        state_index=state_index,
                        state_rows_payload=write_payload.payload,
                        state_rows_path=path,
                    )
                if write_state_class_segment_index:
                    self._write_snapshot_state_class_segment_index(
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        commit_id=commit_id,
                        object_instance_graph_id=object_instance_graph_id,
                        graph_hash=graph_hash,
                        state_index=state_index,
                        state_rows_payload=write_payload.payload,
                        state_rows_path=path,
                    )
                _SESSION_SNAPSHOT_STATE_ROWS_READ_CACHE.store_path(
                    path,
                    payload=write_payload.payload,
                    state_rows=state_index.rows,
                )
                return write_payload.payload
        _atomic_write_rebuildable_sidecar(path, write_payload.data)
        _SESSION_JSON_FILE_CACHE.invalidate_path(path)
        if write_state_witness or write_state_class_segment_index:
            self._write_snapshot_state_witness_index(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                object_instance_graph_id=object_instance_graph_id,
                graph_hash=graph_hash,
                state_index=state_index,
                state_rows_payload=write_payload.payload,
                state_rows_path=path,
            )
        if write_state_class_segments:
            self._write_snapshot_state_class_segments_index(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                object_instance_graph_id=object_instance_graph_id,
                graph_hash=graph_hash,
                state_index=state_index,
                state_rows_payload=write_payload.payload,
                state_rows_path=path,
            )
        if write_state_class_segment_index:
            self._write_snapshot_state_class_segment_index(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                object_instance_graph_id=object_instance_graph_id,
                graph_hash=graph_hash,
                state_index=state_index,
                state_rows_payload=write_payload.payload,
                state_rows_path=path,
            )
        _SESSION_SNAPSHOT_STATE_ROWS_READ_CACHE.store_path(
            path,
            payload=write_payload.payload,
            state_rows=state_index.rows,
        )
        return write_payload.payload

    async def put_state_snapshot_rows_from_payloads(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        object_instance_graph_id: UUID,
        graph_hash: str,
        graph_meta: Mapping[str, object],
        class_instance_payloads: Iterable[Mapping[str, object]],
        class_instances: Iterable[ClassInstance],
        class_instance_relationships: Iterable[ClassInstanceRelationship],
        state_index: CommitStateIndex,
        write_state_witness: bool = False,
        write_state_class_segments: bool = False,
        write_state_class_segment_index: bool = False,
    ) -> JsonObject:
        payload = self._snapshot_state_rows_payload_from_payloads(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            object_instance_graph_id=object_instance_graph_id,
            graph_hash=graph_hash,
            graph_meta=graph_meta,
            class_instance_payloads=class_instance_payloads,
            class_instances=class_instances,
            class_instance_relationships=class_instance_relationships,
            state_index=state_index,
        )
        write_payload = _snapshot_state_rows_payload_write(payload)
        path = self._snapshot_state_rows_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        if path.exists():
            existing_payload = _try_read_json_object(
                path,
                log_prefix=(
                    f"Existing OIG snapshot state row index is unreadable: {path}"
                ),
            )
            if existing_payload == write_payload.payload:
                if write_state_witness or write_state_class_segment_index:
                    self._write_snapshot_state_witness_index(
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        commit_id=commit_id,
                        object_instance_graph_id=object_instance_graph_id,
                        graph_hash=graph_hash,
                        state_index=state_index,
                        state_rows_payload=write_payload.payload,
                        state_rows_path=path,
                    )
                if write_state_class_segments:
                    self._write_snapshot_state_class_segments_index(
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        commit_id=commit_id,
                        object_instance_graph_id=object_instance_graph_id,
                        graph_hash=graph_hash,
                        state_index=state_index,
                        state_rows_payload=write_payload.payload,
                        state_rows_path=path,
                    )
                if write_state_class_segment_index:
                    self._write_snapshot_state_class_segment_index(
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        commit_id=commit_id,
                        object_instance_graph_id=object_instance_graph_id,
                        graph_hash=graph_hash,
                        state_index=state_index,
                        state_rows_payload=write_payload.payload,
                        state_rows_path=path,
                    )
                _SESSION_SNAPSHOT_STATE_ROWS_READ_CACHE.store_path(
                    path,
                    payload=write_payload.payload,
                    state_rows=state_index.rows,
                )
                return write_payload.payload
        _atomic_write_rebuildable_sidecar(path, write_payload.data)
        _SESSION_JSON_FILE_CACHE.invalidate_path(path)
        if write_state_witness or write_state_class_segment_index:
            self._write_snapshot_state_witness_index(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                object_instance_graph_id=object_instance_graph_id,
                graph_hash=graph_hash,
                state_index=state_index,
                state_rows_payload=write_payload.payload,
                state_rows_path=path,
            )
        if write_state_class_segments:
            self._write_snapshot_state_class_segments_index(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                object_instance_graph_id=object_instance_graph_id,
                graph_hash=graph_hash,
                state_index=state_index,
                state_rows_payload=write_payload.payload,
                state_rows_path=path,
            )
        if write_state_class_segment_index:
            self._write_snapshot_state_class_segment_index(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                object_instance_graph_id=object_instance_graph_id,
                graph_hash=graph_hash,
                state_index=state_index,
                state_rows_payload=write_payload.payload,
                state_rows_path=path,
            )
        _SESSION_SNAPSHOT_STATE_ROWS_READ_CACHE.store_path(
            path,
            payload=write_payload.payload,
            state_rows=state_index.rows,
        )
        return write_payload.payload

    async def get_snapshot_health_metadata(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> ObjectInstanceGraphSnapshotHealthMetadata | None:
        snapshot_path = (
            self._lane_dir(branch_id, projection_hash)
            / "snapshots"
            / f"{commit_id}.json"
        )
        if not snapshot_path.exists():
            return None
        file_size, file_mtime_ns, file_ctime_ns = _file_stat_payload(snapshot_path)
        health_path = self._snapshot_health_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        if not health_path.exists():
            return None
        payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
            health_path,
            log_prefix=f"Failed reading snapshot health metadata {commit_id}",
        )
        if payload is None:
            return None
        if payload.get("v") != OBJECT_INSTANCE_GRAPH_SNAPSHOT_HEALTH_INDEX_VERSION:
            return None
        if payload.get("branch_id") != str(branch_id):
            return None
        if payload.get("projection_hash") != projection_hash:
            return None
        if payload.get("commit_id") != str(commit_id):
            return None
        if _json_optional_int(payload, "file_size") != file_size:
            return None
        if _json_optional_int(payload, "file_mtime_ns") != file_mtime_ns:
            return None
        if _json_optional_int(payload, "file_ctime_ns") != file_ctime_ns:
            return None
        if _json_optional_string(payload, "file_sha256") != _file_sha256(snapshot_path):
            return None
        object_instance_graph_id = _json_optional_uuid(
            payload,
            "object_instance_graph_id",
        )
        graph_hash = _json_optional_string(payload, "graph_hash")
        file_sha256 = _json_optional_string(payload, "file_sha256")
        if object_instance_graph_id is None or graph_hash is None or not file_sha256:
            return None
        return ObjectInstanceGraphSnapshotHealthMetadata(
            commit_id=commit_id,
            object_instance_graph_id=object_instance_graph_id,
            graph_hash=graph_hash,
            file_size=file_size,
            file_mtime_ns=file_mtime_ns,
            file_ctime_ns=file_ctime_ns,
            file_sha256=file_sha256,
        )

    def write_snapshot_health_metadata(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        oig: ObjectInstanceGraph,
    ) -> None:
        self._write_snapshot_health_index(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            oig=oig,
        )

    async def get_snapshot_state_rows(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        expected_object_instance_graph_id: UUID | None = None,
        expected_graph_hash: str | None = None,
    ) -> JsonObject | None:
        snapshot_path = (
            self._lane_dir(branch_id, projection_hash)
            / "snapshots"
            / f"{commit_id}.json"
        )
        path = self._snapshot_state_rows_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        if not path.exists():
            return None
        trace_metadata = _snapshot_trace_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        with commit_perf_span(
            phase="oig_snapshot_store.state_rows.read_payload",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
                path,
                log_prefix=f"Failed reading snapshot state rows {commit_id}",
            )
        if payload is None:
            return None
        with commit_perf_span(
            phase="oig_snapshot_store.state_rows.validate_payload",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            if payload.get("v") != (
                OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_ROWS_INDEX_VERSION
            ):
                return None
            if (
                payload.get("schema")
                != OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_ROWS_SCHEMA
            ):
                return None
            if payload.get("branch_id") != str(branch_id):
                return None
            if payload.get("projection_hash") != projection_hash:
                return None
            if payload.get("commit_id") != str(commit_id):
                return None
            object_instance_graph_id = _json_optional_uuid(
                payload,
                "object_instance_graph_id",
            )
            graph_hash = _json_optional_string(payload, "graph_hash")
            if object_instance_graph_id is None or not graph_hash:
                return None
            if (
                expected_object_instance_graph_id is not None
                and object_instance_graph_id != expected_object_instance_graph_id
            ):
                return None
            if expected_graph_hash is not None and graph_hash != expected_graph_hash:
                return None
            if payload.get("payload_hash_algorithm") != (
                OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_ROWS_PAYLOAD_HASH_ALGORITHM
            ):
                return None
            if _json_optional_string(payload, "payload_sha256") != (
                _snapshot_state_rows_payload_hash(payload)
            ):
                return None
            if snapshot_path.exists():
                try:
                    file_size, file_mtime_ns, file_ctime_ns = _file_stat_payload(
                        snapshot_path,
                    )
                except Exception:
                    return None
                recorded_file_size = _json_optional_int(payload, "snapshot_file_size")
                recorded_file_mtime_ns = _json_optional_int(
                    payload,
                    "snapshot_file_mtime_ns",
                )
                recorded_file_ctime_ns = _json_optional_int(
                    payload,
                    "snapshot_file_ctime_ns",
                )
                if recorded_file_size is not None and recorded_file_size != file_size:
                    return None
                if (
                    recorded_file_mtime_ns is not None
                    and recorded_file_mtime_ns != file_mtime_ns
                ):
                    return None
                if (
                    recorded_file_ctime_ns is not None
                    and recorded_file_ctime_ns != file_ctime_ns
                ):
                    return None
            state_rows = _commit_state_rows_from_snapshot_payload(payload)
            if state_rows is None:
                return None
            if compute_commit_state_rows_hash(state_rows) != payload.get("state_hash"):
                return None
        return payload

    async def get_snapshot_state_rows_by_file_witness(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        expected_file_size: int,
        expected_file_mtime_ns: int,
        expected_file_ctime_ns: int,
        expected_payload_sha256: str,
        expected_state_hash: str,
        expected_object_instance_graph_id: UUID | None = None,
        expected_graph_hash: str | None = None,
    ) -> JsonObject | None:
        read = await self._get_snapshot_state_rows_read_by_file_witness(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            expected_file_size=expected_file_size,
            expected_file_mtime_ns=expected_file_mtime_ns,
            expected_file_ctime_ns=expected_file_ctime_ns,
            expected_payload_sha256=expected_payload_sha256,
            expected_state_hash=expected_state_hash,
            expected_object_instance_graph_id=expected_object_instance_graph_id,
            expected_graph_hash=expected_graph_hash,
            include_state_row_maps=False,
        )
        return read.payload if read is not None else None

    async def get_snapshot_state_witness_metadata(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        expected_object_instance_graph_id: UUID | None = None,
        expected_graph_hash: str | None = None,
        expected_state_hash: str | None = None,
        expected_witness_hash: str | None = None,
        expected_state_rows_payload_sha256: str | None = None,
    ) -> ObjectInstanceGraphSnapshotStateWitnessMetadata | None:
        try:
            state_rows_file_size, state_rows_file_mtime_ns, state_rows_file_ctime_ns = (
                _file_stat_payload(
                    self._snapshot_state_rows_index_path(
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        commit_id=commit_id,
                    )
                )
            )
        except Exception:
            return None
        return (
            await self.get_snapshot_state_witness_metadata_by_state_rows_file_witness(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                expected_state_rows_file_size=state_rows_file_size,
                expected_state_rows_file_mtime_ns=state_rows_file_mtime_ns,
                expected_state_rows_file_ctime_ns=state_rows_file_ctime_ns,
                expected_state_rows_payload_sha256=expected_state_rows_payload_sha256,
                expected_state_hash=expected_state_hash,
                expected_witness_hash=expected_witness_hash,
                expected_object_instance_graph_id=expected_object_instance_graph_id,
                expected_graph_hash=expected_graph_hash,
            )
        )

    async def get_snapshot_state_witness_metadata_by_state_rows_file_witness(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        expected_state_rows_file_size: int,
        expected_state_rows_file_mtime_ns: int,
        expected_state_rows_file_ctime_ns: int,
        expected_state_rows_payload_sha256: str | None = None,
        expected_state_hash: str | None = None,
        expected_witness_hash: str | None = None,
        expected_object_instance_graph_id: UUID | None = None,
        expected_graph_hash: str | None = None,
    ) -> ObjectInstanceGraphSnapshotStateWitnessMetadata | None:
        if (
            expected_state_rows_file_size < 0
            or expected_state_rows_file_mtime_ns < 0
            or expected_state_rows_file_ctime_ns < 0
        ):
            return None
        state_rows_path = self._snapshot_state_rows_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        trace_metadata = _snapshot_trace_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        with commit_perf_span(
            phase="oig_snapshot_store.state_witness.stat_state_rows",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            try:
                (
                    state_rows_file_size,
                    state_rows_file_mtime_ns,
                    state_rows_file_ctime_ns,
                ) = _file_stat_payload(state_rows_path)
            except Exception:
                return None
        if (
            state_rows_file_size != expected_state_rows_file_size
            or state_rows_file_mtime_ns != expected_state_rows_file_mtime_ns
            or state_rows_file_ctime_ns != expected_state_rows_file_ctime_ns
        ):
            return None
        witness_path = self._snapshot_state_witness_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        with commit_perf_span(
            phase="oig_snapshot_store.state_witness.read_payload",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
                witness_path,
                log_prefix=f"Failed reading snapshot state witness {commit_id}",
            )
        if payload is None:
            return None
        with commit_perf_span(
            phase="oig_snapshot_store.state_witness.validate_payload",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            if (
                payload.get("v")
                != OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_WITNESS_INDEX_VERSION
            ):
                return None
            if (
                payload.get("schema")
                != OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_WITNESS_SCHEMA
            ):
                return None
            if payload.get("branch_id") != str(branch_id):
                return None
            if payload.get("projection_hash") != projection_hash:
                return None
            if payload.get("commit_id") != str(commit_id):
                return None
            metadata = _snapshot_state_witness_metadata_from_payload(payload)
            if metadata is None:
                return None
            if (
                expected_object_instance_graph_id is not None
                and metadata.object_instance_graph_id
                != expected_object_instance_graph_id
            ):
                return None
            if (
                expected_graph_hash is not None
                and metadata.graph_hash != expected_graph_hash
            ):
                return None
            if (
                expected_state_hash is not None
                and metadata.state_hash != expected_state_hash
            ):
                return None
            if (
                expected_witness_hash is not None
                and metadata.witness_hash != expected_witness_hash
            ):
                return None
            if (
                expected_state_rows_payload_sha256 is not None
                and metadata.state_rows_payload_sha256
                != expected_state_rows_payload_sha256
            ):
                return None
            if (
                metadata.state_rows_file_size != state_rows_file_size
                or metadata.state_rows_file_mtime_ns != state_rows_file_mtime_ns
                or metadata.state_rows_file_ctime_ns != state_rows_file_ctime_ns
            ):
                return None
            if metadata.row_count != (
                metadata.node_count + metadata.attribute_count + metadata.edge_count
            ):
                return None
            if _json_optional_int(payload, "segment_count") != len(
                metadata.witness_ref.segments
            ):
                return None
        return metadata

    async def get_snapshot_state_class_segments_by_file_witness(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        class_instance_ids: Iterable[UUID],
        expected_state_rows_file_size: int,
        expected_state_rows_file_mtime_ns: int,
        expected_state_rows_file_ctime_ns: int,
        expected_state_rows_payload_sha256: str,
        expected_state_hash: str,
        expected_object_instance_graph_id: UUID | None = None,
        expected_graph_hash: str | None = None,
    ) -> ObjectInstanceGraphSnapshotStateClassSegmentSelection | None:
        selected_ids = {
            str(class_instance_id) for class_instance_id in class_instance_ids
        }
        if not selected_ids:
            return None
        witness_metadata = (
            await self.get_snapshot_state_witness_metadata_by_state_rows_file_witness(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                expected_state_rows_file_size=expected_state_rows_file_size,
                expected_state_rows_file_mtime_ns=expected_state_rows_file_mtime_ns,
                expected_state_rows_file_ctime_ns=expected_state_rows_file_ctime_ns,
                expected_state_rows_payload_sha256=expected_state_rows_payload_sha256,
                expected_state_hash=expected_state_hash,
                expected_object_instance_graph_id=expected_object_instance_graph_id,
                expected_graph_hash=expected_graph_hash,
            )
        )
        if witness_metadata is None:
            return None
        segment_refs_by_key = {
            segment.key: segment for segment in witness_metadata.witness_ref.segments
        }
        path = self._snapshot_state_class_segments_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        trace_metadata = _snapshot_trace_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        with commit_perf_span(
            phase="oig_snapshot_store.state_class_segments.read_payload",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
                path,
                log_prefix=f"Failed reading snapshot state class segments {commit_id}",
            )
        if payload is None:
            return None
        with commit_perf_span(
            phase="oig_snapshot_store.state_class_segments.validate_payload",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            if (
                payload.get("v")
                != OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENTS_INDEX_VERSION
            ):
                return None
            if (
                payload.get("schema")
                != OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENTS_SCHEMA
            ):
                return None
            if payload.get("branch_id") != str(branch_id):
                return None
            if payload.get("projection_hash") != projection_hash:
                return None
            if payload.get("commit_id") != str(commit_id):
                return None
            if payload.get("object_instance_graph_id") != str(
                witness_metadata.object_instance_graph_id
            ):
                return None
            if payload.get("graph_hash") != witness_metadata.graph_hash:
                return None
            embedded_witness = payload.get("state_witness")
            if not isinstance(embedded_witness, dict):
                return None
            embedded_metadata = _snapshot_state_witness_metadata_from_payload(
                _coerce_json_object_view(
                    embedded_witness,
                    error_message="Embedded state witness must be a JSON object",
                )
            )
            if embedded_metadata is None:
                return None
            if embedded_metadata.witness_ref != witness_metadata.witness_ref:
                return None
            raw_class_segments = payload.get("class_segments")
            if not isinstance(raw_class_segments, list):
                return None
            raw_segment_count = _json_optional_int(payload, "class_segment_count")
            if raw_segment_count != len(raw_class_segments):
                return None

        selected_segments: dict[
            UUID,
            ObjectInstanceGraphSnapshotStateClassSegment,
        ] = {}
        selected_class_instances: dict[UUID, ClassInstance] = {}
        with commit_perf_span(
            phase="oig_snapshot_store.state_class_segments.select",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata={**trace_metadata, "selected_count": len(selected_ids)},
        ):
            for raw_item in raw_class_segments:
                if not isinstance(raw_item, Mapping):
                    return None
                item = {
                    str(key): value
                    for key, value in raw_item.items()
                    if isinstance(key, str)
                }
                raw_class_instance_id = item.get("class_instance_id")
                if (
                    not isinstance(raw_class_instance_id, str)
                    or raw_class_instance_id not in selected_ids
                ):
                    continue
                rows_text = item.get("rows_text")
                if not isinstance(rows_text, str):
                    return None
                text_read = _commit_state_rows_read_from_text(rows_text)
                if text_read is None:
                    return None
                rows, _row_maps = text_read
                segment_payload = item.get("segment")
                try:
                    segment_ref = _commit_state_segment_ref_from_payload(
                        segment_payload
                    )
                except Exception:
                    return None
                expected_segment_ref = segment_refs_by_key.get(
                    f"class:{raw_class_instance_id}"
                )
                if segment_ref != expected_segment_ref:
                    return None
                if segment_ref.row_hash != compute_commit_state_rows_hash(rows):
                    return None
                snapshot_payload = item.get("snapshot_payload")
                if not isinstance(snapshot_payload, dict):
                    return None
                try:
                    class_instance = ClassInstance.model_validate(snapshot_payload)
                except Exception:
                    return None
                if class_instance.id is None:
                    return None
                class_instance_id = UUID(raw_class_instance_id)
                class_config_id = UUID(str(item.get("class_config_id")))
                raw_source_object_id = item.get("source_object_id")
                source_object_id = (
                    UUID(raw_source_object_id)
                    if isinstance(raw_source_object_id, str)
                    else None
                )
                selected_segments[class_instance_id] = (
                    ObjectInstanceGraphSnapshotStateClassSegment(
                        class_instance_id=class_instance_id,
                        class_config_id=class_config_id,
                        source_object_id=source_object_id,
                        rows=rows,
                        snapshot_payload=_coerce_json_object_view(
                            snapshot_payload,
                            error_message=(
                                "Selected class segment snapshot payload must be "
                                "a JSON object"
                            ),
                        ),
                    )
                )
                selected_class_instances[class_instance.id] = class_instance
        if set(selected_segments) != {UUID(raw_id) for raw_id in selected_ids}:
            return None
        return ObjectInstanceGraphSnapshotStateClassSegmentSelection(
            witness_metadata=witness_metadata,
            class_segments_by_id=selected_segments,
            class_instances_by_id=selected_class_instances,
        )

    async def get_snapshot_state_raw_class_segments_by_file_witness(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        class_instance_ids: Iterable[UUID],
        expected_state_rows_file_size: int,
        expected_state_rows_file_mtime_ns: int,
        expected_state_rows_file_ctime_ns: int,
        expected_state_rows_payload_sha256: str,
        expected_state_hash: str,
        expected_object_instance_graph_id: UUID | None = None,
        expected_graph_hash: str | None = None,
    ) -> ObjectInstanceGraphSnapshotStateRawClassSegmentSelection | None:
        selected_ids = {
            str(class_instance_id) for class_instance_id in class_instance_ids
        }
        if not selected_ids:
            return None
        witness_metadata = (
            await self.get_snapshot_state_witness_metadata_by_state_rows_file_witness(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                expected_state_rows_file_size=expected_state_rows_file_size,
                expected_state_rows_file_mtime_ns=expected_state_rows_file_mtime_ns,
                expected_state_rows_file_ctime_ns=expected_state_rows_file_ctime_ns,
                expected_state_rows_payload_sha256=expected_state_rows_payload_sha256,
                expected_state_hash=expected_state_hash,
                expected_object_instance_graph_id=expected_object_instance_graph_id,
                expected_graph_hash=expected_graph_hash,
            )
        )
        if witness_metadata is None:
            return None
        segment_refs_by_key = {
            segment.key: segment for segment in witness_metadata.witness_ref.segments
        }
        path = self._snapshot_state_class_segments_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        trace_metadata = _snapshot_trace_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        with commit_perf_span(
            phase="oig_snapshot_store.state_class_segments.raw_read_payload",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
                path,
                log_prefix=(
                    f"Failed reading raw snapshot state class segments {commit_id}"
                ),
            )
        if payload is None:
            return None
        with commit_perf_span(
            phase="oig_snapshot_store.state_class_segments.raw_validate_payload",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            if (
                payload.get("v")
                != OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENTS_INDEX_VERSION
            ):
                return None
            if (
                payload.get("schema")
                != OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENTS_SCHEMA
            ):
                return None
            if payload.get("branch_id") != str(branch_id):
                return None
            if payload.get("projection_hash") != projection_hash:
                return None
            if payload.get("commit_id") != str(commit_id):
                return None
            if payload.get("object_instance_graph_id") != str(
                witness_metadata.object_instance_graph_id
            ):
                return None
            if payload.get("graph_hash") != witness_metadata.graph_hash:
                return None
            embedded_witness = payload.get("state_witness")
            if not isinstance(embedded_witness, dict):
                return None
            embedded_metadata = _snapshot_state_witness_metadata_from_payload(
                _coerce_json_object_view(
                    embedded_witness,
                    error_message="Embedded state witness must be a JSON object",
                )
            )
            if embedded_metadata is None:
                return None
            if embedded_metadata.witness_ref != witness_metadata.witness_ref:
                return None
            raw_class_segments = payload.get("class_segments")
            if not isinstance(raw_class_segments, list):
                return None
            raw_segment_count = _json_optional_int(payload, "class_segment_count")
            if raw_segment_count != len(raw_class_segments):
                return None

        selected_segments: dict[
            UUID,
            ObjectInstanceGraphSnapshotStateRawClassSegment,
        ] = {}
        with commit_perf_span(
            phase="oig_snapshot_store.state_class_segments.raw_select",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata={**trace_metadata, "selected_count": len(selected_ids)},
        ):
            for raw_item in raw_class_segments:
                if not isinstance(raw_item, Mapping):
                    return None
                item = {
                    str(key): value
                    for key, value in raw_item.items()
                    if isinstance(key, str)
                }
                raw_class_instance_id = item.get("class_instance_id")
                if (
                    not isinstance(raw_class_instance_id, str)
                    or raw_class_instance_id not in selected_ids
                ):
                    continue
                rows_text = item.get("rows_text")
                if not isinstance(rows_text, str):
                    return None
                rows_text_hash = _commit_state_rows_text_hash_and_count(rows_text)
                if rows_text_hash is None:
                    return None
                row_hash, row_count = rows_text_hash
                segment_payload = item.get("segment")
                try:
                    segment_ref = _commit_state_segment_ref_from_payload(
                        segment_payload
                    )
                except Exception:
                    return None
                expected_segment_ref = segment_refs_by_key.get(
                    f"class:{raw_class_instance_id}"
                )
                if segment_ref != expected_segment_ref:
                    return None
                if segment_ref.row_hash != row_hash:
                    return None
                if segment_ref.row_count != row_count:
                    return None
                snapshot_payload = item.get("snapshot_payload")
                if not isinstance(snapshot_payload, dict):
                    return None
                class_instance_id = UUID(raw_class_instance_id)
                class_config_id = UUID(str(item.get("class_config_id")))
                raw_source_object_id = item.get("source_object_id")
                source_object_id = (
                    UUID(raw_source_object_id)
                    if isinstance(raw_source_object_id, str)
                    else None
                )
                selected_segments[class_instance_id] = (
                    ObjectInstanceGraphSnapshotStateRawClassSegment(
                        class_instance_id=class_instance_id,
                        class_config_id=class_config_id,
                        source_object_id=source_object_id,
                        rows_text=rows_text,
                        row_count=row_count,
                        row_hash=row_hash,
                        snapshot_payload=_coerce_json_object_view(
                            snapshot_payload,
                            error_message=(
                                "Selected raw class segment snapshot payload must be "
                                "a JSON object"
                            ),
                        ),
                        segment_ref=segment_ref,
                    )
                )
        if set(selected_segments) != {UUID(raw_id) for raw_id in selected_ids}:
            return None
        return ObjectInstanceGraphSnapshotStateRawClassSegmentSelection(
            witness_metadata=witness_metadata,
            class_segments_by_id=selected_segments,
        )

    async def get_snapshot_state_indexed_raw_class_segments_by_file_witness(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        class_instance_ids: Iterable[UUID],
        expected_state_rows_file_size: int,
        expected_state_rows_file_mtime_ns: int,
        expected_state_rows_file_ctime_ns: int,
        expected_state_rows_payload_sha256: str,
        expected_state_hash: str,
        expected_object_instance_graph_id: UUID | None = None,
        expected_graph_hash: str | None = None,
    ) -> ObjectInstanceGraphSnapshotStateRawClassSegmentSelection | None:
        selected_ids = {
            str(class_instance_id) for class_instance_id in class_instance_ids
        }
        if not selected_ids:
            return None
        witness_metadata = (
            await self.get_snapshot_state_witness_metadata_by_state_rows_file_witness(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                expected_state_rows_file_size=expected_state_rows_file_size,
                expected_state_rows_file_mtime_ns=expected_state_rows_file_mtime_ns,
                expected_state_rows_file_ctime_ns=expected_state_rows_file_ctime_ns,
                expected_state_rows_payload_sha256=expected_state_rows_payload_sha256,
                expected_state_hash=expected_state_hash,
                expected_object_instance_graph_id=expected_object_instance_graph_id,
                expected_graph_hash=expected_graph_hash,
            )
        )
        if witness_metadata is None:
            return None
        segment_refs_by_key = {
            segment.key: segment for segment in witness_metadata.witness_ref.segments
        }
        manifest_path = self._snapshot_state_class_segment_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        blob_path = self._snapshot_state_class_segment_blob_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        trace_metadata = _snapshot_trace_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        with commit_perf_span(
            phase="oig_snapshot_store.state_class_segment_index.read_manifest",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
                manifest_path,
                log_prefix=(
                    f"Failed reading snapshot state class segment index {commit_id}"
                ),
            )
        if payload is None:
            return None
        with commit_perf_span(
            phase="oig_snapshot_store.state_class_segment_index.validate_manifest",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            if (
                payload.get("v")
                != OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_INDEX_VERSION
            ):
                return None
            if (
                payload.get("schema")
                != OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_INDEX_SCHEMA
            ):
                return None
            if payload.get("branch_id") != str(branch_id):
                return None
            if payload.get("projection_hash") != projection_hash:
                return None
            if payload.get("commit_id") != str(commit_id):
                return None
            if payload.get("object_instance_graph_id") != str(
                witness_metadata.object_instance_graph_id
            ):
                return None
            if payload.get("graph_hash") != witness_metadata.graph_hash:
                return None
            embedded_witness = payload.get("state_witness")
            if not isinstance(embedded_witness, dict):
                return None
            embedded_metadata = _snapshot_state_witness_metadata_from_payload(
                _coerce_json_object_view(
                    embedded_witness,
                    error_message="Embedded state witness must be a JSON object",
                )
            )
            if embedded_metadata is None:
                return None
            if embedded_metadata.witness_ref != witness_metadata.witness_ref:
                return None
            raw_blob_metadata = payload.get("segment_blob")
            if not isinstance(raw_blob_metadata, Mapping):
                return None
            blob_metadata = {
                str(key): value
                for key, value in raw_blob_metadata.items()
                if isinstance(key, str)
            }
            if blob_metadata.get("file_name") != "segments.jsonl":
                return None
            blob_byte_size = _json_optional_int(blob_metadata, "byte_size")
            if blob_byte_size is None or blob_byte_size < 0:
                return None
            try:
                if blob_path.stat().st_size != blob_byte_size:
                    return None
            except Exception:
                return None
            raw_class_segments = payload.get("class_segments")
            if not isinstance(raw_class_segments, list):
                return None
            raw_segment_count = _json_optional_int(payload, "class_segment_count")
            if raw_segment_count != len(raw_class_segments):
                return None

            selected_refs: dict[str, JsonObject] = {}
            for raw_item in raw_class_segments:
                if not isinstance(raw_item, Mapping):
                    return None
                item = {
                    str(key): value
                    for key, value in raw_item.items()
                    if isinstance(key, str)
                }
                raw_class_instance_id = item.get("class_instance_id")
                if (
                    not isinstance(raw_class_instance_id, str)
                    or raw_class_instance_id not in selected_ids
                ):
                    continue
                if raw_class_instance_id in selected_refs:
                    return None
                selected_refs[raw_class_instance_id] = item
            if set(selected_refs) != selected_ids:
                return None

        selected_segments: dict[
            UUID,
            ObjectInstanceGraphSnapshotStateRawClassSegment,
        ] = {}
        with commit_perf_span(
            phase="oig_snapshot_store.state_class_segment_index.read_selected",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata={**trace_metadata, "selected_count": len(selected_ids)},
        ):
            try:
                for raw_class_instance_id, item in selected_refs.items():
                    byte_offset = _json_optional_int(item, "byte_offset")
                    byte_length = _json_optional_int(item, "byte_length")
                    record_sha256 = _json_optional_string(
                        item,
                        "record_sha256",
                    )
                    raw_blob_commit_id = _json_optional_string(
                        item, "blob_commit_id"
                    ) or str(commit_id)
                    if (
                        byte_offset is None
                        or byte_offset < 0
                        or byte_length is None
                        or byte_length <= 0
                        or not record_sha256
                    ):
                        return None
                    record_blob_path = self._snapshot_state_class_segment_blob_path(
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        commit_id=UUID(raw_blob_commit_id),
                    )
                    with open(record_blob_path, "rb") as file_handle:
                        file_handle.seek(byte_offset)
                        record_bytes = file_handle.read(byte_length)
                    if len(record_bytes) != byte_length:
                        return None
                    if hashlib.sha256(record_bytes).hexdigest() != record_sha256:
                        return None
                    try:
                        raw_record = json.loads(record_bytes.decode("utf-8"))
                    except Exception:
                        return None
                    if not isinstance(raw_record, dict):
                        return None
                    record = {
                        str(key): value
                        for key, value in raw_record.items()
                        if isinstance(key, str)
                    }
                    selected_segment = _raw_class_segment_from_payload(
                        raw_class_instance_id=raw_class_instance_id,
                        item=record,
                        segment_refs_by_key=segment_refs_by_key,
                    )
                    if selected_segment is None:
                        return None
                    selected_segments[selected_segment.class_instance_id] = (
                        selected_segment
                    )
            except Exception:
                return None
        if set(selected_segments) != {UUID(raw_id) for raw_id in selected_ids}:
            return None
        return ObjectInstanceGraphSnapshotStateRawClassSegmentSelection(
            witness_metadata=witness_metadata,
            class_segments_by_id=selected_segments,
        )

    def _read_snapshot_state_indexed_raw_class_segment_records(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        selected_refs: Mapping[str, JsonObject],
        segment_refs_by_key: Mapping[str, CommitStateSegmentRef],
    ) -> dict[UUID, ObjectInstanceGraphSnapshotStateRawClassSegment] | None:
        selected_segments: dict[
            UUID,
            ObjectInstanceGraphSnapshotStateRawClassSegment,
        ] = {}
        trace_metadata = {
            **_snapshot_trace_metadata(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
            ),
            "selected_count": len(selected_refs),
        }
        try:
            for raw_class_instance_id, item in selected_refs.items():
                with commit_perf_span(
                    phase=(
                        "oig_snapshot_store.state_class_segment_records." "prepare_ref"
                    ),
                    category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                    metadata=trace_metadata,
                ):
                    byte_offset = _json_required_int(item, "byte_offset")
                    byte_length = _json_required_int(item, "byte_length")
                    record_sha256 = _json_required_string(
                        item,
                        "record_sha256",
                    )
                    raw_blob_commit_id = _json_optional_string(
                        item, "blob_commit_id"
                    ) or str(commit_id)
                    if byte_offset < 0 or byte_length <= 0:
                        return None
                    record_blob_path = self._snapshot_state_class_segment_blob_path(
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        commit_id=UUID(raw_blob_commit_id),
                    )
                with commit_perf_span(
                    phase=("oig_snapshot_store.state_class_segment_records.blob_read"),
                    category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                    metadata={**trace_metadata, "byte_length": byte_length},
                ):
                    with open(record_blob_path, "rb") as file_handle:
                        file_handle.seek(byte_offset)
                        record_bytes = file_handle.read(byte_length)
                    if len(record_bytes) != byte_length:
                        return None
                with commit_perf_span(
                    phase=("oig_snapshot_store.state_class_segment_records.hash_check"),
                    category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                    metadata=trace_metadata,
                ):
                    if hashlib.sha256(record_bytes).hexdigest() != record_sha256:
                        return None
                with commit_perf_span(
                    phase=(
                        "oig_snapshot_store.state_class_segment_records.json_decode"
                    ),
                    category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                    metadata=trace_metadata,
                ):
                    raw_record = json.loads(record_bytes.decode("utf-8"))
                    if not isinstance(raw_record, dict):
                        return None
                    record = {
                        str(key): value
                        for key, value in raw_record.items()
                        if isinstance(key, str)
                    }
                with commit_perf_span(
                    phase=(
                        "oig_snapshot_store.state_class_segment_records."
                        "payload_decode"
                    ),
                    category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                    metadata=trace_metadata,
                ):
                    selected_segment = _raw_class_segment_from_payload(
                        raw_class_instance_id=raw_class_instance_id,
                        item=record,
                        segment_refs_by_key=segment_refs_by_key,
                    )
                if selected_segment is None:
                    return None
                selected_segments[selected_segment.class_instance_id] = selected_segment
        except Exception:
            return None
        return selected_segments

    def _snapshot_state_class_segment_cursor_summary_from_payload(
        self,
        *,
        payload: JsonObject,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        expected_object_instance_graph_id: UUID | None,
        expected_graph_hash: str | None,
    ) -> CommitStateWitnessCursorSummary | None:
        if payload.get("branch_id") != str(branch_id):
            return None
        if payload.get("projection_hash") != projection_hash:
            return None
        if payload.get("commit_id") != str(commit_id):
            return None
        try:
            object_instance_graph_id = _json_required_uuid(
                payload,
                "object_instance_graph_id",
            )
        except Exception:
            return None
        if (
            expected_object_instance_graph_id is not None
            and object_instance_graph_id != expected_object_instance_graph_id
        ):
            return None
        graph_hash = _json_optional_string(payload, "graph_hash")
        if not graph_hash:
            return None
        if expected_graph_hash is not None and graph_hash != expected_graph_hash:
            return None
        if (payload.get("graph_hash_source") or "state_hash") != "witness_cursor_hash":
            return None
        summary = _commit_state_witness_cursor_summary_from_payload(
            payload.get("state_witness_cursor"),
        )
        if summary is None or summary.cursor_hash != graph_hash:
            return None
        return summary

    def _state_witness_cursor_selected_segment_refs_from_index_payload(
        self,
        *,
        payload: JsonObject,
        summary: CommitStateWitnessCursorSummary,
        selected_segment_keys: set[str],
    ) -> (
        tuple[
            dict[str, CommitStateSegmentRef],
            dict[int, CommitStateWitnessCursorChunk],
            dict[str, CommitStateWitnessCursorChunkSummary],
        ]
        | None
    ):
        with commit_perf_span(
            phase=(
                "oig_snapshot_store.state_class_segment_cursor." "select_chunk_indexes"
            ),
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata={
                "selected_segment_count": len(selected_segment_keys),
                "summary_chunk_count": len(summary.chunks),
            },
        ):
            selected_chunk_indexes = (
                self._state_witness_cursor_selected_chunk_indexes_from_index_payload(
                    payload=payload,
                    selected_segment_keys=selected_segment_keys,
                )
            )
        if selected_chunk_indexes is None:
            return None
        with commit_perf_span(
            phase=(
                "oig_snapshot_store.state_class_segment_cursor." "parse_selected_chunks"
            ),
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata={
                "selected_chunk_count": len(selected_chunk_indexes),
                "selected_segment_count": len(selected_segment_keys),
            },
        ):
            chunks = self._state_witness_cursor_chunks_from_index_payload(
                payload=payload,
                summary=summary,
                selected_chunk_indexes=selected_chunk_indexes,
            )
        if chunks is None:
            return None
        return self._state_witness_cursor_selected_segment_refs_from_chunks(
            chunks=chunks,
            summary=summary,
            selected_segment_keys=selected_segment_keys,
        )

    @staticmethod
    def _state_witness_cursor_selected_chunk_indexes_from_index_payload(
        *,
        payload: JsonObject,
        selected_segment_keys: set[str],
    ) -> set[int] | None:
        raw_chunks = payload.get("state_witness_cursor_chunks")
        if raw_chunks is None:
            return set()
        if not isinstance(raw_chunks, list):
            return None
        selected_chunk_indexes: set[int] = set()
        for raw_chunk in raw_chunks:
            if not isinstance(raw_chunk, Mapping):
                return None
            raw_index = raw_chunk.get("index")
            if not isinstance(raw_index, int) or isinstance(raw_index, bool):
                return None
            raw_segment_keys = raw_chunk.get("segment_keys")
            if not isinstance(raw_segment_keys, list):
                return None
            for raw_key in raw_segment_keys:
                if not isinstance(raw_key, str):
                    return None
                if raw_key in selected_segment_keys:
                    selected_chunk_indexes.add(raw_index)
                    break
        return selected_chunk_indexes

    def _state_witness_cursor_selected_segment_refs_from_chunks(
        self,
        *,
        chunks: tuple[CommitStateWitnessCursorChunk, ...],
        summary: CommitStateWitnessCursorSummary,
        selected_segment_keys: set[str],
    ) -> (
        tuple[
            dict[str, CommitStateSegmentRef],
            dict[int, CommitStateWitnessCursorChunk],
            dict[str, CommitStateWitnessCursorChunkSummary],
        ]
        | None
    ):
        summary_chunks_by_index = {chunk.index: chunk for chunk in summary.chunks}
        if len(summary_chunks_by_index) != len(summary.chunks):
            return None
        segment_refs_by_key: dict[str, CommitStateSegmentRef] = {}
        cursor_chunks_by_index: dict[int, CommitStateWitnessCursorChunk] = {}
        chunk_summaries_by_segment_key: dict[str, CommitStateWitnessCursorChunkSummary]
        chunk_summaries_by_segment_key = {}
        for chunk in chunks:
            summary_chunk = summary_chunks_by_index.get(chunk.index)
            if summary_chunk is None:
                return None
            for segment in chunk.segments:
                if segment.key not in selected_segment_keys:
                    continue
                if segment.key in segment_refs_by_key:
                    return None
                cursor_chunks_by_index[chunk.index] = chunk
                segment_refs_by_key[segment.key] = segment
                chunk_summaries_by_segment_key[segment.key] = summary_chunk
        return (
            segment_refs_by_key,
            cursor_chunks_by_index,
            chunk_summaries_by_segment_key,
        )

    def _read_snapshot_state_class_segment_cursor_key_index_sidecars(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        selected_ids: set[str],
        expected_cursor_summary: CommitStateWitnessCursorSummary,
        expected_object_instance_graph_id: UUID | None,
        expected_graph_hash: str | None,
    ) -> dict[str, int] | None:
        selected_ids_by_bucket: dict[str, set[str]] = {}
        for raw_id in selected_ids:
            bucket = _snapshot_state_class_segment_cursor_key_index_bucket(raw_id)
            if bucket is None:
                return None
            selected_ids_by_bucket.setdefault(bucket, set()).add(raw_id)
        chunk_indexes_by_key: dict[str, int] = {}
        summary_chunk_indexes = {
            chunk.index for chunk in expected_cursor_summary.chunks
        }
        for bucket, bucket_selected_ids in selected_ids_by_bucket.items():
            sidecar_path = (
                self._snapshot_state_class_segment_cursor_key_index_sidecar_path(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    commit_id=commit_id,
                    bucket_key=bucket,
                )
            )
            payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
                sidecar_path,
                log_prefix=(
                    "Failed reading snapshot state class segment cursor key "
                    f"index sidecar {commit_id}:{bucket}"
                ),
            )
            if payload is None:
                return None
            if (
                payload.get("schema")
                != _SNAPSHOT_STATE_CLASS_SEGMENT_CURSOR_KEY_INDEX_SIDECAR_SCHEMA
            ):
                return None
            if (
                payload.get("v")
                != _SNAPSHOT_STATE_CLASS_SEGMENT_CURSOR_KEY_INDEX_SIDECAR_VERSION
            ):
                return None
            if payload.get("branch_id") != str(branch_id):
                return None
            if payload.get("projection_hash") != projection_hash:
                return None
            if payload.get("commit_id") != str(commit_id):
                return None
            if payload.get("bucket") != bucket:
                return None
            if payload.get("state_witness_cursor_hash") != (
                expected_cursor_summary.cursor_hash
            ):
                return None
            try:
                object_instance_graph_id = _json_required_uuid(
                    payload,
                    "object_instance_graph_id",
                )
                graph_hash = _json_required_string(payload, "graph_hash")
            except Exception:
                return None
            if (
                expected_object_instance_graph_id is not None
                and object_instance_graph_id != expected_object_instance_graph_id
            ):
                return None
            if expected_graph_hash is not None and graph_hash != expected_graph_hash:
                return None
            raw_chunk_indexes = payload.get("class_chunk_indexes")
            if not isinstance(raw_chunk_indexes, Mapping):
                return None
            raw_count = _json_optional_int(payload, "class_chunk_index_count")
            if raw_count != len(raw_chunk_indexes):
                return None
            for raw_id in bucket_selected_ids:
                raw_chunk_index = raw_chunk_indexes.get(raw_id)
                if (
                    not isinstance(raw_chunk_index, int)
                    or isinstance(raw_chunk_index, bool)
                    or raw_chunk_index not in summary_chunk_indexes
                ):
                    return None
                chunk_indexes_by_key[f"class:{raw_id}"] = raw_chunk_index
        return chunk_indexes_by_key

    def _read_snapshot_state_class_segment_cursor_chunk_sidecar(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        selected_ids: set[str],
        expected_cursor_summary: CommitStateWitnessCursorSummary,
        summary_chunk: CommitStateWitnessCursorChunkSummary,
        expected_object_instance_graph_id: UUID | None,
        expected_graph_hash: str | None,
    ) -> tuple[JsonObject, CommitStateWitnessCursorChunk, dict[str, JsonObject]] | None:
        sidecar_path = self._snapshot_state_class_segment_cursor_chunk_sidecar_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            chunk_index=summary_chunk.index,
        )
        payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
            sidecar_path,
            log_prefix=(
                "Failed reading snapshot state class segment cursor chunk sidecar "
                f"{commit_id}:{summary_chunk.index}"
            ),
        )
        if payload is None:
            return None
        if (
            payload.get("schema")
            != _SNAPSHOT_STATE_CLASS_SEGMENT_CURSOR_CHUNK_SIDECAR_SCHEMA
        ):
            return None
        if (
            payload.get("v")
            != _SNAPSHOT_STATE_CLASS_SEGMENT_CURSOR_CHUNK_SIDECAR_VERSION
        ):
            return None
        if payload.get("branch_id") != str(branch_id):
            return None
        if payload.get("projection_hash") != projection_hash:
            return None
        if payload.get("commit_id") != str(commit_id):
            return None
        if payload.get("chunk_index") != summary_chunk.index:
            return None
        if payload.get("state_witness_cursor_hash") != (
            expected_cursor_summary.cursor_hash
        ):
            return None
        try:
            object_instance_graph_id = _json_required_uuid(
                payload,
                "object_instance_graph_id",
            )
            graph_hash = _json_required_string(payload, "graph_hash")
        except Exception:
            return None
        if (
            expected_object_instance_graph_id is not None
            and object_instance_graph_id != expected_object_instance_graph_id
        ):
            return None
        if expected_graph_hash is not None and graph_hash != expected_graph_hash:
            return None
        blob_path = self._snapshot_state_class_segment_blob_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        if not self._snapshot_state_class_segment_blob_metadata_valid(
            payload=payload,
            blob_path=blob_path,
        ):
            return None
        chunk = _commit_state_witness_cursor_chunk_from_payload(
            payload.get("state_witness_cursor_chunk"),
        )
        if chunk is None:
            return None
        try:
            self._require_matching_state_witness_cursor_chunk_summary(
                chunk=chunk,
                summary_chunk=summary_chunk,
            )
        except ValueError:
            return None
        selected_refs = self._snapshot_state_class_segment_selected_refs_from_payload(
            payload=payload,
            selected_ids=selected_ids,
            field_name="class_segments",
            count_field_name="class_segment_count",
        )
        if selected_refs is None or set(selected_refs) != selected_ids:
            return None
        return payload, chunk, selected_refs

    def _get_snapshot_state_indexed_raw_class_segments_from_cursor_chunk_sidecars(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        selected_ids: set[str],
        expected_cursor_summary: CommitStateWitnessCursorSummary,
        expected_object_instance_graph_id: UUID | None,
        expected_graph_hash: str | None,
    ) -> _CursorSelectedSegmentRead | None:
        trace_metadata = _snapshot_trace_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        selected_segment_keys = {f"class:{raw_id}" for raw_id in selected_ids}
        with commit_perf_span(
            phase=(
                "oig_snapshot_store.state_class_segment_cursor." "chunk_key_index_read"
            ),
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata={
                **trace_metadata,
                "selected_count": len(selected_segment_keys),
                "summary_chunk_count": len(expected_cursor_summary.chunks),
            },
        ):
            chunk_indexes_by_key = (
                self._read_snapshot_state_class_segment_cursor_key_index_sidecars(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    commit_id=commit_id,
                    selected_ids=selected_ids,
                    expected_cursor_summary=expected_cursor_summary,
                    expected_object_instance_graph_id=(
                        expected_object_instance_graph_id
                    ),
                    expected_graph_hash=expected_graph_hash,
                )
            )
        if chunk_indexes_by_key is None:
            return None
        selected_ids_by_chunk: dict[int, set[str]] = {}
        for raw_id in selected_ids:
            chunk_index = chunk_indexes_by_key.get(f"class:{raw_id}")
            if chunk_index is None:
                return None
            selected_ids_by_chunk.setdefault(chunk_index, set()).add(raw_id)
        summary_chunks_by_index = {
            chunk.index: chunk for chunk in expected_cursor_summary.chunks
        }
        selected_segments: dict[
            UUID,
            ObjectInstanceGraphSnapshotStateRawClassSegment,
        ] = {}
        cursor_chunks_by_index: dict[int, CommitStateWitnessCursorChunk] = {}
        segment_refs_by_key: dict[str, CommitStateSegmentRef] = {}
        chunk_summaries_by_segment_key: dict[
            str,
            CommitStateWitnessCursorChunkSummary,
        ] = {}
        first_payload: JsonObject | None = None
        object_instance_graph_id: UUID | None = None
        graph_hash: str | None = None
        for chunk_index in sorted(selected_ids_by_chunk):
            summary_chunk = summary_chunks_by_index.get(chunk_index)
            if summary_chunk is None:
                return None
            with commit_perf_span(
                phase=(
                    "oig_snapshot_store.state_class_segment_cursor."
                    "chunk_sidecar_read"
                ),
                category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                metadata={**trace_metadata, "chunk_index": chunk_index},
            ):
                sidecar = self._read_snapshot_state_class_segment_cursor_chunk_sidecar(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    commit_id=commit_id,
                    selected_ids=selected_ids_by_chunk[chunk_index],
                    expected_cursor_summary=expected_cursor_summary,
                    summary_chunk=summary_chunk,
                    expected_object_instance_graph_id=(
                        expected_object_instance_graph_id
                    ),
                    expected_graph_hash=expected_graph_hash,
                )
            if sidecar is None:
                return None
            payload, chunk, selected_refs = sidecar
            if first_payload is None:
                first_payload = payload
                try:
                    object_instance_graph_id = _json_required_uuid(
                        payload,
                        "object_instance_graph_id",
                    )
                    graph_hash = _json_required_string(payload, "graph_hash")
                except Exception:
                    return None
            for segment in chunk.segments:
                existing_segment = segment_refs_by_key.get(segment.key)
                if existing_segment is not None and existing_segment != segment:
                    return None
                segment_refs_by_key[segment.key] = segment
            selected_keys_for_chunk = {
                f"class:{raw_id}" for raw_id in selected_ids_by_chunk[chunk_index]
            }
            if not selected_keys_for_chunk <= set(segment_refs_by_key):
                return None
            with commit_perf_span(
                phase=(
                    "oig_snapshot_store.state_class_segment_cursor."
                    "chunk_sidecar_read_records"
                ),
                category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                metadata={
                    **trace_metadata,
                    "chunk_index": chunk_index,
                    "selected_ref_count": len(selected_refs),
                },
            ):
                selected_chunk_segments = (
                    self._read_snapshot_state_indexed_raw_class_segment_records(
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        commit_id=commit_id,
                        selected_refs=selected_refs,
                        segment_refs_by_key=segment_refs_by_key,
                    )
                )
            if selected_chunk_segments is None:
                return None
            selected_segments.update(selected_chunk_segments)
            cursor_chunks_by_index[chunk.index] = chunk
            for selected_key in selected_keys_for_chunk:
                chunk_summaries_by_segment_key[selected_key] = summary_chunk
        if (
            first_payload is None
            or object_instance_graph_id is None
            or graph_hash is None
        ):
            return None
        return _CursorSelectedSegmentRead(
            payload=first_payload,
            object_instance_graph_id=object_instance_graph_id,
            graph_hash=graph_hash,
            cursor_summary=expected_cursor_summary,
            class_segments_by_id=selected_segments,
            cursor_chunks_by_index=cursor_chunks_by_index,
            segment_refs_by_key=segment_refs_by_key,
            chunk_summaries_by_segment_key=chunk_summaries_by_segment_key,
        )

    async def _get_snapshot_state_indexed_raw_class_segments_from_cursor_payload(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        payload: JsonObject,
        selected_ids: set[str],
        expected_cursor_summary: CommitStateWitnessCursorSummary,
        expected_object_instance_graph_id: UUID | None,
        expected_graph_hash: str | None,
        visited_commit_ids: set[UUID],
        depth: int,
    ) -> _CursorSelectedSegmentRead | None:
        if depth > _SNAPSHOT_STATE_CLASS_SEGMENT_OVERLAY_MAX_DEPTH:
            return None
        if commit_id in visited_commit_ids:
            return None
        visited_commit_ids.add(commit_id)
        trace_metadata = {
            **_snapshot_trace_metadata(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
            ),
            "depth": depth,
            "selected_count": len(selected_ids),
        }
        with commit_perf_span(
            phase="oig_snapshot_store.state_class_segment_cursor.validate_summary",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            summary = self._snapshot_state_class_segment_cursor_summary_from_payload(
                payload=payload,
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                expected_object_instance_graph_id=expected_object_instance_graph_id,
                expected_graph_hash=expected_graph_hash,
            )
        if summary is None or summary != expected_cursor_summary:
            return None
        blob_path = self._snapshot_state_class_segment_blob_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        with commit_perf_span(
            phase="oig_snapshot_store.state_class_segment_cursor.blob_metadata",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            if not self._snapshot_state_class_segment_blob_metadata_valid(
                payload=payload,
                blob_path=blob_path,
            ):
                return None
        selected_segment_keys = {f"class:{raw_id}" for raw_id in selected_ids}
        with commit_perf_span(
            phase="oig_snapshot_store.state_class_segment_cursor.extract_refs",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            cursor_refs = (
                self._state_witness_cursor_selected_segment_refs_from_index_payload(
                    payload=payload,
                    summary=summary,
                    selected_segment_keys=selected_segment_keys,
                )
            )
        if cursor_refs is None:
            return None
        (
            segment_refs_by_key,
            cursor_chunks_by_index,
            chunk_summaries_by_segment_key,
        ) = cursor_refs
        schema = payload.get("schema")
        if (
            schema
            == OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_OVERLAY_INDEX_SCHEMA
        ):
            with commit_perf_span(
                phase=(
                    "oig_snapshot_store.state_class_segment_cursor."
                    "overlay_selected_refs"
                ),
                category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                metadata=trace_metadata,
            ):
                selected_refs = (
                    self._snapshot_state_class_segment_selected_refs_from_payload(
                        payload=payload,
                        selected_ids=selected_ids,
                        field_name="replacement_class_segments",
                        count_field_name="replacement_class_segment_count",
                    )
                )
            if selected_refs is None:
                return None
            selected_ref_keys = {f"class:{raw_id}" for raw_id in selected_refs}
            if not selected_ref_keys <= set(segment_refs_by_key):
                return None
            with commit_perf_span(
                phase=(
                    "oig_snapshot_store.state_class_segment_cursor."
                    "read_overlay_records"
                ),
                category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                metadata={**trace_metadata, "selected_ref_count": len(selected_refs)},
            ):
                selected_segments = (
                    self._read_snapshot_state_indexed_raw_class_segment_records(
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        commit_id=commit_id,
                        selected_refs=selected_refs,
                        segment_refs_by_key=segment_refs_by_key,
                    )
                )
            if selected_segments is None:
                return None
            missing_ids = selected_ids - set(selected_refs)
            if missing_ids:
                raw_base_commit_id = _json_optional_string(payload, "base_commit_id")
                if raw_base_commit_id is None:
                    return None
                try:
                    base_commit_id = UUID(raw_base_commit_id)
                except Exception:
                    return None
                base_manifest_path = self._snapshot_state_class_segment_index_path(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    commit_id=base_commit_id,
                )
                with commit_perf_span(
                    phase=(
                        "oig_snapshot_store.state_class_segment_cursor."
                        "base_manifest_read"
                    ),
                    category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                    metadata={**trace_metadata, "missing_count": len(missing_ids)},
                ):
                    base_payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
                        base_manifest_path,
                        log_prefix=(
                            "Failed reading base snapshot state class segment "
                            f"index {base_commit_id}"
                        ),
                    )
                if base_payload is None:
                    return None
                base_summary = (
                    self._snapshot_state_class_segment_cursor_summary_from_payload(
                        payload=base_payload,
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        commit_id=base_commit_id,
                        expected_object_instance_graph_id=(
                            expected_object_instance_graph_id
                        ),
                        expected_graph_hash=None,
                    )
                )
                if base_summary is None:
                    return None
                with commit_perf_span(
                    phase=(
                        "oig_snapshot_store.state_class_segment_cursor."
                        "base_recursion"
                    ),
                    category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                    metadata={**trace_metadata, "missing_count": len(missing_ids)},
                ):
                    base_read = await self._get_snapshot_state_indexed_raw_class_segments_from_cursor_payload(
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        commit_id=base_commit_id,
                        payload=base_payload,
                        selected_ids=missing_ids,
                        expected_cursor_summary=base_summary,
                        expected_object_instance_graph_id=(
                            expected_object_instance_graph_id
                        ),
                        expected_graph_hash=None,
                        visited_commit_ids=visited_commit_ids,
                        depth=depth + 1,
                    )
                if base_read is None:
                    return None
                with commit_perf_span(
                    phase=(
                        "oig_snapshot_store.state_class_segment_cursor."
                        "merge_base_selection"
                    ),
                    category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                    metadata={**trace_metadata, "missing_count": len(missing_ids)},
                ):
                    summary_chunks_by_index = {
                        item.index: item for item in summary.chunks
                    }
                    for raw_id in missing_ids:
                        key = f"class:{raw_id}"
                        base_chunk_summary = (
                            base_read.chunk_summaries_by_segment_key.get(key)
                        )
                        if base_chunk_summary is None:
                            return None
                        current_chunk_summary = summary_chunks_by_index.get(
                            base_chunk_summary.index,
                        )
                        current_segment_ref = segment_refs_by_key.get(key)
                        if current_segment_ref is not None:
                            if (
                                current_segment_ref
                                != base_read.segment_refs_by_key.get(key)
                            ):
                                return None
                        elif current_chunk_summary != base_chunk_summary:
                            return None
                        else:
                            chunk_summaries_by_segment_key[key] = base_chunk_summary
                            segment_refs_by_key[key] = base_read.segment_refs_by_key[
                                key
                            ]
                            cursor_chunks_by_index.update(
                                base_read.cursor_chunks_by_index
                            )
                            continue
                        if current_chunk_summary is None:
                            return None
                        chunk_summaries_by_segment_key[key] = current_chunk_summary
                        segment_refs_by_key[key] = base_read.segment_refs_by_key[key]
                        cursor_chunks_by_index.update(base_read.cursor_chunks_by_index)
                    selected_segments.update(base_read.class_segments_by_id)
            return _CursorSelectedSegmentRead(
                payload=payload,
                object_instance_graph_id=_json_required_uuid(
                    payload,
                    "object_instance_graph_id",
                ),
                graph_hash=_json_required_string(payload, "graph_hash"),
                cursor_summary=summary,
                class_segments_by_id=selected_segments,
                cursor_chunks_by_index=cursor_chunks_by_index,
                segment_refs_by_key=segment_refs_by_key,
                chunk_summaries_by_segment_key=chunk_summaries_by_segment_key,
            )

        if (
            schema
            != OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_REF_INDEX_SCHEMA
        ):
            return None
        with commit_perf_span(
            phase=(
                "oig_snapshot_store.state_class_segment_cursor." "direct_selected_refs"
            ),
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            selected_refs = (
                self._snapshot_state_class_segment_selected_refs_from_payload(
                    payload=payload,
                    selected_ids=selected_ids,
                    field_name="class_segments",
                    count_field_name="class_segment_count",
                )
            )
        if selected_refs is None or set(selected_refs) != selected_ids:
            return None
        if selected_segment_keys != set(segment_refs_by_key):
            return None
        with commit_perf_span(
            phase=(
                "oig_snapshot_store.state_class_segment_cursor." "read_direct_records"
            ),
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata={**trace_metadata, "selected_ref_count": len(selected_refs)},
        ):
            selected_segments = (
                self._read_snapshot_state_indexed_raw_class_segment_records(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    commit_id=commit_id,
                    selected_refs=selected_refs,
                    segment_refs_by_key=segment_refs_by_key,
                )
            )
        if selected_segments is None:
            return None
        return _CursorSelectedSegmentRead(
            payload=payload,
            object_instance_graph_id=_json_required_uuid(
                payload,
                "object_instance_graph_id",
            ),
            graph_hash=_json_required_string(payload, "graph_hash"),
            cursor_summary=summary,
            class_segments_by_id=selected_segments,
            cursor_chunks_by_index=cursor_chunks_by_index,
            segment_refs_by_key=segment_refs_by_key,
            chunk_summaries_by_segment_key=chunk_summaries_by_segment_key,
        )

    async def _get_snapshot_state_indexed_raw_class_segments_from_ref_payload(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        payload: JsonObject,
        selected_ids: set[str],
        expected_witness_ref: CommitStateWitnessRef,
        expected_segment_refs_by_key: Mapping[str, CommitStateSegmentRef],
        expected_object_instance_graph_id: UUID | None,
        expected_graph_hash: str | None,
        require_witness_ref: bool,
        visited_commit_ids: set[UUID],
        depth: int,
        prevalidated_metadata: (
            ObjectInstanceGraphSnapshotStateSegmentIndexMetadata | None
        ) = None,
    ) -> dict[UUID, ObjectInstanceGraphSnapshotStateRawClassSegment] | None:
        if depth > _SNAPSHOT_STATE_CLASS_SEGMENT_OVERLAY_MAX_DEPTH:
            return None
        if commit_id in visited_commit_ids:
            return None
        visited_commit_ids.add(commit_id)
        metadata = prevalidated_metadata or (
            self._snapshot_state_class_segment_index_metadata_from_payload(
                payload=payload,
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                expected_object_instance_graph_id=expected_object_instance_graph_id,
                expected_graph_hash=expected_graph_hash,
            )
        )
        if metadata is None:
            return None
        if require_witness_ref and metadata.witness_ref != expected_witness_ref:
            return None
        blob_path = self._snapshot_state_class_segment_blob_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        schema = payload.get("schema")
        if (
            schema
            == OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_OVERLAY_INDEX_SCHEMA
        ):
            if (
                payload.get("v")
                != OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_OVERLAY_INDEX_VERSION
            ):
                return None
            if not self._snapshot_state_class_segment_blob_metadata_valid(
                payload=payload,
                blob_path=blob_path,
            ):
                return None
            selected_refs = (
                self._snapshot_state_class_segment_selected_refs_from_payload(
                    payload=payload,
                    selected_ids=selected_ids,
                    field_name="replacement_class_segments",
                    count_field_name="replacement_class_segment_count",
                )
            )
            if selected_refs is None:
                return None
            selected_segments = (
                self._read_snapshot_state_indexed_raw_class_segment_records(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    commit_id=commit_id,
                    selected_refs=selected_refs,
                    segment_refs_by_key=expected_segment_refs_by_key,
                )
            )
            if selected_segments is None:
                return None
            missing_ids = selected_ids - set(selected_refs)
            if missing_ids:
                raw_base_commit_id = _json_optional_string(payload, "base_commit_id")
                if raw_base_commit_id is None:
                    return None
                try:
                    base_commit_id = UUID(raw_base_commit_id)
                except Exception:
                    return None
                base_manifest_path = self._snapshot_state_class_segment_index_path(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    commit_id=base_commit_id,
                )
                base_payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
                    base_manifest_path,
                    log_prefix=(
                        "Failed reading base snapshot state class segment "
                        f"index {base_commit_id}"
                    ),
                )
                if base_payload is None:
                    return None
                base_segments = await self._get_snapshot_state_indexed_raw_class_segments_from_ref_payload(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    commit_id=base_commit_id,
                    payload=base_payload,
                    selected_ids=missing_ids,
                    expected_witness_ref=expected_witness_ref,
                    expected_segment_refs_by_key=expected_segment_refs_by_key,
                    expected_object_instance_graph_id=(
                        expected_object_instance_graph_id
                    ),
                    expected_graph_hash=None,
                    require_witness_ref=False,
                    visited_commit_ids=visited_commit_ids,
                    depth=depth + 1,
                )
                if base_segments is None:
                    return None
                selected_segments.update(base_segments)
            return selected_segments

        if (
            schema
            == OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_REF_INDEX_SCHEMA
        ):
            if (
                payload.get("v")
                != OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_REF_INDEX_VERSION
            ):
                return None
        elif schema == OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_INDEX_SCHEMA:
            if (
                payload.get("v")
                != OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_INDEX_VERSION
            ):
                return None
        else:
            return None
        if not self._snapshot_state_class_segment_blob_metadata_valid(
            payload=payload,
            blob_path=blob_path,
        ):
            return None
        selected_refs = self._snapshot_state_class_segment_selected_refs_from_payload(
            payload=payload,
            selected_ids=selected_ids,
            field_name="class_segments",
            count_field_name="class_segment_count",
        )
        if selected_refs is None or set(selected_refs) != selected_ids:
            return None
        return self._read_snapshot_state_indexed_raw_class_segment_records(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            selected_refs=selected_refs,
            segment_refs_by_key=expected_segment_refs_by_key,
        )

    async def get_snapshot_state_indexed_raw_class_segments_by_witness_ref(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        class_instance_ids: Iterable[UUID],
        expected_witness_ref: CommitStateWitnessRef,
        expected_object_instance_graph_id: UUID | None = None,
        expected_graph_hash: str | None = None,
    ) -> ObjectInstanceGraphSnapshotStateRawClassSegmentIndexSelection | None:
        selected_ids = {
            str(class_instance_id) for class_instance_id in class_instance_ids
        }
        if not selected_ids or not validate_commit_state_witness_ref(
            expected_witness_ref
        ):
            return None
        selected_segment_keys = {f"class:{raw_id}" for raw_id in selected_ids}
        expected_segment_refs_by_key = {
            segment.key: segment
            for segment in expected_witness_ref.segments
            if segment.key in selected_segment_keys
        }
        if set(expected_segment_refs_by_key) != selected_segment_keys:
            return None
        manifest_path = self._snapshot_state_class_segment_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        trace_metadata = _snapshot_trace_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        with commit_perf_span(
            phase="oig_snapshot_store.state_class_segment_ref_index.read_manifest",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
                manifest_path,
                log_prefix=(
                    "Failed reading snapshot state class segment ref index "
                    f"{commit_id}"
                ),
            )
        if payload is None:
            return None
        with commit_perf_span(
            phase="oig_snapshot_store.state_class_segment_ref_index.validate_manifest",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            metadata = self._snapshot_state_class_segment_index_metadata_from_payload(
                payload=payload,
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                expected_object_instance_graph_id=expected_object_instance_graph_id,
                expected_graph_hash=expected_graph_hash,
            )
            if metadata is None:
                return None
            if metadata.witness_ref != expected_witness_ref:
                return None

        selected_segments: dict[
            UUID,
            ObjectInstanceGraphSnapshotStateRawClassSegment,
        ] = {}
        with commit_perf_span(
            phase="oig_snapshot_store.state_class_segment_ref_index.read_selected",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata={**trace_metadata, "selected_count": len(selected_ids)},
        ):
            resolved_segments = await self._get_snapshot_state_indexed_raw_class_segments_from_ref_payload(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                payload=payload,
                selected_ids=selected_ids,
                expected_witness_ref=expected_witness_ref,
                expected_segment_refs_by_key=expected_segment_refs_by_key,
                expected_object_instance_graph_id=(expected_object_instance_graph_id),
                expected_graph_hash=expected_graph_hash,
                require_witness_ref=True,
                visited_commit_ids=set(),
                depth=0,
                prevalidated_metadata=metadata,
            )
            if resolved_segments is None:
                return None
            selected_segments.update(resolved_segments)
        if set(selected_segments) != {UUID(raw_id) for raw_id in selected_ids}:
            return None
        return ObjectInstanceGraphSnapshotStateRawClassSegmentIndexSelection(
            witness_metadata=metadata,
            class_segments_by_id=selected_segments,
        )

    async def get_snapshot_state_indexed_raw_class_segments_by_witness_cursor(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        class_instance_ids: Iterable[UUID],
        expected_witness_cursor_summary: CommitStateWitnessCursorSummary,
        expected_object_instance_graph_id: UUID | None = None,
        expected_graph_hash: str | None = None,
    ) -> ObjectInstanceGraphSnapshotStateRawClassSegmentCursorSelection | None:
        selected_ids = {
            str(class_instance_id) for class_instance_id in class_instance_ids
        }
        if not selected_ids:
            return None
        trace_metadata = _snapshot_trace_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        fast_read = self._get_snapshot_state_indexed_raw_class_segments_from_cursor_chunk_sidecars(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            selected_ids=selected_ids,
            expected_cursor_summary=expected_witness_cursor_summary,
            expected_object_instance_graph_id=(expected_object_instance_graph_id),
            expected_graph_hash=expected_graph_hash,
        )
        if fast_read is not None and set(fast_read.class_segments_by_id) == {
            UUID(raw_id) for raw_id in selected_ids
        }:
            return ObjectInstanceGraphSnapshotStateRawClassSegmentCursorSelection(
                payload=fast_read.payload,
                object_instance_graph_id=fast_read.object_instance_graph_id,
                graph_hash=fast_read.graph_hash,
                witness_cursor_summary=fast_read.cursor_summary,
                cursor_chunks_by_index=fast_read.cursor_chunks_by_index,
                class_segments_by_id=fast_read.class_segments_by_id,
            )
        manifest_path = self._snapshot_state_class_segment_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        with commit_perf_span(
            phase="oig_snapshot_store.state_class_segment_cursor.read_manifest",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
                manifest_path,
                log_prefix=(
                    "Failed reading snapshot state class segment cursor index "
                    f"{commit_id}"
                ),
            )
        if payload is None:
            return None
        with commit_perf_span(
            phase="oig_snapshot_store.state_class_segment_cursor.read_selected",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata={**trace_metadata, "selected_count": len(selected_ids)},
        ):
            read = await self._get_snapshot_state_indexed_raw_class_segments_from_cursor_payload(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                payload=payload,
                selected_ids=selected_ids,
                expected_cursor_summary=expected_witness_cursor_summary,
                expected_object_instance_graph_id=(expected_object_instance_graph_id),
                expected_graph_hash=expected_graph_hash,
                visited_commit_ids=set(),
                depth=0,
            )
        if read is None:
            return None
        if set(read.class_segments_by_id) != {UUID(raw_id) for raw_id in selected_ids}:
            return None
        return ObjectInstanceGraphSnapshotStateRawClassSegmentCursorSelection(
            payload=read.payload,
            object_instance_graph_id=read.object_instance_graph_id,
            graph_hash=read.graph_hash,
            witness_cursor_summary=read.cursor_summary,
            cursor_chunks_by_index=read.cursor_chunks_by_index,
            class_segments_by_id=read.class_segments_by_id,
        )

    async def _get_snapshot_state_rows_read_by_file_witness(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        expected_file_size: int,
        expected_file_mtime_ns: int,
        expected_file_ctime_ns: int,
        expected_payload_sha256: str,
        expected_state_hash: str,
        expected_object_instance_graph_id: UUID | None = None,
        expected_graph_hash: str | None = None,
        include_state_row_maps: bool = False,
    ) -> _SnapshotStateRowsRead | None:
        if (
            expected_file_size < 0
            or expected_file_mtime_ns < 0
            or expected_file_ctime_ns < 0
            or not expected_payload_sha256
            or not expected_state_hash
        ):
            return None
        path = self._snapshot_state_rows_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        trace_metadata = _snapshot_trace_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        with commit_perf_span(
            phase="oig_snapshot_store.state_rows.witness_stat",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            try:
                file_size, file_mtime_ns, file_ctime_ns = _file_stat_payload(path)
            except Exception:
                return None
        if (
            file_size != expected_file_size
            or file_mtime_ns != expected_file_mtime_ns
            or file_ctime_ns != expected_file_ctime_ns
        ):
            return None
        with commit_perf_span(
            phase="oig_snapshot_store.state_rows.witness_cached_read",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            cached_read = _SESSION_SNAPSHOT_STATE_ROWS_READ_CACHE.try_read(
                path,
                file_size=file_size,
                file_mtime_ns=file_mtime_ns,
                file_ctime_ns=file_ctime_ns,
            )
        payload: JsonObject | None
        payload = cached_read.payload if cached_read is not None else None
        with commit_perf_span(
            phase="oig_snapshot_store.state_rows.witness_read_payload",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            if payload is None:
                payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
                    path,
                    log_prefix=(
                        f"Failed reading witnessed snapshot state rows {commit_id}"
                    ),
                )
        if payload is None:
            return None
        with commit_perf_span(
            phase="oig_snapshot_store.state_rows.witness_validate_metadata",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            if (
                payload.get("v")
                != OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_ROWS_INDEX_VERSION
            ):
                return None
            if (
                payload.get("schema")
                != OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_ROWS_SCHEMA
            ):
                return None
            if payload.get("branch_id") != str(branch_id):
                return None
            if payload.get("projection_hash") != projection_hash:
                return None
            if payload.get("commit_id") != str(commit_id):
                return None
            object_instance_graph_id = _json_optional_uuid(
                payload,
                "object_instance_graph_id",
            )
            graph_hash = _json_optional_string(payload, "graph_hash")
            if object_instance_graph_id is None or not graph_hash:
                return None
            if (
                expected_object_instance_graph_id is not None
                and object_instance_graph_id != expected_object_instance_graph_id
            ):
                return None
            if expected_graph_hash is not None and graph_hash != expected_graph_hash:
                return None
            if payload.get("payload_hash_algorithm") != (
                OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_ROWS_PAYLOAD_HASH_ALGORITHM
            ):
                return None
            if payload.get("payload_sha256") != expected_payload_sha256:
                return None
            if payload.get("state_hash") != expected_state_hash:
                return None
        if cached_read is not None:
            if include_state_row_maps and cached_read.state_row_maps is None:
                with commit_perf_span(
                    phase=("oig_snapshot_store.state_rows." "witness_cached_row_maps"),
                    category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                    metadata=trace_metadata,
                ):
                    cached_read = (
                        _SESSION_SNAPSHOT_STATE_ROWS_READ_CACHE.with_state_row_maps(
                            path,
                            file_size=file_size,
                            file_mtime_ns=file_mtime_ns,
                            file_ctime_ns=file_ctime_ns,
                            read=cached_read,
                        )
                    )
                if cached_read is None:
                    return None
            return cached_read
        with commit_perf_span(
            phase="oig_snapshot_store.state_rows.witness_parse_state_rows",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            read = _commit_state_rows_read_from_snapshot_payload(
                payload,
                include_state_row_maps=include_state_row_maps,
            )
        if read is None:
            return None
        _SESSION_SNAPSHOT_STATE_ROWS_READ_CACHE.store_read(
            path,
            file_size=file_size,
            file_mtime_ns=file_mtime_ns,
            file_ctime_ns=file_ctime_ns,
            read=read,
        )
        return read

    async def get_snapshot_state_selection(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        class_instance_ids: Iterable[UUID],
        expected_object_instance_graph_id: UUID | None = None,
        expected_graph_hash: str | None = None,
        include_state_row_maps: bool = False,
    ) -> ObjectInstanceGraphSnapshotStateSelection | None:
        payload = await self.get_snapshot_state_rows(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            expected_object_instance_graph_id=expected_object_instance_graph_id,
            expected_graph_hash=expected_graph_hash,
        )
        if payload is None:
            return None
        state_rows = _commit_state_rows_from_snapshot_payload(payload)
        if state_rows is None:
            return None
        selected_ids = {
            str(class_instance_id) for class_instance_id in class_instance_ids
        }
        class_instances = payload.get("class_instances")
        if not isinstance(class_instances, list):
            return None
        class_instances_by_id: dict[UUID, ClassInstance] = {}
        if selected_ids:
            try:
                for item in class_instances:
                    if not isinstance(item, dict):
                        continue
                    raw_id = item.get("id")
                    if not isinstance(raw_id, str) or raw_id not in selected_ids:
                        continue
                    class_instance = ClassInstance.model_validate(item)
                    if class_instance.id is None:
                        return None
                    class_instances_by_id[class_instance.id] = class_instance
            except Exception as exc:
                logger.warning(
                    "Failed hydrating selected snapshot state rows for %s: %s",
                    commit_id,
                    exc,
                )
                return None
        state_row_maps: CommitStateRowMaps | None = None
        if include_state_row_maps:
            with commit_perf_span(
                phase="oig_snapshot_store.state_rows.selection_row_maps",
                category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                metadata=_snapshot_trace_metadata(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    commit_id=commit_id,
                ),
            ):
                state_row_maps = CommitStateIndex(rows=state_rows).row_maps()
        return ObjectInstanceGraphSnapshotStateSelection(
            payload=payload,
            state_rows=state_rows,
            class_instances_by_id=class_instances_by_id,
            state_row_maps=state_row_maps,
        )

    async def get_snapshot_state_selection_by_file_witness(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        class_instance_ids: Iterable[UUID],
        expected_file_size: int,
        expected_file_mtime_ns: int,
        expected_file_ctime_ns: int,
        expected_payload_sha256: str,
        expected_state_hash: str,
        expected_object_instance_graph_id: UUID | None = None,
        expected_graph_hash: str | None = None,
        include_state_row_maps: bool = False,
    ) -> ObjectInstanceGraphSnapshotStateSelection | None:
        read = await self._get_snapshot_state_rows_read_by_file_witness(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            expected_file_size=expected_file_size,
            expected_file_mtime_ns=expected_file_mtime_ns,
            expected_file_ctime_ns=expected_file_ctime_ns,
            expected_payload_sha256=expected_payload_sha256,
            expected_state_hash=expected_state_hash,
            expected_object_instance_graph_id=expected_object_instance_graph_id,
            expected_graph_hash=expected_graph_hash,
            include_state_row_maps=include_state_row_maps,
        )
        if read is None:
            return None
        payload = read.payload
        state_rows = read.state_rows
        selected_ids = {
            str(class_instance_id) for class_instance_id in class_instance_ids
        }
        class_instances = payload.get("class_instances")
        if not isinstance(class_instances, list):
            return None
        class_instances_by_id: dict[UUID, ClassInstance] = {}
        if selected_ids:
            try:
                for item in class_instances:
                    if not isinstance(item, dict):
                        continue
                    raw_id = item.get("id")
                    if not isinstance(raw_id, str) or raw_id not in selected_ids:
                        continue
                    class_instance = ClassInstance.model_validate(item)
                    if class_instance.id is None:
                        return None
                    class_instances_by_id[class_instance.id] = class_instance
            except Exception as exc:
                logger.warning(
                    "Failed hydrating witnessed snapshot state rows for %s: %s",
                    commit_id,
                    exc,
                )
                return None
        return ObjectInstanceGraphSnapshotStateSelection(
            payload=payload,
            state_rows=state_rows,
            class_instances_by_id=class_instances_by_id,
            state_row_maps=read.state_row_maps,
        )

    async def get_snapshot_state_graph(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        expected_object_instance_graph_id: UUID | None = None,
        expected_graph_hash: str | None = None,
    ) -> tuple[ObjectInstanceGraph, JsonObject] | None:
        trace_metadata = _snapshot_trace_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        with commit_perf_span(
            phase="oig_snapshot_store.state_graph.read_rows",
            category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            payload = await self.get_snapshot_state_rows(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                expected_object_instance_graph_id=expected_object_instance_graph_id,
                expected_graph_hash=expected_graph_hash,
            )
        if payload is None:
            return None
        try:
            with commit_perf_span(
                phase="oig_snapshot_store.state_graph.hydrate_graph",
                category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                metadata=trace_metadata,
            ):
                with commit_perf_span(
                    phase="oig_snapshot_store.state_graph.graph_metadata",
                    category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                    metadata=trace_metadata,
                ):
                    graph_meta = _json_mapping(payload, "graph")
                with commit_perf_span(
                    phase="oig_snapshot_store.state_graph.payload_shape",
                    category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                    metadata=trace_metadata,
                ):
                    class_instances = payload.get("class_instances")
                    relationships = payload.get("class_instance_relationships")
                    if not isinstance(class_instances, list) or not isinstance(
                        relationships,
                        list,
                    ):
                        return None
                with commit_perf_span(
                    phase="oig_snapshot_store.state_graph.hydrate_class_instances",
                    category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                    metadata=trace_metadata,
                ):
                    class_instance_models = tuple(
                        _trusted_class_instance_from_snapshot_state_payload(item)
                        for item in class_instances
                    )
                with commit_perf_span(
                    phase="oig_snapshot_store.state_graph.hydrate_relationships",
                    category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                    metadata=trace_metadata,
                ):
                    relationship_models = tuple(
                        _trusted_relationship_from_snapshot_state_payload(item)
                        for item in relationships
                    )
                with commit_perf_span(
                    phase="oig_snapshot_store.state_graph.resolve_root",
                    category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                    metadata=trace_metadata,
                ):
                    root_class_instance_id = graph_meta.get("root_class_instance_id")
                    root_class_instance = None
                    if isinstance(root_class_instance_id, str):
                        root_class_instance_uuid = UUID(root_class_instance_id)
                        root_class_instance = next(
                            (
                                class_instance
                                for class_instance in class_instance_models
                                if class_instance.id == root_class_instance_uuid
                            ),
                            None,
                        )
                with commit_perf_span(
                    phase="oig_snapshot_store.state_graph.construct_graph",
                    category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                    metadata=trace_metadata,
                ):
                    snapshot = ObjectInstanceGraph.model_construct(
                        id=_json_required_uuid(graph_meta, "id"),
                        key=_json_required_string(graph_meta, "key"),
                        name=_json_required_string(graph_meta, "name"),
                        description=_json_optional_string(graph_meta, "description"),
                        hash=_json_optional_string(graph_meta, "hash"),
                        object_projection_graph_id=_json_required_uuid(
                            graph_meta,
                            "object_projection_graph_id",
                        ),
                        root_class_instance_id=_json_optional_uuid(
                            graph_meta,
                            "root_class_instance_id",
                        ),
                        root_class_instance=root_class_instance,
                        class_instances=list(class_instance_models),
                        class_instance_relationships=list(relationship_models),
                    )
            index_path = (
                self._lane_dir(branch_id, projection_hash)
                / "indexes"
                / f"{commit_id}.json"
            )
            with commit_perf_span(
                phase="oig_snapshot_store.state_graph.read_snapshot_index",
                category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                metadata=trace_metadata,
            ):
                fallback_indexes: JsonObject = {
                    "v": 1,
                    "source": "snapshot_state_rows",
                }
                indexes = (
                    dict(
                        _SESSION_JSON_FILE_CACHE.read_json_object(
                            index_path,
                            error_message=f"Invalid snapshot index JSON object: {index_path}",
                        )
                    )
                    if index_path.exists()
                    else fallback_indexes
                )
            return snapshot, indexes
        except Exception as exc:
            logger.warning(
                "Failed hydrating snapshot state rows for %s: %s",
                commit_id,
                exc,
            )
            return None

    async def get(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> tuple[ObjectInstanceGraph, JsonObject] | None:
        lane_dir = self._lane_dir(branch_id, projection_hash)
        snapshot_path = lane_dir / "snapshots" / f"{commit_id}.json"
        if not snapshot_path.exists():
            return None

        try:
            trace_metadata = _snapshot_trace_metadata(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
            )
            with commit_perf_span(
                phase="oig_snapshot_store.get.read_snapshot_json",
                category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                metadata=trace_metadata,
            ):
                snapshot_payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
                    snapshot_path,
                    log_prefix=f"Failed reading snapshot for {commit_id}",
                )
            if snapshot_payload is None:
                return None
            with commit_perf_span(
                phase="oig_snapshot_store.get.validate_snapshot_model",
                category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                metadata=trace_metadata,
            ):
                snapshot = ObjectInstanceGraph.model_validate(snapshot_payload)
            index_path = lane_dir / "indexes" / f"{commit_id}.json"
            with commit_perf_span(
                phase="oig_snapshot_store.get.read_snapshot_index",
                category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                metadata=trace_metadata,
            ):
                indexes = (
                    dict(
                        _SESSION_JSON_FILE_CACHE.read_json_object(
                            index_path,
                            error_message=f"Invalid snapshot index JSON object: {index_path}",
                        )
                    )
                    if index_path.exists()
                    else {}
                )
            return snapshot, indexes
        except Exception as exc:
            logger.warning("Failed reading snapshot for %s: %s", commit_id, exc)
            return None

    async def nearest_at_or_before(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID | None,
    ) -> tuple[UUID, ObjectInstanceGraph, JsonObject] | None:
        lane_dir = self._lane_dir(branch_id, projection_hash)
        if not lane_dir.exists():
            return None

        target_commit_id = commit_id
        commits = FSCommitStore(root_dir=self._aware_root)
        if target_commit_id is None:
            with commit_perf_span(
                phase="oig_snapshot_store.nearest.head_read",
                category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                metadata=_snapshot_trace_metadata(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    commit_id=None,
                ),
            ):
                head = await commits.head(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                )
            if head is None:
                return None
            target_commit_id = _json_optional_uuid(head, "commit_id")
            if target_commit_id is None:
                return None

        current_commit_id: UUID | None = target_commit_id
        visited_commit_ids: set[UUID] = set()
        while (
            current_commit_id is not None
            and current_commit_id not in visited_commit_ids
        ):
            visited_commit_ids.add(current_commit_id)
            trace_metadata = _snapshot_trace_metadata(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=current_commit_id,
                walk_depth=len(visited_commit_ids) - 1,
            )

            with commit_perf_span(
                phase="oig_snapshot_store.nearest.try_state_graph",
                category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                metadata=trace_metadata,
            ):
                state_snapshot = await self.get_snapshot_state_graph(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    commit_id=current_commit_id,
                )
            if state_snapshot is not None:
                graph_snapshot, indexes = state_snapshot
                return current_commit_id, graph_snapshot, indexes

            with commit_perf_span(
                phase="oig_snapshot_store.nearest.try_full_snapshot",
                category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                metadata=trace_metadata,
            ):
                snapshot = await self.get(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    commit_id=current_commit_id,
                )
            if snapshot is not None:
                graph_snapshot, indexes = snapshot
                return current_commit_id, graph_snapshot, indexes

            with commit_perf_span(
                phase="oig_snapshot_store.nearest.parent_envelope_read",
                category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                metadata=trace_metadata,
            ):
                envelope = await commits.get_commit_envelope(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    commit_id=current_commit_id,
                )
            if envelope is not None:
                parent_ids = envelope.parent_commit_ids
                if len(parent_ids) > 1:
                    raise ValueError(
                        f"Non-linear commit {envelope.commit_id} has {len(parent_ids)} parents"
                    )
                current_commit_id = parent_ids[0] if parent_ids else None
                continue

            with commit_perf_span(
                phase="oig_snapshot_store.nearest.parent_commit_read",
                category=_OIG_SNAPSHOT_STORE_TRACE_CATEGORY,
                metadata=trace_metadata,
            ):
                commit = await commits.get_commit(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    commit_id=current_commit_id,
                )
            if commit is None:
                return None

            parents = commit.commit.commit_parents
            if len(parents) > 1:
                raise ValueError(
                    f"Non-linear commit {commit.commit.id} has {len(parents)} parents"
                )
            current_commit_id = parents[0].parent_commit_id if parents else None

        return None
