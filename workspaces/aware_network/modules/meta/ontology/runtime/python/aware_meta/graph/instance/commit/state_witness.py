from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import hashlib
from typing import Literal
from uuid import UUID

from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)

from aware_meta.graph.instance.commit.state_index import (
    CommitStateIndex,
    CommitStateRow,
    _canonical_commit_state_index,
    apply_commit_state_index_row_changes,
    build_class_instance_state_rows,
    compute_commit_state_rows_hash,
)


CommitStateSegmentKind = Literal["CLASS", "ORPHAN_ATTR", "EDGE"]

COMMIT_STATE_WITNESS_SCHEMA = "aware.oig.commit_state_witness.v1"
COMMIT_STATE_SEGMENT_SCHEMA = "aware.oig.commit_state_segment.v1"
COMMIT_STATE_WITNESS_CURSOR_SCHEMA = "aware.oig.commit_state_witness_cursor.v1"
COMMIT_STATE_WITNESS_CURSOR_CHUNK_SCHEMA = (
    "aware.oig.commit_state_witness_cursor_chunk.v1"
)
DEFAULT_COMMIT_STATE_WITNESS_CURSOR_CHUNK_SIZE = 64


@dataclass(frozen=True, slots=True)
class CommitStateSegment:
    kind: CommitStateSegmentKind
    key: str
    rows: tuple[CommitStateRow, ...]
    row_hash: str
    digest: str

    def ref(self) -> CommitStateSegmentRef:
        return CommitStateSegmentRef(
            kind=self.kind,
            key=self.key,
            row_count=len(self.rows),
            row_hash=self.row_hash,
            digest=self.digest,
        )


@dataclass(frozen=True, slots=True)
class CommitStateSegmentRef:
    kind: CommitStateSegmentKind
    key: str
    row_count: int
    row_hash: str
    digest: str


@dataclass(frozen=True, slots=True)
class CommitStateWitness:
    schema: str
    state_hash: str
    witness_hash: str
    row_count: int
    segments: tuple[CommitStateSegment, ...]

    @property
    def rows(self) -> tuple[CommitStateRow, ...]:
        return tuple(row for segment in self.segments for row in segment.rows)

    def state_index(self) -> CommitStateIndex:
        return CommitStateIndex(rows=self.rows)

    def segment_digests_by_key(self) -> Mapping[str, str]:
        return {segment.key: segment.digest for segment in self.segments}

    def ref(self) -> CommitStateWitnessRef:
        return CommitStateWitnessRef(
            schema=self.schema,
            state_hash=self.state_hash,
            witness_hash=self.witness_hash,
            row_count=self.row_count,
            segments=tuple(segment.ref() for segment in self.segments),
        )


@dataclass(frozen=True, slots=True)
class CommitStateWitnessRef:
    schema: str
    state_hash: str | None
    witness_hash: str
    row_count: int
    segments: tuple[CommitStateSegmentRef, ...]

    def segment_digests_by_key(self) -> Mapping[str, str]:
        return {segment.key: segment.digest for segment in self.segments}


@dataclass(frozen=True, slots=True)
class CommitStateWitnessCursorChunk:
    index: int
    segment_keys: tuple[str, ...]
    row_count: int
    segments: tuple[CommitStateSegmentRef, ...]
    digest: str


@dataclass(frozen=True, slots=True)
class CommitStateWitnessCursorChunkSummary:
    index: int
    first_segment_key: str
    last_segment_key: str
    segment_count: int
    row_count: int
    digest: str


