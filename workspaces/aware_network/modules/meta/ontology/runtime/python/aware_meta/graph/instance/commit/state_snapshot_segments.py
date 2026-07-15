from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import hashlib
import json
from typing import Literal, cast
from uuid import UUID

from aware_meta.graph.instance.commit.contract import JsonObject
from aware_meta.graph.instance.commit.state_index import CommitStateRow
from aware_meta.graph.instance.commit.state_witness import (
    CommitStateWitnessCursorChunk,
    CommitStateSegmentRef,
    CommitStateWitnessCursorChunkSummary,
    CommitStateWitnessCursorSummary,
    CommitStateWitnessRef,
    compute_commit_state_witness_cursor_chunk_hash,
    compute_commit_state_segment_digest,
    validate_commit_state_witness_cursor_summary,
    validate_commit_state_witness_ref,
)
from aware_meta_ontology.class_.class_instance import ClassInstance


OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENTS_INDEX_VERSION = 1
OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENTS_SCHEMA = (
    "aware.oig.snapshot_state_class_segments.v1"
)
OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_INDEX_VERSION = 1
OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_INDEX_SCHEMA = (
    "aware.oig.snapshot_state_class_segment_index.v1"
)
OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_REF_INDEX_VERSION = 3
OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_REF_INDEX_SCHEMA = (
    "aware.oig.snapshot_state_class_segment_index.v3"
)
OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_OVERLAY_INDEX_VERSION = 4
OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_OVERLAY_INDEX_SCHEMA = (
    "aware.oig.snapshot_state_class_segment_index.v4"
)
OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_RECORD_VERSION = 1
OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_RECORD_SCHEMA = (
    "aware.oig.snapshot_state_class_segment_record.v1"
)


@dataclass(frozen=True, slots=True)
class ObjectInstanceGraphSnapshotStateWitnessMetadata:
    payload: JsonObject
    object_instance_graph_id: UUID
    graph_hash: str
    state_hash: str
    witness_hash: str
    row_count: int
    node_count: int
    attribute_count: int
    edge_count: int
    state_rows_payload_sha256: str
    state_rows_file_size: int
    state_rows_file_mtime_ns: int
    state_rows_file_ctime_ns: int
    witness_ref: CommitStateWitnessRef


@dataclass(frozen=True, slots=True)
class ObjectInstanceGraphSnapshotStateClassSegment:
    class_instance_id: UUID
    class_config_id: UUID
    source_object_id: UUID | None
    rows: tuple[CommitStateRow, ...]
    snapshot_payload: JsonObject


@dataclass(frozen=True, slots=True)
class ObjectInstanceGraphSnapshotStateRawClassSegment:
    class_instance_id: UUID
    class_config_id: UUID
    source_object_id: UUID | None
    rows_text: str
    row_count: int
    row_hash: str
    snapshot_payload: JsonObject
    segment_ref: CommitStateSegmentRef


@dataclass(frozen=True, slots=True)
class ObjectInstanceGraphSnapshotStateClassSegmentSelection:
    witness_metadata: ObjectInstanceGraphSnapshotStateWitnessMetadata
    class_segments_by_id: Mapping[UUID, ObjectInstanceGraphSnapshotStateClassSegment]
    class_instances_by_id: Mapping[UUID, ClassInstance]


@dataclass(frozen=True, slots=True)
class ObjectInstanceGraphSnapshotStateRawClassSegmentSelection:
    witness_metadata: ObjectInstanceGraphSnapshotStateWitnessMetadata
    class_segments_by_id: Mapping[
        UUID,
        ObjectInstanceGraphSnapshotStateRawClassSegment,
    ]


@dataclass(frozen=True, slots=True)
class ObjectInstanceGraphSnapshotStateSegmentIndexMetadata:
    payload: JsonObject
    object_instance_graph_id: UUID
    graph_hash: str
    state_hash: str | None
    witness_hash: str
    row_count: int
    witness_ref: CommitStateWitnessRef
    witness_cursor_summary: CommitStateWitnessCursorSummary | None = None


@dataclass(frozen=True, slots=True)
class ObjectInstanceGraphSnapshotStateRawClassSegmentIndexSelection:
    witness_metadata: ObjectInstanceGraphSnapshotStateSegmentIndexMetadata
    class_segments_by_id: Mapping[
        UUID,
        ObjectInstanceGraphSnapshotStateRawClassSegment,
    ]