@dataclass(frozen=True, slots=True)
class CommitStateWitnessCursor:
    schema: str
    state_hash: str | None
    legacy_witness_hash: str | None
    cursor_hash: str
    row_count: int
    segment_count: int
    chunk_size: int
    chunks: tuple[CommitStateWitnessCursorChunk, ...]

    def summary(self) -> CommitStateWitnessCursorSummary:
        return CommitStateWitnessCursorSummary(
            schema=self.schema,
            state_hash=self.state_hash,
            legacy_witness_hash=self.legacy_witness_hash,
            cursor_hash=self.cursor_hash,
            row_count=self.row_count,
            segment_count=self.segment_count,
            chunk_size=self.chunk_size,
            chunks=tuple(
                CommitStateWitnessCursorChunkSummary(
                    index=chunk.index,
                    first_segment_key=chunk.segment_keys[0],
                    last_segment_key=chunk.segment_keys[-1],
                    segment_count=len(chunk.segments),
                    row_count=chunk.row_count,
                    digest=chunk.digest,
                )
                for chunk in self.chunks
            ),
        )

    def segment_digests_by_key(self) -> Mapping[str, str]:
        return {
            segment.key: segment.digest
            for chunk in self.chunks
            for segment in chunk.segments
        }


@dataclass(frozen=True, slots=True)
class CommitStateWitnessCursorSummary:
    schema: str
    state_hash: str | None
    legacy_witness_hash: str | None
    cursor_hash: str
    row_count: int
    segment_count: int
    chunk_size: int
    chunks: tuple[CommitStateWitnessCursorChunkSummary, ...]


def build_commit_state_witness(
    state_index: CommitStateIndex,
) -> CommitStateWitness:
    canonical_state_index = _canonical_commit_state_index(state_index.rows)
    segments = tuple(_commit_state_segments_from_rows(canonical_state_index.rows))
    return CommitStateWitness(
        schema=COMMIT_STATE_WITNESS_SCHEMA,
        state_hash=canonical_state_index.compute_hash(),
        witness_hash=compute_commit_state_witness_hash(segments),
        row_count=len(canonical_state_index.rows),
        segments=segments,
    )


def build_commit_state_witness_ref(
    state_index: CommitStateIndex,
) -> CommitStateWitnessRef:
    return build_commit_state_witness(state_index).ref()


def build_commit_state_witness_cursor(
    ref: CommitStateWitnessRef,
    *,
    chunk_size: int = DEFAULT_COMMIT_STATE_WITNESS_CURSOR_CHUNK_SIZE,
) -> CommitStateWitnessCursor:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if not validate_commit_state_witness_ref(ref):
        raise ValueError("Cannot build cursor from invalid witness ref")
    chunks = tuple(
        _commit_state_witness_cursor_chunk(index=index, segments=segments)
        for index, segments in enumerate(_chunked(ref.segments, chunk_size))
    )
    return _commit_state_witness_cursor(
        state_hash=ref.state_hash,
        legacy_witness_hash=ref.witness_hash,
        chunk_size=chunk_size,
        chunks=chunks,
    )


def compute_commit_state_witness_hash(
    segments: Iterable[CommitStateSegment | CommitStateSegmentRef],
) -> str:
    digest = hashlib.sha256()
    digest.update(COMMIT_STATE_WITNESS_SCHEMA.encode("utf-8"))
    digest.update(b"\n")
    for segment in segments:
        digest.update(segment.digest.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def compute_commit_state_witness_cursor_chunk_hash(
    segments: Iterable[CommitStateSegmentRef],
) -> str:
    digest = hashlib.sha256()
    digest.update(COMMIT_STATE_WITNESS_CURSOR_CHUNK_SCHEMA.encode("utf-8"))
    digest.update(b"\n")
    for segment in segments:
        digest.update(segment.digest.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def compute_commit_state_witness_cursor_hash(
    chunks: Iterable[
        CommitStateWitnessCursorChunk | CommitStateWitnessCursorChunkSummary
    ],
) -> str:
    digest = hashlib.sha256()
    digest.update(COMMIT_STATE_WITNESS_CURSOR_SCHEMA.encode("utf-8"))
    digest.update(b"\n")
    for chunk in chunks:
        digest.update(chunk.digest.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def validate_commit_state_witness_cursor_summary(
    summary: CommitStateWitnessCursorSummary,
) -> bool:
    if summary.schema != COMMIT_STATE_WITNESS_CURSOR_SCHEMA:
        return False
    if summary.state_hash is not None and not summary.state_hash:
        return False
    if summary.legacy_witness_hash is not None and not summary.legacy_witness_hash:
        return False
    if not summary.cursor_hash or summary.chunk_size <= 0:
        return False
    row_count = 0
    segment_count = 0
    for expected_index, chunk in enumerate(summary.chunks):
        if chunk.index != expected_index:
            return False
        if (
            not chunk.first_segment_key
            or not chunk.last_segment_key
            or chunk.segment_count <= 0
            or chunk.row_count < 0
            or not chunk.digest
        ):
            return False
        row_count += chunk.row_count
        segment_count += chunk.segment_count
    return (
        row_count == summary.row_count
        and segment_count == summary.segment_count
        and compute_commit_state_witness_cursor_hash(summary.chunks)
        == summary.cursor_hash
    )


def validate_commit_state_witness_cursor_chunk(
    chunk: CommitStateWitnessCursorChunk,
) -> bool:
    if chunk.index < 0:
        return False
    if not chunk.segments or not chunk.segment_keys:
        return False
    if len(chunk.segments) != len(chunk.segment_keys):
        return False
    if tuple(segment.key for segment in chunk.segments) != chunk.segment_keys:
        return False
    row_count = 0
    segment_keys: set[str] = set()
    for segment in chunk.segments:
        if segment.key in segment_keys or not _commit_state_segment_ref_valid(segment):
            return False
        segment_keys.add(segment.key)
        row_count += segment.row_count
    return (
        chunk.row_count == row_count
        and chunk.digest
        == compute_commit_state_witness_cursor_chunk_hash(chunk.segments)
    )


def validate_commit_state_witness_ref(ref: CommitStateWitnessRef) -> bool:
    if ref.schema != COMMIT_STATE_WITNESS_SCHEMA:
        return False
    if ref.state_hash is not None and not ref.state_hash:
        return False
    row_count = 0
    for segment in ref.segments:
        if segment.row_count < 0 or not segment.row_hash or not segment.digest:
            return False
        if not _commit_state_segment_ref_valid(segment):
            return False
        row_count += segment.row_count
    return (
        row_count == ref.row_count
        and compute_commit_state_witness_hash(ref.segments) == ref.witness_hash
    )


def validate_commit_state_witness_cursor(cursor: CommitStateWitnessCursor) -> bool:
    if cursor.schema != COMMIT_STATE_WITNESS_CURSOR_SCHEMA:
        return False
    if cursor.state_hash is not None and not cursor.state_hash:
        return False
    if cursor.legacy_witness_hash is not None and not cursor.legacy_witness_hash:
        return False
    if not cursor.cursor_hash or cursor.chunk_size <= 0:
        return False
    row_count = 0
    segment_count = 0
    segment_keys: set[str] = set()
    for expected_index, chunk in enumerate(cursor.chunks):
        if chunk.index != expected_index:
            return False
        if not chunk.segments or not chunk.segment_keys:
            return False
        if len(chunk.segments) != len(chunk.segment_keys):
            return False
        if tuple(segment.key for segment in chunk.segments) != chunk.segment_keys:
            return False
        chunk_row_count = 0
        for segment in chunk.segments:
            if segment.key in segment_keys or not _commit_state_segment_ref_valid(
                segment
            ):
                return False
            segment_keys.add(segment.key)
            chunk_row_count += segment.row_count
        if chunk.row_count != chunk_row_count:
            return False
        if chunk.digest != compute_commit_state_witness_cursor_chunk_hash(
            chunk.segments,
        ):
            return False
        row_count += chunk.row_count
        segment_count += len(chunk.segments)
    if row_count != cursor.row_count or segment_count != cursor.segment_count:
        return False
    if compute_commit_state_witness_cursor_hash(cursor.chunks) != cursor.cursor_hash:
        return False
    if cursor.legacy_witness_hash is not None:
        post_segments = tuple(
            segment for chunk in cursor.chunks for segment in chunk.segments
        )
        if compute_commit_state_witness_hash(post_segments) != (
            cursor.legacy_witness_hash
        ):
            return False
    return True


def replace_existing_commit_state_witness_ref_segments(
    *,
    pre_witness_ref: CommitStateWitnessRef,
    replacement_segments_by_key: Mapping[str, CommitStateSegmentRef],
    deleted_segment_keys: Iterable[str] = (),
    post_state_hash: str | None = None,
) -> CommitStateWitnessRef:
    """Apply segment-ref replacements without expanding unchanged state rows.

    Callers that still publish the legacy full row hash may pass
    `post_state_hash`. Segment-only callers can omit it and use `witness_hash`
    as the graph hash source. New segment keys are intentionally rejected until
    the ref shape carries enough ordering data for create-heavy transitions
    without row expansion.
    """

    if post_state_hash is not None and not post_state_hash:
        raise ValueError("post_state_hash must be non-empty when provided")
    if not validate_commit_state_witness_ref(pre_witness_ref):
        raise ValueError("pre_witness_ref is invalid")

    segments_by_key: dict[str, CommitStateSegmentRef] = {}
    for segment in pre_witness_ref.segments:
        if segment.key in segments_by_key:
            raise ValueError(f"Duplicate pre-state witness segment key: {segment.key}")
        segments_by_key[segment.key] = segment

    replacement_keys = set(replacement_segments_by_key)
    deleted_keys = set(deleted_segment_keys)
    unknown_keys = (replacement_keys | deleted_keys) - set(segments_by_key)
    if unknown_keys:
        raise ValueError(
            "Witness ref segment replacement cannot introduce unknown keys: "
            + ",".join(sorted(unknown_keys))
        )
    if replacement_keys & deleted_keys:
        raise ValueError("Witness ref segment keys cannot be replaced and deleted")

    for segment in replacement_segments_by_key.values():
        if segment.key not in replacement_keys:
            raise ValueError(
                "Witness ref replacement segment key does not match mapping key"
            )
        if segment.digest != compute_commit_state_segment_digest(
            kind=segment.kind,
            key=segment.key,
            row_count=segment.row_count,
            row_hash=segment.row_hash,
        ):
            raise ValueError(
                f"Witness ref replacement segment is invalid: {segment.key}"
            )

    post_segments = tuple(
        replacement_segments_by_key.get(segment.key, segment)
        for segment in pre_witness_ref.segments
        if segment.key not in deleted_keys
    )
    row_count = sum(segment.row_count for segment in post_segments)
    return CommitStateWitnessRef(
        schema=COMMIT_STATE_WITNESS_SCHEMA,
        state_hash=post_state_hash,
        witness_hash=compute_commit_state_witness_hash(post_segments),
        row_count=row_count,
        segments=post_segments,
    )


def replace_existing_commit_state_witness_cursor_segments(
    *,
    cursor: CommitStateWitnessCursor,
    replacement_segments_by_key: Mapping[str, CommitStateSegmentRef],
    deleted_segment_keys: Iterable[str] = (),
    post_state_hash: str | None = None,
) -> CommitStateWitnessCursor:
    """Apply segment-ref replacements through chunk-local cursor recomputation."""

    if post_state_hash is not None and not post_state_hash:
        raise ValueError("post_state_hash must be non-empty when provided")
    if not validate_commit_state_witness_cursor(cursor):
        raise ValueError("cursor is invalid")

    segments_by_key: dict[str, CommitStateSegmentRef] = {}
    for chunk in cursor.chunks:
        for segment in chunk.segments:
            if segment.key in segments_by_key:
                raise ValueError(f"Duplicate cursor segment key: {segment.key}")
            segments_by_key[segment.key] = segment

    replacement_keys = set(replacement_segments_by_key)
    deleted_keys = set(deleted_segment_keys)
    unknown_keys = (replacement_keys | deleted_keys) - set(segments_by_key)
    if unknown_keys:
        raise ValueError(
            "Witness cursor segment replacement cannot introduce unknown keys: "
            + ",".join(sorted(unknown_keys))
        )
    if replacement_keys & deleted_keys:
        raise ValueError("Witness cursor segment keys cannot be replaced and deleted")

    for key, segment in replacement_segments_by_key.items():
        if segment.key != key:
            raise ValueError(
                "Witness cursor replacement segment key does not match mapping key"
            )
        if not _commit_state_segment_ref_valid(segment):
            raise ValueError(
                f"Witness cursor replacement segment is invalid: {segment.key}"
            )

    chunks: list[CommitStateWitnessCursorChunk] = []
    for chunk in cursor.chunks:
        post_segments = tuple(
            replacement_segments_by_key.get(segment.key, segment)
            for segment in chunk.segments
            if segment.key not in deleted_keys
        )
        if post_segments:
            chunks.append(
                _commit_state_witness_cursor_chunk(
                    index=len(chunks),
                    segments=post_segments,
                )
            )
    legacy_witness_hash = compute_commit_state_witness_hash(
        segment for chunk in chunks for segment in chunk.segments
    )
    return _commit_state_witness_cursor(
        state_hash=post_state_hash,
        legacy_witness_hash=legacy_witness_hash,
        chunk_size=cursor.chunk_size,
        chunks=tuple(chunks),
    )


def replace_commit_state_witness_cursor_chunk_segments(
    *,
    chunk: CommitStateWitnessCursorChunk,
    replacement_segments_by_key: Mapping[str, CommitStateSegmentRef],
    deleted_segment_keys: Iterable[str] = (),
) -> CommitStateWitnessCursorChunk:
    """Apply replacements inside one cursor chunk without reading other chunks."""

    if not validate_commit_state_witness_cursor_chunk(chunk):
        raise ValueError("cursor chunk is invalid")
    segments_by_key = {segment.key: segment for segment in chunk.segments}
    replacement_keys = set(replacement_segments_by_key)
    deleted_keys = set(deleted_segment_keys)
    unknown_keys = (replacement_keys | deleted_keys) - set(segments_by_key)
    if unknown_keys:
        raise ValueError(
            "Witness cursor chunk replacement cannot introduce unknown keys: "
            + ",".join(sorted(unknown_keys))
        )
    if replacement_keys & deleted_keys:
        raise ValueError("Witness cursor chunk keys cannot be replaced and deleted")
    for key, segment in replacement_segments_by_key.items():
        if segment.key != key:
            raise ValueError(
                "Witness cursor chunk replacement segment key does not match mapping key"
            )
        if not _commit_state_segment_ref_valid(segment):
            raise ValueError(
                f"Witness cursor chunk replacement segment is invalid: {segment.key}"
            )
    post_segments = tuple(
        replacement_segments_by_key.get(segment.key, segment)
        for segment in chunk.segments
        if segment.key not in deleted_keys
    )
    return _commit_state_witness_cursor_chunk(
        index=chunk.index,
        segments=post_segments,
    )


def replace_existing_commit_state_witness_cursor_summary_chunks(
    *,
    summary: CommitStateWitnessCursorSummary,
    replacement_chunks_by_index: Mapping[int, CommitStateWitnessCursorChunk],
    post_state_hash: str | None = None,
    legacy_witness_hash: str | None = None,
) -> CommitStateWitnessCursorSummary:
    """Apply chunk replacements to a cursor summary without full segment refs."""

    if post_state_hash is not None and not post_state_hash:
        raise ValueError("post_state_hash must be non-empty when provided")
    if legacy_witness_hash is not None and not legacy_witness_hash:
        raise ValueError("legacy_witness_hash must be non-empty when provided")
    if not validate_commit_state_witness_cursor_summary(summary):
        raise ValueError("cursor summary is invalid")
    unknown_indexes = set(replacement_chunks_by_index) - {
        chunk.index for chunk in summary.chunks
    }
    if unknown_indexes:
        raise ValueError(
            "Witness cursor summary replacement cannot introduce unknown chunks: "
            + ",".join(str(index) for index in sorted(unknown_indexes))
        )
    replacement_summaries_by_index: dict[int, CommitStateWitnessCursorChunkSummary] = {}
    for index, chunk in replacement_chunks_by_index.items():
        if chunk.index != index:
            raise ValueError(
                "Witness cursor summary replacement chunk index does not match mapping"
            )
        if not validate_commit_state_witness_cursor_chunk(chunk):
            raise ValueError(
                f"Witness cursor summary replacement chunk is invalid: {index}"
            )
        replacement_summaries_by_index[index] = CommitStateWitnessCursorChunkSummary(
            index=chunk.index,
            first_segment_key=chunk.segment_keys[0],
            last_segment_key=chunk.segment_keys[-1],
            segment_count=len(chunk.segments),
            row_count=chunk.row_count,
            digest=chunk.digest,
        )
    post_chunks = tuple(
        replacement_summaries_by_index.get(chunk.index, chunk)
        for chunk in summary.chunks
    )
    return CommitStateWitnessCursorSummary(
        schema=summary.schema,
        state_hash=post_state_hash,
        legacy_witness_hash=legacy_witness_hash,
        cursor_hash=compute_commit_state_witness_cursor_hash(post_chunks),
        row_count=sum(chunk.row_count for chunk in post_chunks),
        segment_count=sum(chunk.segment_count for chunk in post_chunks),
        chunk_size=summary.chunk_size,
        chunks=post_chunks,
    )


def apply_commit_state_witness_changes(
    *,
    pre_witness: CommitStateWitness,
    changes: Iterable[ObjectInstanceGraphChange],
    post_class_instances_by_id: Mapping[UUID, ClassInstance],
) -> CommitStateWitness:
    return apply_commit_state_witness_row_changes(
        pre_witness=pre_witness,
        changes=changes,
        post_class_state_rows_by_id={
            class_instance_id: build_class_instance_state_rows(class_instance)
            for class_instance_id, class_instance in (
                post_class_instances_by_id.items()
            )
        },
    )


def apply_commit_state_witness_row_changes(
    *,
    pre_witness: CommitStateWitness,
    changes: Iterable[ObjectInstanceGraphChange],
    post_class_state_rows_by_id: Mapping[UUID, Iterable[CommitStateRow]],
) -> CommitStateWitness:
    state_index = apply_commit_state_index_row_changes(
        pre_state_index=pre_witness.state_index(),
        changes=changes,
        post_class_state_rows_by_id=post_class_state_rows_by_id,
    )
    return build_commit_state_witness(state_index)


def _commit_state_segments_from_rows(
    rows: tuple[CommitStateRow, ...],
) -> tuple[CommitStateSegment, ...]:
    segments: list[CommitStateSegment] = []
    index = 0
    while index < len(rows):
        row = rows[index]
        if row.kind == "NODE":
            class_instance_id = row.value
            segment_rows = [row]
            index += 1
            while (
                index < len(rows)
                and rows[index].kind == "ATTR"
                and rows[index].key == class_instance_id
            ):
                segment_rows.append(rows[index])
                index += 1
            segments.append(
                _commit_state_segment(
                    kind="CLASS",
                    key=_class_segment_key(UUID(class_instance_id)),
                    rows=tuple(segment_rows),
                )
            )
            continue
        if row.kind == "ATTR":
            class_instance_id = row.key
            segment_rows = [row]
            index += 1
            while (
                index < len(rows)
                and rows[index].kind == "ATTR"
                and rows[index].key == class_instance_id
            ):
                segment_rows.append(rows[index])
                index += 1
            segments.append(
                _commit_state_segment(
                    kind="ORPHAN_ATTR",
                    key=f"orphan_attr:{class_instance_id}",
                    rows=tuple(segment_rows),
                )
            )
            continue
        if row.kind == "EDGE":
            segments.append(
                _commit_state_segment(
                    kind="EDGE",
                    key=_edge_segment_key(row),
                    rows=(row,),
                )
            )
            index += 1
            continue
        raise ValueError(f"Unsupported CommitStateRow kind: {row.kind!r}")
    return tuple(segments)


def _commit_state_segment(
    *,
    kind: CommitStateSegmentKind,
    key: str,
    rows: tuple[CommitStateRow, ...],
) -> CommitStateSegment:
    row_hash = compute_commit_state_rows_hash(rows)
    return CommitStateSegment(
        kind=kind,
        key=key,
        rows=rows,
        row_hash=row_hash,
        digest=compute_commit_state_segment_digest(
            kind=kind,
            key=key,
            row_count=len(rows),
            row_hash=row_hash,
        ),
    )


def compute_commit_state_segment_digest(
    *,
    kind: CommitStateSegmentKind,
    key: str,
    row_count: int,
    row_hash: str,
) -> str:
    digest = hashlib.sha256()
    digest.update(COMMIT_STATE_SEGMENT_SCHEMA.encode("utf-8"))
    digest.update(b"\n")
    digest.update(kind.encode("utf-8"))
    digest.update(b"\n")
    digest.update(key.encode("utf-8"))
    digest.update(b"\n")
    digest.update(str(row_count).encode("utf-8"))
    digest.update(b"\n")
    digest.update(row_hash.encode("utf-8"))
    digest.update(b"\n")
    return digest.hexdigest()


def _commit_state_segment_ref_valid(segment: CommitStateSegmentRef) -> bool:
    return segment.digest == compute_commit_state_segment_digest(
        kind=segment.kind,
        key=segment.key,
        row_count=segment.row_count,
        row_hash=segment.row_hash,
    )


def _commit_state_witness_cursor_chunk(
    *,
    index: int,
    segments: tuple[CommitStateSegmentRef, ...],
) -> CommitStateWitnessCursorChunk:
    if not segments:
        raise ValueError("cursor chunk requires at least one segment")
    row_count = sum(segment.row_count for segment in segments)
    return CommitStateWitnessCursorChunk(
        index=index,
        segment_keys=tuple(segment.key for segment in segments),
        row_count=row_count,
        segments=segments,
        digest=compute_commit_state_witness_cursor_chunk_hash(segments),
    )


def _commit_state_witness_cursor(
    *,
    state_hash: str | None,
    legacy_witness_hash: str | None,
    chunk_size: int,
    chunks: tuple[CommitStateWitnessCursorChunk, ...],
) -> CommitStateWitnessCursor:
    row_count = sum(chunk.row_count for chunk in chunks)
    segment_count = sum(len(chunk.segments) for chunk in chunks)
    return CommitStateWitnessCursor(
        schema=COMMIT_STATE_WITNESS_CURSOR_SCHEMA,
        state_hash=state_hash,
        legacy_witness_hash=legacy_witness_hash,
        cursor_hash=compute_commit_state_witness_cursor_hash(chunks),
        row_count=row_count,
        segment_count=segment_count,
        chunk_size=chunk_size,
        chunks=chunks,
    )


def _chunked(
    items: tuple[CommitStateSegmentRef, ...],
    size: int,
) -> Iterable[tuple[CommitStateSegmentRef, ...]]:
    for index in range(0, len(items), size):
        yield items[index : index + size]


def _class_segment_key(class_instance_id: UUID) -> str:
    return f"class:{class_instance_id}"


def _edge_segment_key(row: CommitStateRow) -> str:
    return f"edge:{row.key}:{row.value}"


__all__ = [
    "COMMIT_STATE_SEGMENT_SCHEMA",
    "COMMIT_STATE_WITNESS_CURSOR_CHUNK_SCHEMA",
    "COMMIT_STATE_WITNESS_CURSOR_SCHEMA",
    "COMMIT_STATE_WITNESS_SCHEMA",
    "DEFAULT_COMMIT_STATE_WITNESS_CURSOR_CHUNK_SIZE",
    "CommitStateSegment",
    "CommitStateSegmentKind",
    "CommitStateSegmentRef",
    "CommitStateWitness",
    "CommitStateWitnessCursor",
    "CommitStateWitnessCursorChunk",
    "CommitStateWitnessCursorChunkSummary",
    "CommitStateWitnessCursorSummary",
    "CommitStateWitnessRef",
    "apply_commit_state_witness_changes",
    "apply_commit_state_witness_row_changes",
    "build_commit_state_witness",
    "build_commit_state_witness_cursor",
    "build_commit_state_witness_ref",
    "compute_commit_state_segment_digest",
    "compute_commit_state_witness_cursor_chunk_hash",
    "compute_commit_state_witness_cursor_hash",
    "compute_commit_state_witness_hash",
    "replace_existing_commit_state_witness_cursor_segments",
    "replace_existing_commit_state_witness_ref_segments",
    "validate_commit_state_witness_cursor",
    "validate_commit_state_witness_cursor_summary",
    "validate_commit_state_witness_ref",
]