@dataclass(frozen=True, slots=True)
class ObjectInstanceGraphSnapshotStateRawClassSegmentCursorSelection:
    payload: JsonObject
    object_instance_graph_id: UUID
    graph_hash: str
    witness_cursor_summary: CommitStateWitnessCursorSummary
    cursor_chunks_by_index: Mapping[int, CommitStateWitnessCursorChunk]
    class_segments_by_id: Mapping[
        UUID,
        ObjectInstanceGraphSnapshotStateRawClassSegment,
    ]


def commit_state_segment_ref_payload(segment: CommitStateSegmentRef) -> JsonObject:
    return {
        "kind": segment.kind,
        "key": segment.key,
        "row_count": segment.row_count,
        "row_hash": segment.row_hash,
        "digest": segment.digest,
    }


def commit_state_segment_ref_from_payload(
    payload: object,
) -> CommitStateSegmentRef:
    segment_payload = _coerce_json_object(
        payload,
        error_message="Commit state segment ref must be a JSON object",
    )
    kind = _json_required_string(segment_payload, "kind")
    if kind not in {"CLASS", "ORPHAN_ATTR", "EDGE"}:
        raise ValueError(f"Unsupported commit state segment kind: {kind!r}")
    return CommitStateSegmentRef(
        kind=cast(Literal["CLASS", "ORPHAN_ATTR", "EDGE"], kind),
        key=_json_required_string(segment_payload, "key"),
        row_count=_json_required_int(segment_payload, "row_count"),
        row_hash=_json_required_string(segment_payload, "row_hash"),
        digest=_json_required_string(segment_payload, "digest"),
    )


def commit_state_witness_ref_payload(ref: CommitStateWitnessRef) -> JsonObject:
    payload: JsonObject = {
        "commit_state_witness_schema": ref.schema,
        "witness_hash": ref.witness_hash,
        "row_count": ref.row_count,
        "segment_count": len(ref.segments),
        "segments": [
            commit_state_segment_ref_payload(segment) for segment in ref.segments
        ],
    }
    if ref.state_hash is not None:
        payload["state_hash"] = ref.state_hash
    return payload


def commit_state_witness_ref_summary_payload(
    ref: CommitStateWitnessRef,
) -> JsonObject:
    payload: JsonObject = {
        "commit_state_witness_schema": ref.schema,
        "witness_hash": ref.witness_hash,
        "row_count": ref.row_count,
        "segment_count": len(ref.segments),
    }
    if ref.state_hash is not None:
        payload["state_hash"] = ref.state_hash
    return payload


def commit_state_witness_cursor_summary_payload(
    summary: CommitStateWitnessCursorSummary,
) -> JsonObject:
    payload: JsonObject = {
        "commit_state_witness_cursor_schema": summary.schema,
        "cursor_hash": summary.cursor_hash,
        "row_count": summary.row_count,
        "segment_count": summary.segment_count,
        "chunk_size": summary.chunk_size,
        "chunk_count": len(summary.chunks),
        "chunks": [
            {
                "index": chunk.index,
                "first_segment_key": chunk.first_segment_key,
                "last_segment_key": chunk.last_segment_key,
                "segment_count": chunk.segment_count,
                "row_count": chunk.row_count,
                "digest": chunk.digest,
            }
            for chunk in summary.chunks
        ],
    }
    if summary.state_hash is not None:
        payload["state_hash"] = summary.state_hash
    if summary.legacy_witness_hash is not None:
        payload["legacy_witness_hash"] = summary.legacy_witness_hash
    return payload


def commit_state_witness_cursor_chunk_payload(
    chunk: CommitStateWitnessCursorChunk,
) -> JsonObject:
    return {
        "commit_state_witness_cursor_chunk_schema": (
            "aware.oig.commit_state_witness_cursor_chunk.v1"
        ),
        "index": chunk.index,
        "segment_keys": list(chunk.segment_keys),
        "row_count": chunk.row_count,
        "segment_count": len(chunk.segments),
        "segments": [
            commit_state_segment_ref_payload(segment) for segment in chunk.segments
        ],
        "digest": chunk.digest,
    }


def commit_state_witness_cursor_chunk_from_payload(
    payload: object,
) -> CommitStateWitnessCursorChunk | None:
    try:
        chunk_payload = _coerce_json_object(
            payload,
            error_message="Commit state witness cursor chunk must be a JSON object",
        )
        if (
            _json_required_string(
                chunk_payload,
                "commit_state_witness_cursor_chunk_schema",
            )
            != "aware.oig.commit_state_witness_cursor_chunk.v1"
        ):
            return None
        segment_keys = tuple(
            _json_required_string({"value": raw_key}, "value")
            for raw_key in _json_required_list(chunk_payload, "segment_keys")
        )
        segments = tuple(
            commit_state_segment_ref_from_payload(raw_segment)
            for raw_segment in _json_required_list(chunk_payload, "segments")
        )
        chunk = CommitStateWitnessCursorChunk(
            index=_json_required_int(chunk_payload, "index"),
            segment_keys=segment_keys,
            row_count=_json_required_int(chunk_payload, "row_count"),
            segments=segments,
            digest=_json_required_string(chunk_payload, "digest"),
        )
    except Exception:
        return None
    if _json_optional_int(chunk_payload, "segment_count") != len(chunk.segments):
        return None
    if len(chunk.segment_keys) != len(chunk.segments):
        return None
    if tuple(segment.key for segment in chunk.segments) != chunk.segment_keys:
        return None
    if chunk.row_count != sum(segment.row_count for segment in chunk.segments):
        return None
    if chunk.digest != compute_commit_state_witness_cursor_chunk_hash(chunk.segments):
        return None
    return chunk


def commit_state_witness_cursor_summary_from_payload(
    payload: object,
) -> CommitStateWitnessCursorSummary | None:
    try:
        cursor_payload = _coerce_json_object(
            payload,
            error_message="Commit state witness cursor summary must be a JSON object",
        )
        chunks = tuple(
            CommitStateWitnessCursorChunkSummary(
                index=_json_required_int(chunk_payload, "index"),
                first_segment_key=_json_required_string(
                    chunk_payload,
                    "first_segment_key",
                ),
                last_segment_key=_json_required_string(
                    chunk_payload,
                    "last_segment_key",
                ),
                segment_count=_json_required_int(chunk_payload, "segment_count"),
                row_count=_json_required_int(chunk_payload, "row_count"),
                digest=_json_required_string(chunk_payload, "digest"),
            )
            for chunk_payload in (
                _coerce_json_object(
                    raw_chunk,
                    error_message=(
                        "Commit state witness cursor chunk must be a JSON object"
                    ),
                )
                for raw_chunk in _json_required_list(cursor_payload, "chunks")
            )
        )
        summary = CommitStateWitnessCursorSummary(
            schema=_json_required_string(
                cursor_payload,
                "commit_state_witness_cursor_schema",
            ),
            state_hash=_json_optional_string(cursor_payload, "state_hash"),
            legacy_witness_hash=_json_optional_string(
                cursor_payload,
                "legacy_witness_hash",
            ),
            cursor_hash=_json_required_string(cursor_payload, "cursor_hash"),
            row_count=_json_required_int(cursor_payload, "row_count"),
            segment_count=_json_required_int(cursor_payload, "segment_count"),
            chunk_size=_json_required_int(cursor_payload, "chunk_size"),
            chunks=chunks,
        )
    except Exception:
        return None
    if _json_optional_int(cursor_payload, "chunk_count") != len(summary.chunks):
        return None
    return summary if validate_commit_state_witness_cursor_summary(summary) else None


def commit_state_witness_ref_from_index_payload(
    payload: JsonObject,
) -> CommitStateWitnessRef | None:
    try:
        segments = tuple(
            commit_state_segment_ref_from_payload(item)
            for item in _json_required_list(payload, "segments")
        )
        ref = CommitStateWitnessRef(
            schema=_json_required_string(payload, "commit_state_witness_schema"),
            state_hash=_json_optional_string(payload, "state_hash"),
            witness_hash=_json_required_string(payload, "witness_hash"),
            row_count=_json_required_int(payload, "row_count"),
            segments=segments,
        )
    except Exception:
        return None
    if _json_optional_int(payload, "segment_count") != len(ref.segments):
        return None
    return ref if validate_commit_state_witness_ref(ref) else None


def snapshot_state_segment_index_metadata_from_payload(
    payload: JsonObject,
) -> ObjectInstanceGraphSnapshotStateSegmentIndexMetadata | None:
    witness_ref = commit_state_witness_ref_from_index_payload(payload)
    if witness_ref is None:
        return None
    witness_cursor_summary = None
    raw_witness_cursor_summary = payload.get("state_witness_cursor")
    if raw_witness_cursor_summary is not None:
        witness_cursor_summary = commit_state_witness_cursor_summary_from_payload(
            raw_witness_cursor_summary,
        )
        if witness_cursor_summary is None:
            return None
    try:
        return ObjectInstanceGraphSnapshotStateSegmentIndexMetadata(
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


def commit_state_rows_snapshot_state_text(
    rows: Iterable[CommitStateRow],
) -> str:
    lines: list[str] = []
    for row in rows:
        if row.kind not in {"NODE", "ATTR", "EDGE"}:
            raise ValueError(f"Unsupported CommitStateRow kind: {row.kind!r}")
        for field_name, value in (
            ("key", row.key),
            ("value", row.value),
        ):
            if not value or any(separator in value for separator in ("\t", "\n", "\r")):
                raise ValueError(
                    "CommitStateRow text sidecar field contains an unsupported "
                    f"separator: field={field_name}"
                )
        lines.append(f"{row.kind}\t{row.key}\t{row.value}")
    return "\n".join(lines) + ("\n" if lines else "")


def commit_state_rows_text_hash_and_count(rows_text: str) -> tuple[str, int] | None:
    if rows_text and not rows_text.endswith("\n"):
        return None
    digest = hashlib.sha256()
    count = 0
    for line in rows_text.splitlines():
        raw_kind, separator, remainder = line.partition("\t")
        if not separator:
            return None
        raw_key, separator, raw_value = remainder.partition("\t")
        if not separator:
            return None
        if raw_kind not in {"NODE", "ATTR", "EDGE"}:
            return None
        if not raw_key or not raw_value:
            return None
        if any(separator in raw_key for separator in ("\t", "\n", "\r")):
            return None
        if any(separator in raw_value for separator in ("\t", "\n", "\r")):
            return None
        digest.update(raw_kind.encode("utf-8"))
        digest.update(b"|")
        digest.update(raw_key.encode("utf-8"))
        digest.update(b"|")
        digest.update(raw_value.encode("utf-8"))
        digest.update(b"\n")
        count += 1
    return digest.hexdigest(), count


def raw_class_segment_from_payload(
    *,
    raw_class_instance_id: str,
    item: Mapping[str, object],
    segment_refs_by_key: Mapping[str, CommitStateSegmentRef],
) -> ObjectInstanceGraphSnapshotStateRawClassSegment | None:
    if (
        item.get("v")
        != OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_RECORD_VERSION
    ):
        return None
    if (
        item.get("schema")
        != OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_RECORD_SCHEMA
    ):
        return None
    if item.get("class_instance_id") != raw_class_instance_id:
        return None
    rows_text = item.get("rows_text")
    if not isinstance(rows_text, str):
        return None
    rows_text_hash = commit_state_rows_text_hash_and_count(rows_text)
    if rows_text_hash is None:
        return None
    row_hash, row_count = rows_text_hash
    segment_payload = item.get("segment")
    try:
        segment_ref = commit_state_segment_ref_from_payload(segment_payload)
    except Exception:
        return None
    expected_segment_ref = segment_refs_by_key.get(f"class:{raw_class_instance_id}")
    if segment_ref != expected_segment_ref:
        return None
    if segment_ref.row_hash != row_hash:
        return None
    if segment_ref.row_count != row_count:
        return None
    snapshot_payload = item.get("snapshot_payload")
    if not isinstance(snapshot_payload, dict):
        return None
    raw_class_config_id = item.get("class_config_id")
    if not isinstance(raw_class_config_id, str):
        return None
    raw_source_object_id = item.get("source_object_id")
    try:
        class_instance_id = UUID(raw_class_instance_id)
        class_config_id = UUID(raw_class_config_id)
        source_object_id = (
            UUID(raw_source_object_id)
            if isinstance(raw_source_object_id, str)
            else None
        )
        typed_snapshot_payload = _coerce_json_object_view(
            snapshot_payload,
            error_message="Selected raw class segment snapshot payload must be a "
            "JSON object",
        )
    except Exception:
        return None
    return ObjectInstanceGraphSnapshotStateRawClassSegment(
        class_instance_id=class_instance_id,
        class_config_id=class_config_id,
        source_object_id=source_object_id,
        rows_text=rows_text,
        row_count=row_count,
        row_hash=row_hash,
        snapshot_payload=typed_snapshot_payload,
        segment_ref=segment_ref,
    )


def raw_class_segment_record_payload(
    segment: ObjectInstanceGraphSnapshotStateRawClassSegment,
) -> JsonObject:
    if segment.segment_ref.kind != "CLASS":
        raise ValueError("Class segment record requires a CLASS witness segment")
    if segment.segment_ref.key != f"class:{segment.class_instance_id}":
        raise ValueError("Class segment record key does not match class_instance_id")
    rows_text_hash = commit_state_rows_text_hash_and_count(segment.rows_text)
    if rows_text_hash is None:
        raise ValueError("Class segment record has invalid rows_text")
    row_hash, row_count = rows_text_hash
    if segment.row_hash != row_hash or segment.row_count != row_count:
        raise ValueError("Class segment record row hash/count mismatch")
    if (
        segment.segment_ref.row_hash != row_hash
        or segment.segment_ref.row_count != row_count
    ):
        raise ValueError("Class segment record witness row hash/count mismatch")
    if segment.segment_ref.digest != compute_commit_state_segment_digest(
        kind=segment.segment_ref.kind,
        key=segment.segment_ref.key,
        row_count=segment.segment_ref.row_count,
        row_hash=segment.segment_ref.row_hash,
    ):
        raise ValueError("Class segment record witness digest mismatch")
    if segment.snapshot_payload.get("id") != str(segment.class_instance_id):
        raise ValueError("Class segment record snapshot payload id mismatch")
    return {
        "v": OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_RECORD_VERSION,
        "schema": OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_CLASS_SEGMENT_RECORD_SCHEMA,
        "class_instance_id": str(segment.class_instance_id),
        "class_config_id": str(segment.class_config_id),
        "source_object_id": (
            str(segment.source_object_id)
            if segment.source_object_id is not None
            else None
        ),
        "rows_text": segment.rows_text,
        "segment": commit_state_segment_ref_payload(segment.segment_ref),
        "snapshot_payload": segment.snapshot_payload,
    }


def raw_class_segment_record_data(
    segment: ObjectInstanceGraphSnapshotStateRawClassSegment,
) -> str:
    return _dump_json(raw_class_segment_record_payload(segment)) + "\n"


def commit_state_class_rows_by_raw_id(
    rows: Iterable[CommitStateRow],
) -> dict[str, tuple[CommitStateRow, ...]]:
    rows_by_id: dict[str, list[CommitStateRow]] = {}
    for row in rows:
        if row.kind == "NODE":
            rows_by_id.setdefault(row.value, []).append(row)
        elif row.kind == "ATTR":
            rows_by_id.setdefault(row.key, []).append(row)
    return {
        class_instance_id: tuple(member_rows)
        for class_instance_id, member_rows in rows_by_id.items()
    }


def _dump_json(payload: JsonObject) -> str:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def _coerce_json_object(payload: object, *, error_message: str) -> JsonObject:
    if not isinstance(payload, dict):
        raise ValueError(error_message)
    source = cast(dict[object, object], payload)
    typed_payload: JsonObject = {}
    for raw_key, raw_value in source.items():
        if not isinstance(raw_key, str):
            raise ValueError(error_message)
        typed_payload[raw_key] = raw_value
    return typed_payload


def _coerce_json_object_view(payload: object, *, error_message: str) -> JsonObject:
    if not isinstance(payload, dict):
        raise ValueError(error_message)
    for raw_key in payload:
        if not isinstance(raw_key, str):
            raise ValueError(error_message)
    return cast(JsonObject, payload)


def _json_optional_string(payload: JsonObject, key: str) -> str | None:
    value = payload.get(key)
    if isinstance(value, str):
        return value
    return None


def _json_required_string(payload: JsonObject, key: str) -> str:
    value = _json_optional_string(payload, key)
    if value is None:
        raise ValueError(f"Missing required JSON string: {key}")
    return value


def _json_optional_uuid(payload: JsonObject, key: str) -> UUID | None:
    value = _json_optional_string(payload, key)
    if value is None:
        return None
    return UUID(value)


def _json_required_uuid(payload: JsonObject, key: str) -> UUID:
    value = _json_optional_uuid(payload, key)
    if value is None:
        raise ValueError(f"Missing required JSON UUID: {key}")
    return value


def _json_optional_int(payload: JsonObject, key: str) -> int | None:
    value = payload.get(key)
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None


def _json_required_int(payload: JsonObject, key: str) -> int:
    value = _json_optional_int(payload, key)
    if value is None:
        raise ValueError(f"Missing required JSON integer: {key}")
    return value


def _json_required_list(payload: JsonObject, key: str) -> list[object]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ValueError(f"Missing required JSON list: {key}")
    return value
