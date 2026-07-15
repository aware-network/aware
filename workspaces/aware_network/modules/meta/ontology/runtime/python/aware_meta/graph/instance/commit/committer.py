"""FS lane committer for canonical OIG commits.

This is the durability boundary for the meta "graph commit" rail:
runtime/executor produces:
  - `changes` (canonical Change graph)
  - `graph_hash_pre` / `graph_hash_post`

This module:
  - reads the lane HEAD (`FSCommitStore.head`)
  - derives the parent pointer (linear lane)
  - builds an `ObjectInstanceGraphCommit`
  - appends it to the lane store (`FSCommitStore.append`)

Invariants:
- No DB lookups
- Commit DAG does not mutate Branch objects (git-style)
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import time
from typing import cast
from uuid import UUID

from aware_history_ontology.commit.commit_enums import CommitStatus
from aware_history_ontology.change.change_enums import ChangeType
from aware_history_ontology.lane.lane import Lane
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta_ontology.stable_ids import stable_object_instance_graph_commit_id
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_code_ontology.code.code_enums import CodeLanguage

from aware_meta.graph.instance.commit.builder import (
    build_object_instance_graph_commit_from_changes,
    build_object_instance_graph_commit_from_shallow_changes,
    build_object_instance_graph_commit_record_from_body_draft,
    build_object_instance_graph_commit_record_from_shallow_changes,
    build_object_instance_graph_seed_commit,
    build_object_instance_graph_seed_commit_record,
)
from aware_meta.graph.instance.commit.body_codec import (
    OigCommitBodyDraft,
    build_oig_commit_body,
    object_instance_graph_changes_from_body_draft,
)
from aware_meta.graph.instance.commit.contract import (
    CommitActionDescriptor,
    LaneCommitBatchRequest,
    ObjectInstanceGraphCommitBodyRecord,
    ObjectInstanceGraphCommitGraphHashSource,
    ObjectInstanceGraphCommitPreStateEvidence,
    CommitStateIndex,
    ObjectInstanceGraphCommitRootMetadata,
)
from aware_meta.graph.instance.commit.hash_contract import compute_oig_lane_hash_state
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.perf_trace import (
    commit_perf_span,
    record_commit_perf_elapsed,
)
from aware_meta.graph.instance.commit.stored_commit_records import (
    object_instance_graph_commit_envelope_from_commit,
)
from aware_meta.graph.instance.commit.state_witness import (
    build_commit_state_witness_cursor,
    build_commit_state_witness_ref,
)
from aware_meta.graph.instance.commit.validator import (
    OigCommitValidationError,
    validate_object_instance_graph_commit,
)


class LaneCommitError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class LaneBeforeOigHashMismatchDetails:
    branch_id: UUID
    projection_hash: str
    object_instance_graph_id: UUID
    graph_hash_pre: str
    lane_hash: str
    raw_hash: str

    def to_dict(self) -> dict[str, object]:
        return {
            "branch_id": str(self.branch_id),
            "projection_hash": self.projection_hash,
            "object_instance_graph_id": str(self.object_instance_graph_id),
            "graph_hash_pre": self.graph_hash_pre,
            "lane_hash": self.lane_hash,
            "raw_hash": self.raw_hash,
        }


class LaneBeforeOigHashMismatchError(LaneCommitError):
    details: LaneBeforeOigHashMismatchDetails

    def __init__(self, *, details: LaneBeforeOigHashMismatchDetails) -> None:
        self.details = details
        super().__init__(self._build_message(details))

    @staticmethod
    def _build_message(details: LaneBeforeOigHashMismatchDetails) -> str:
        return (
            "before_oig hash must match graph_hash_pre under the lane hash contract: "
            f"lane_hash={details.lane_hash} raw_hash={details.raw_hash} "
            f"graph_hash_pre={details.graph_hash_pre} "
            f"branch_id={details.branch_id} projection_hash={details.projection_hash} "
            f"object_instance_graph_id={details.object_instance_graph_id}"
        )


@dataclass(frozen=True, slots=True)
class LaneStateIndexPreHashMismatchDetails:
    branch_id: UUID
    projection_hash: str
    object_instance_graph_id: UUID
    graph_hash_pre: str
    state_index_hash: str

    def to_dict(self) -> dict[str, object]:
        return {
            "branch_id": str(self.branch_id),
            "projection_hash": self.projection_hash,
            "object_instance_graph_id": str(self.object_instance_graph_id),
            "graph_hash_pre": self.graph_hash_pre,
            "state_index_hash": self.state_index_hash,
        }


class LaneStateIndexPreHashMismatchError(LaneCommitError):
    details: LaneStateIndexPreHashMismatchDetails

    def __init__(self, *, details: LaneStateIndexPreHashMismatchDetails) -> None:
        self.details = details
        super().__init__(self._build_message(details))

    @staticmethod
    def _build_message(details: LaneStateIndexPreHashMismatchDetails) -> str:
        return (
            "pre_state_index hash must match graph_hash_pre under the lane hash contract: "
            f"state_index_hash={details.state_index_hash} "
            f"graph_hash_pre={details.graph_hash_pre} "
            f"branch_id={details.branch_id} projection_hash={details.projection_hash} "
            f"object_instance_graph_id={details.object_instance_graph_id}"
        )


def _require_matching_pre_state_evidence(
    *,
    pre_state_evidence: ObjectInstanceGraphCommitPreStateEvidence,
    branch_id: UUID,
    projection_hash: str,
    object_instance_graph_id: UUID,
    graph_hash_pre: str,
    perf: dict[str, int],
) -> None:
    graph_hash_source = pre_state_evidence.graph_hash_source
    perf["pre_state_hash_evidence_hit"] = 1
    if graph_hash_source == "state_hash":
        if not pre_state_evidence.state_hash:
            raise LaneCommitError("pre_state_evidence.state_hash is required")
        evidence_graph_hash = pre_state_evidence.state_hash
        perf["pre_state_graph_hash_source_state_hash_hit"] = 1
    elif graph_hash_source == "witness_hash":
        if not pre_state_evidence.witness_hash:
            raise LaneCommitError(
                "pre_state_evidence.witness_hash is required when "
                + "graph_hash_source is witness_hash"
            )
        evidence_graph_hash = pre_state_evidence.witness_hash
        perf["pre_state_graph_hash_source_witness_hash_hit"] = 1
    elif graph_hash_source == "witness_cursor_hash":
        if not pre_state_evidence.witness_cursor_hash:
            raise LaneCommitError(
                "pre_state_evidence.witness_cursor_hash is required when "
                + "graph_hash_source is witness_cursor_hash"
            )
        evidence_graph_hash = pre_state_evidence.witness_cursor_hash
        perf["pre_state_graph_hash_source_witness_cursor_hash_hit"] = 1
    else:
        raise LaneCommitError(
            "Unsupported pre_state_evidence.graph_hash_source: "
            + f"{graph_hash_source!r}"
        )
    if pre_state_evidence.witness_hash:
        perf["pre_state_witness_hash_evidence_hit"] = 1
    if pre_state_evidence.witness_cursor_hash:
        perf["pre_state_witness_cursor_hash_evidence_hit"] = 1
    if pre_state_evidence.row_count is not None:
        perf["pre_state_evidence_row_count"] = max(pre_state_evidence.row_count, 0)
    if evidence_graph_hash != graph_hash_pre:
        raise LaneStateIndexPreHashMismatchError(
            details=LaneStateIndexPreHashMismatchDetails(
                branch_id=branch_id,
                projection_hash=projection_hash,
                object_instance_graph_id=object_instance_graph_id,
                graph_hash_pre=graph_hash_pre,
                state_index_hash=evidence_graph_hash,
            )
        )


def _record_lane_committer_elapsed(
    *,
    phase: str,
    started: float,
    metadata: Mapping[str, object],
) -> None:
    record_commit_perf_elapsed(
        phase=f"oig_lane_committer.{phase}",
        started=started,
        category="meta.oig.lane_committer",
        metadata=metadata,
    )


def _body_draft_shape_metrics(body_draft: OigCommitBodyDraft) -> dict[str, int]:
    class_instance_change_count = 0
    attribute_change_count = 0
    attribute_value_change_count = 0
    relationship_change_count = 0
    for root in body_draft.roots:
        class_instance_change_count += len(root.class_instance_changes)
        relationship_change_count += len(root.class_instance_relationship_changes)
        for class_instance_change in root.class_instance_changes:
            attribute_change_count += len(class_instance_change.attribute_changes)
            for attribute_change in class_instance_change.attribute_changes:
                if attribute_change.value_root_change is not None:
                    attribute_value_change_count += 1
    return {
        "body_draft_root_count": len(body_draft.roots),
        "body_draft_class_instance_change_count": class_instance_change_count,
        "body_draft_attribute_change_count": attribute_change_count,
        "body_draft_attribute_value_change_count": attribute_value_change_count,
        "body_draft_relationship_change_count": relationship_change_count,
    }


def _coerce_change_type(value: object) -> ChangeType:
    if isinstance(value, ChangeType):
        return value
    raw = getattr(value, "value", value)
    try:
        return ChangeType(str(raw))
    except ValueError:
        text = str(value)
        for change_type in ChangeType:
            if text in {change_type.name, f"ChangeType.{change_type.name}"}:
                return change_type
        raise


def _field_delta_property(field: object) -> str | None:
    value = getattr(field, "property", None)
    return value if isinstance(value, str) else None


def _field_delta_payload_value(field: object) -> object:
    payload = getattr(field, "payload", None)
    if payload is None and hasattr(field, "value"):
        payload = getattr(field, "value")
    if isinstance(payload, Mapping):
        return payload.get("value")
    return payload


def _body_draft_attribute_config_id(attribute_change: object) -> UUID | None:
    change = getattr(attribute_change, "change", None)
    fields = getattr(change, "fields", ()) if change is not None else ()
    for field in fields:
        if _field_delta_property(field) != "attribute_config_id":
            continue
        value = _field_delta_payload_value(field)
        if value is None:
            return None
        return value if isinstance(value, UUID) else UUID(str(value))
    return None


def _validate_body_draft_against_pre_state_index(
    *,
    body_draft: OigCommitBodyDraft | None,
    pre_state_index: CommitStateIndex | None,
) -> None:
    if body_draft is None or pre_state_index is None:
        return

    pre_state_maps = pre_state_index.row_maps(include_relationship_keys=False)
    pre_node_ids = frozenset(pre_state_maps.class_state_rows_by_id)
    pre_attribute_config_ids_by_class_instance_id: dict[UUID, set[UUID]] = {}
    for class_instance_id, rows in pre_state_maps.class_state_rows_by_id.items():
        attribute_config_ids: set[UUID] = set()
        for row in rows:
            if row.kind != "ATTR":
                continue
            raw_attribute_config_id, separator, _fingerprint = row.value.partition(":")
            if not separator:
                continue
            attribute_config_ids.add(UUID(raw_attribute_config_id))
        pre_attribute_config_ids_by_class_instance_id[class_instance_id] = (
            attribute_config_ids
        )

    for root in body_draft.roots:
        for class_change in root.class_instance_changes:
            class_instance_id = class_change.class_instance_id
            class_operation = _coerce_change_type(class_change.change.type)
            class_exists = class_instance_id in pre_node_ids
            if class_operation == ChangeType.create and class_exists:
                raise LaneCommitError(
                    "OIG shallow body draft cannot CREATE existing ClassInstance: "
                    + f"class_instance_id={class_instance_id}"
                )
            if class_operation in (ChangeType.update, ChangeType.delete) and (
                not class_exists
            ):
                raise LaneCommitError(
                    "OIG shallow body draft cannot "
                    + f"{class_operation.value.upper()} missing ClassInstance: "
                    + f"class_instance_id={class_instance_id}"
                )

            existing_attribute_config_ids = (
                pre_attribute_config_ids_by_class_instance_id.get(
                    class_instance_id,
                    set(),
                )
            )
            for attribute_change in class_change.attribute_changes:
                attribute_operation = _coerce_change_type(
                    attribute_change.change.type,
                )
                attribute_config_id = _body_draft_attribute_config_id(
                    attribute_change,
                )
                if attribute_config_id is None:
                    continue
                attribute_exists = attribute_config_id in existing_attribute_config_ids
                if attribute_operation == ChangeType.create and attribute_exists:
                    raise LaneCommitError(
                        "OIG shallow body draft cannot CREATE existing Attribute: "
                        + f"class_instance_id={class_instance_id} "
                        + f"attribute_id={attribute_change.attribute_id} "
                        + f"attribute_config_id={attribute_config_id}"
                    )
                if attribute_operation in (
                    ChangeType.update,
                    ChangeType.delete,
                ) and (not attribute_exists):
                    raise LaneCommitError(
                        "OIG shallow body draft cannot "
                        + f"{attribute_operation.value.upper()} missing Attribute: "
                        + f"class_instance_id={class_instance_id} "
                        + f"attribute_id={attribute_change.attribute_id} "
                        + f"attribute_config_id={attribute_config_id}"
                    )


@dataclass(frozen=True, slots=True)
class LaneHeadPreHashMismatchDetails:
    branch_id: UUID
    projection_hash: str
    object_instance_graph_id: UUID
    head_commit_id: UUID | None
    head_graph_hash_post: str
    graph_hash_pre: str

    def to_dict(self) -> dict[str, object]:
        return {
            "branch_id": str(self.branch_id),
            "projection_hash": self.projection_hash,
            "object_instance_graph_id": str(self.object_instance_graph_id),
            "head_commit_id": (
                None if self.head_commit_id is None else str(self.head_commit_id)
            ),
            "head_graph_hash_post": self.head_graph_hash_post,
            "graph_hash_pre": self.graph_hash_pre,
        }


class LaneHeadPreHashMismatchError(LaneCommitError):
    details: LaneHeadPreHashMismatchDetails

    def __init__(self, *, details: LaneHeadPreHashMismatchDetails) -> None:
        self.details = details
        super().__init__(self._build_message(details))

    @staticmethod
    def _build_message(details: LaneHeadPreHashMismatchDetails) -> str:
        return (
            "Lane pre-hash mismatch: "
            f"head_graph_hash_post={details.head_graph_hash_post} "
            f"graph_hash_pre={details.graph_hash_pre} "
            f"branch_id={details.branch_id} projection_hash={details.projection_hash} "
            f"head_commit_id={details.head_commit_id} "
            f"object_instance_graph_id={details.object_instance_graph_id}"
        )


DEFAULT_SOURCE_LANGUAGE: CodeLanguage = CodeLanguage("python")
DEFAULT_COMMIT_STATUS: CommitStatus = CommitStatus("local")


def _lane_commit_trace_metadata(
    *,
    branch_id: UUID,
    projection_hash: str,
    object_instance_graph_identity_id: UUID,
    object_instance_graph_id: UUID,
    change_count: int,
    commit_action: CommitActionDescriptor | None,
) -> dict[str, object]:
    return {
        "branch_id": str(branch_id),
        "projection_hash": projection_hash,
        "object_instance_graph_identity_id": str(object_instance_graph_identity_id),
        "object_instance_graph_id": str(object_instance_graph_id),
        "change_count": change_count,
        "operation_label": (
            commit_action.operation_label if commit_action is not None else None
        ),
    }


@dataclass(frozen=True, slots=True)
class _LaneHeadState:
    commit_id: UUID | None = None
    graph_hash_post: str | None = None
    object_instance_graph_id: UUID | None = None


def _decode_optional_uuid_field(
    *, head: Mapping[object, object], field_name: str
) -> UUID | None:
    raw_value = head.get(field_name)
    if raw_value is None:
        return None
    if not isinstance(raw_value, str) or not raw_value.strip():
        raise LaneCommitError(f"Lane HEAD {field_name} must be a non-empty UUID string")
    try:
        return UUID(raw_value)
    except ValueError as exc:
        raise LaneCommitError(
            f"Lane HEAD {field_name} must be a UUID string: {raw_value!r}"
        ) from exc


def _decode_optional_string_field(
    *, head: Mapping[object, object], field_name: str
) -> str | None:
    raw_value = head.get(field_name)
    if raw_value is None:
        return None
    if not isinstance(raw_value, str):
        raise LaneCommitError(f"Lane HEAD {field_name} must be a string")
    return raw_value


def _decode_lane_head_state(*, head: object) -> _LaneHeadState:
    if head is None:
        return _LaneHeadState()
    if not isinstance(head, dict):
        raise LaneCommitError("Lane HEAD payload must be a JSON object")
    head_payload = cast(Mapping[object, object], head)
    return _LaneHeadState(
        commit_id=_decode_optional_uuid_field(
            head=head_payload, field_name="commit_id"
        ),
        graph_hash_post=_decode_optional_string_field(
            head=head_payload, field_name="graph_hash_post"
        ),
        object_instance_graph_id=_decode_optional_uuid_field(
            head=head_payload,
            field_name="object_instance_graph_id",
        ),
    )


def _canonicalize_existing_commit_identity_metadata(
    *,
    commit: ObjectInstanceGraphCommit,
    object_instance_graph_identity_id: UUID,
    object_instance_graph_id: UUID,
) -> tuple[ObjectInstanceGraphCommit, bool]:
    if commit.object_instance_graph_id != object_instance_graph_id:
        raise LaneCommitError(
            "Existing HEAD commit targets unexpected object_instance_graph_id: "
            + f"expected={object_instance_graph_id} got={commit.object_instance_graph_id}"
        )
    if commit.object_instance_graph_identity_id == object_instance_graph_identity_id:
        return commit, False

    return (
        commit.model_copy(
            update={
                "id": stable_object_instance_graph_commit_id(
                    object_instance_graph_identity_id=object_instance_graph_identity_id,
                    commit_id=commit.commit.id,
                ),
                "object_instance_graph_identity_id": object_instance_graph_identity_id,
            }
        ),
        True,
    )


async def _require_idempotent_head_envelope(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID,
    object_instance_graph_identity_id: UUID,
    object_instance_graph_id: UUID,
    graph_hash_post: str,
) -> tuple[UUID | None, ...]:
    envelope = await store.get_commit_envelope(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
    )
    if envelope is None:
        raise LaneCommitError(
            f"Lane HEAD points to {commit_id} but commit envelope is missing"
        )
    if envelope.object_instance_graph_id != object_instance_graph_id:
        raise LaneCommitError(
            "Existing HEAD envelope targets unexpected object_instance_graph_id: "
            + f"expected={object_instance_graph_id} got={envelope.object_instance_graph_id}"
        )
    if envelope.object_instance_graph_identity_id != object_instance_graph_identity_id:
        raise LaneCommitError(
            "Existing HEAD envelope targets unexpected object_instance_graph_identity_id: "
            + f"expected={object_instance_graph_identity_id} "
            + f"got={envelope.object_instance_graph_identity_id}"
        )
    if envelope.graph_hash_post != graph_hash_post:
        raise LaneCommitError(
            "Existing HEAD envelope graph_hash_post mismatch: "
            + f"expected={graph_hash_post} got={envelope.graph_hash_post}"
        )
    return envelope.parent_commit_ids


class FSLaneCommitter:
    """Commit changes to a filesystem-backed lane."""

    def __init__(self, store: FSCommitStore | None = None) -> None:
        self._store: FSCommitStore = store or FSCommitStore()
        self._last_commit_perf_profile: dict[str, int] = {}

    @staticmethod
    def _elapsed_ms(*, started: float, ended: float | None = None) -> int:
        stop = time.monotonic() if ended is None else ended
        return max(int((stop - started) * 1000), 0)

    def last_commit_perf_profile_snapshot(self) -> dict[str, int]:
        return dict(self._last_commit_perf_profile)

    async def commit_many(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        requests: Sequence[LaneCommitBatchRequest],
    ) -> tuple[ObjectInstanceGraphCommit, ...]:
        """
        Append a linear batch of same-lane commits under one store append.

        The caller remains responsible for providing sequential pre-state OIGs.
        This method verifies the supplied graph hash chain and builds parent
        pointers from one resolved lane HEAD plus prior commits in the batch.
        """
        commit_started = time.monotonic()
        request_tuple = tuple(requests)
        if not projection_hash:
            raise LaneCommitError("projection_hash is required")
        if not request_tuple:
            raise LaneCommitError("commit_many requires at least one request")

        first_request = request_tuple[0]
        metadata = _lane_commit_trace_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_instance_graph_identity_id=(
                first_request.object_instance_graph_identity_id
            ),
            object_instance_graph_id=first_request.object_instance_graph_id,
            change_count=sum(len(tuple(request.changes)) for request in request_tuple),
            commit_action=first_request.commit_action,
        )
        metadata["batch_request_count"] = len(request_tuple)
        perf: dict[str, int] = {
            "batch_request_count": len(request_tuple),
            "batch_commit_count": len(request_tuple),
        }

        expected_object_projection_graph_identity_id = (
            first_request.object_projection_graph_identity_id
        )
        expected_object_instance_graph_identity_id = (
            first_request.object_instance_graph_identity_id
        )
        expected_object_instance_graph_id = first_request.object_instance_graph_id
        previous_graph_hash_post: str | None = None
        with commit_perf_span(
            phase="runtime.invoke_function.domain_commit.batch_pre_hash_validate",
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            pre_hash_validate_started = time.monotonic()
            for index, request in enumerate(request_tuple):
                if not request.graph_hash_post:
                    raise LaneCommitError("graph_hash_post is required")
                if request.before_oig.id != request.object_instance_graph_id:
                    raise LaneCommitError(
                        "before_oig.id must match object_instance_graph_id: "
                        + f"before_oig.id={request.before_oig.id} "
                        + f"object_instance_graph_id={request.object_instance_graph_id}"
                    )
                if not tuple(request.changes):
                    raise LaneCommitError(
                        "commit_many requires changes in every request"
                    )
                if (
                    request.object_projection_graph_identity_id
                    != expected_object_projection_graph_identity_id
                ):
                    raise LaneCommitError(
                        "Batch object_projection_graph_identity_id mismatch: "
                        + f"expected={expected_object_projection_graph_identity_id} "
                        + f"got={request.object_projection_graph_identity_id}"
                    )
                if (
                    request.object_instance_graph_identity_id
                    != expected_object_instance_graph_identity_id
                ):
                    raise LaneCommitError(
                        "Batch object_instance_graph_identity_id mismatch: "
                        + f"expected={expected_object_instance_graph_identity_id} "
                        + f"got={request.object_instance_graph_identity_id}"
                    )
                if (
                    request.object_instance_graph_id
                    != expected_object_instance_graph_id
                ):
                    raise LaneCommitError(
                        "Batch object_instance_graph_id mismatch: "
                        + f"expected={expected_object_instance_graph_id} "
                        + f"got={request.object_instance_graph_id}"
                    )
                if (
                    previous_graph_hash_post
                    and request.graph_hash_pre
                    and request.graph_hash_pre != previous_graph_hash_post
                ):
                    raise LaneCommitError(
                        "Batch graph_hash_pre mismatch: "
                        + f"request_index={index} expected={previous_graph_hash_post} "
                        + f"got={request.graph_hash_pre}"
                    )

                if request.pre_state_evidence is not None:
                    _require_matching_pre_state_evidence(
                        pre_state_evidence=request.pre_state_evidence,
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        object_instance_graph_id=request.object_instance_graph_id,
                        graph_hash_pre=request.graph_hash_pre,
                        perf=perf,
                    )
                    request.before_oig.hash = request.graph_hash_pre
                    perf["pre_state_evidence_check_count"] = (
                        perf.get("pre_state_evidence_check_count", 0) + 1
                    )
                elif request.pre_state_index is not None:
                    state_index_hash = request.pre_state_index.compute_hash()
                    if state_index_hash != request.graph_hash_pre:
                        raise LaneStateIndexPreHashMismatchError(
                            details=LaneStateIndexPreHashMismatchDetails(
                                branch_id=branch_id,
                                projection_hash=projection_hash,
                                object_instance_graph_id=(
                                    request.object_instance_graph_id
                                ),
                                graph_hash_pre=request.graph_hash_pre,
                                state_index_hash=state_index_hash,
                            )
                        )
                    request.before_oig.hash = request.graph_hash_pre
                    perf["pre_state_index_hash_count"] = (
                        perf.get("pre_state_index_hash_count", 0) + 1
                    )
                else:
                    pre_hash_state = compute_oig_lane_hash_state(
                        graph=request.before_oig,
                        schema_attribute_configs_by_id=(
                            request.schema_attribute_configs_by_id
                        ),
                        expected_hash=request.graph_hash_pre,
                    )
                    if request.graph_hash_pre and not pre_hash_state.matches(
                        request.graph_hash_pre
                    ):
                        raise LaneBeforeOigHashMismatchError(
                            details=LaneBeforeOigHashMismatchDetails(
                                branch_id=branch_id,
                                projection_hash=projection_hash,
                                object_instance_graph_id=(
                                    request.object_instance_graph_id
                                ),
                                graph_hash_pre=request.graph_hash_pre,
                                lane_hash=pre_hash_state.lane_hash,
                                raw_hash=pre_hash_state.raw_hash,
                            )
                        )
                    request.before_oig.hash = pre_hash_state.matched_hash_or_default(
                        request.graph_hash_pre
                    )

                for ch in tuple(request.changes):
                    if ch.object_instance_graph_id != request.object_instance_graph_id:
                        raise LaneCommitError(
                            "ObjectInstanceGraphChange targets unexpected "
                            "object_instance_graph_id: "
                            + f"expected={request.object_instance_graph_id} "
                            + f"got={ch.object_instance_graph_id}"
                        )
                previous_graph_hash_post = request.graph_hash_post
            perf["pre_hash_validate_ms"] = self._elapsed_ms(
                started=pre_hash_validate_started
            )

        with commit_perf_span(
            phase="runtime.invoke_function.domain_commit.batch_head_resolve",
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            head_resolve_started = time.monotonic()
            head = await self._store.head(
                branch_id=branch_id, projection_hash=projection_hash
            )
            perf["head_resolve_ms"] = self._elapsed_ms(started=head_resolve_started)
        head_state = _decode_lane_head_state(head=head)
        head_commit_id = head_state.commit_id
        head_post_hash = head_state.graph_hash_post
        head_oig_id = head_state.object_instance_graph_id
        if head_oig_id is not None and head_oig_id != expected_object_instance_graph_id:
            raise LaneCommitError(
                "Lane OIG id mismatch: "
                + f"head_object_instance_graph_id={head_oig_id} "
                + f"expected_object_instance_graph_id={expected_object_instance_graph_id}"
            )
        if (
            head_post_hash
            and first_request.graph_hash_pre
            and head_post_hash != first_request.graph_hash_pre
        ):
            raise LaneHeadPreHashMismatchError(
                details=LaneHeadPreHashMismatchDetails(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    object_instance_graph_id=expected_object_instance_graph_id,
                    head_commit_id=head_commit_id,
                    head_graph_hash_post=head_post_hash,
                    graph_hash_pre=first_request.graph_hash_pre,
                )
            )

        commits: list[ObjectInstanceGraphCommit] = []
        records: list[ObjectInstanceGraphCommitBodyRecord] = []
        parent_commit_id = head_commit_id
        with commit_perf_span(
            phase="runtime.invoke_function.domain_commit.batch_build_commit_payload",
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            build_payload_started = time.monotonic()
            for request in request_tuple:
                graph_hash_source: ObjectInstanceGraphCommitGraphHashSource = (
                    request.pre_state_evidence.graph_hash_source
                    if request.pre_state_evidence is not None
                    else "state_hash"
                )
                source_language = request.source_language or DEFAULT_SOURCE_LANGUAGE
                status = request.status or DEFAULT_COMMIT_STATUS
                commit = build_object_instance_graph_commit_from_changes(
                    before_oig=request.before_oig,
                    changes=list(request.changes),
                    branch_id=branch_id,
                    object_instance_graph_identity_id=(
                        request.object_instance_graph_identity_id
                    ),
                    object_instance_graph_id=request.object_instance_graph_id,
                    projection_hash=projection_hash,
                    graph_hash_pre=request.graph_hash_pre,
                    graph_hash_post=request.graph_hash_post,
                    graph_hash_source=graph_hash_source,
                    author_id=request.author_id,
                    parent_commit_id=parent_commit_id,
                    commit_id=request.commit_id,
                    source_language=source_language,
                    status=status,
                )
                commits.append(commit)
                commit_id = commit.commit.id
                root_metadata = request.root_metadata
                if root_metadata is None:
                    record = ObjectInstanceGraphCommitBodyRecord(
                        envelope=object_instance_graph_commit_envelope_from_commit(
                            branch_id=branch_id,
                            projection_hash=projection_hash,
                            commit=commit,
                        ),
                        body=build_oig_commit_body(commit),
                    )
                elif request.body_draft is not None:
                    record = build_object_instance_graph_commit_record_from_body_draft(
                        root_metadata=root_metadata,
                        body_draft=request.body_draft,
                        branch_id=branch_id,
                        object_instance_graph_identity_id=(
                            request.object_instance_graph_identity_id
                        ),
                        object_instance_graph_id=request.object_instance_graph_id,
                        projection_hash=projection_hash,
                        graph_hash_pre=request.graph_hash_pre,
                        graph_hash_post=request.graph_hash_post,
                        author_id=request.author_id,
                        parent_commit_id=parent_commit_id,
                        commit_id=commit_id,
                        source_language=source_language,
                        status=status,
                        graph_hash_source=graph_hash_source,
                    )
                    perf["build_commit_record_from_body_draft_count"] = (
                        perf.get("build_commit_record_from_body_draft_count", 0) + 1
                    )
                else:
                    record = (
                        build_object_instance_graph_commit_record_from_shallow_changes(
                            root_metadata=root_metadata,
                            changes=list(request.changes),
                            branch_id=branch_id,
                            object_instance_graph_identity_id=(
                                request.object_instance_graph_identity_id
                            ),
                            object_instance_graph_id=request.object_instance_graph_id,
                            projection_hash=projection_hash,
                            graph_hash_pre=request.graph_hash_pre,
                            graph_hash_post=request.graph_hash_post,
                            author_id=request.author_id,
                            parent_commit_id=parent_commit_id,
                            commit_id=commit_id,
                            source_language=source_language,
                            status=status,
                            graph_hash_source=graph_hash_source,
                        )
                    )
                    perf["build_commit_record_from_shallow_count"] = (
                        perf.get("build_commit_record_from_shallow_count", 0) + 1
                    )
                _validate_body_draft_against_pre_state_index(
                    body_draft=request.body_draft,
                    pre_state_index=request.pre_state_index,
                )
                records.append(record)
                parent_commit_id = commit.commit.id
            perf["build_commit_payload_ms"] = self._elapsed_ms(
                started=build_payload_started
            )

        try:
            with commit_perf_span(
                phase="runtime.invoke_function.domain_commit.batch_validate_commit_payload",
                category="meta.runtime.invoke_function",
                metadata=metadata,
            ):
                validate_started = time.monotonic()
                for commit in commits:
                    validate_object_instance_graph_commit(
                        commit=commit,
                        expected_object_instance_graph_identity_id=(
                            expected_object_instance_graph_identity_id
                        ),
                        expected_object_instance_graph_id=(
                            expected_object_instance_graph_id
                        ),
                        expected_projection_hash=projection_hash,
                        require_linear_history=True,
                    )
                perf["validate_commit_payload_ms"] = self._elapsed_ms(
                    started=validate_started
                )
        except OigCommitValidationError as e:
            raise LaneCommitError(f"Invalid OIG batch commit payload: {e}") from e
        record_tuple = tuple(records)
        write_health_index = all(
            request.write_health_index for request in request_tuple
        )
        with commit_perf_span(
            phase="runtime.invoke_function.domain_commit.batch_store_append_records",
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            append_started = time.monotonic()
            append_perf = await self._store.append_records(
                branch_id=branch_id,
                projection_hash=projection_hash,
                records=record_tuple,
                root_object_ids=tuple(
                    request.root_object_id for request in request_tuple
                ),
                commit_actions=tuple(
                    request.commit_action for request in request_tuple
                ),
                object_projection_graph_identity_id=(
                    expected_object_projection_graph_identity_id
                ),
                write_health_index=write_health_index,
            )
            perf["append_records_ms"] = self._elapsed_ms(started=append_started)
        for metric_name, metric_value in append_perf.items():
            try:
                coerced_value = int(metric_value)
            except Exception:
                continue
            perf[f"append_{metric_name}"] = max(coerced_value, 0)
        perf["total_ms"] = self._elapsed_ms(started=commit_started)
        self._last_commit_perf_profile = perf
        return tuple(commits)

    async def commit_record_many(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        requests: Sequence[LaneCommitBatchRequest],
    ) -> tuple[ObjectInstanceGraphCommitBodyRecord, ...]:
        """Append ordered body-draft records without legacy commit wrappers."""

        commit_started = time.monotonic()
        request_tuple = tuple(requests)
        if not projection_hash:
            raise LaneCommitError("projection_hash is required")
        if not request_tuple:
            raise LaneCommitError("commit_record_many requires at least one request")

        first_request = request_tuple[0]
        metadata = _lane_commit_trace_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_instance_graph_identity_id=(
                first_request.object_instance_graph_identity_id
            ),
            object_instance_graph_id=first_request.object_instance_graph_id,
            change_count=0,
            commit_action=first_request.commit_action,
        )
        metadata["batch_request_count"] = len(request_tuple)
        metadata["record_native"] = True
        perf: dict[str, int] = {
            "batch_request_count": len(request_tuple),
            "batch_record_count": len(request_tuple),
            "record_native_batch_count": 1,
        }

        expected_opgi_id = first_request.object_projection_graph_identity_id
        expected_oigi_id = first_request.object_instance_graph_identity_id
        expected_oig_id = first_request.object_instance_graph_id
        previous_graph_hash_post: str | None = None
        with commit_perf_span(
            phase="runtime.invoke_function.domain_commit.record_batch_pre_hash_validate",
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            pre_hash_validate_started = time.monotonic()
            for request_index, request in enumerate(request_tuple):
                if not request.graph_hash_pre:
                    raise LaneCommitError("graph_hash_pre is required")
                if not request.graph_hash_post:
                    raise LaneCommitError("graph_hash_post is required")
                if request.before_oig.id != request.object_instance_graph_id:
                    raise LaneCommitError(
                        "before_oig.id must match object_instance_graph_id: "
                        + f"before_oig.id={request.before_oig.id} "
                        + f"object_instance_graph_id={request.object_instance_graph_id}"
                    )
                if request.body_draft is None or not request.body_draft.roots:
                    raise LaneCommitError(
                        "commit_record_many requires a non-empty body draft "
                        f"in request {request_index}"
                    )
                if request.root_metadata is None:
                    raise LaneCommitError(
                        "commit_record_many requires root_metadata in every request"
                    )
                if request.object_projection_graph_identity_id != expected_opgi_id:
                    raise LaneCommitError(
                        "Batch object_projection_graph_identity_id mismatch: "
                        + f"expected={expected_opgi_id} "
                        + f"got={request.object_projection_graph_identity_id}"
                    )
                if request.object_instance_graph_identity_id != expected_oigi_id:
                    raise LaneCommitError(
                        "Batch object_instance_graph_identity_id mismatch: "
                        + f"expected={expected_oigi_id} "
                        + f"got={request.object_instance_graph_identity_id}"
                    )
                if request.object_instance_graph_id != expected_oig_id:
                    raise LaneCommitError(
                        "Batch object_instance_graph_id mismatch: "
                        + f"expected={expected_oig_id} "
                        + f"got={request.object_instance_graph_id}"
                    )
                if (
                    previous_graph_hash_post is not None
                    and request.graph_hash_pre != previous_graph_hash_post
                ):
                    raise LaneCommitError(
                        "Batch graph_hash_pre mismatch: "
                        + f"request_index={request_index} "
                        + f"expected={previous_graph_hash_post} "
                        + f"got={request.graph_hash_pre}"
                    )

                if request.pre_state_evidence is not None:
                    _require_matching_pre_state_evidence(
                        pre_state_evidence=request.pre_state_evidence,
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        object_instance_graph_id=request.object_instance_graph_id,
                        graph_hash_pre=request.graph_hash_pre,
                        perf=perf,
                    )
                    perf["pre_state_evidence_check_count"] = (
                        perf.get("pre_state_evidence_check_count", 0) + 1
                    )
                elif request.pre_state_index is not None:
                    state_index_hash = request.pre_state_index.compute_hash()
                    if state_index_hash != request.graph_hash_pre:
                        raise LaneStateIndexPreHashMismatchError(
                            details=LaneStateIndexPreHashMismatchDetails(
                                branch_id=branch_id,
                                projection_hash=projection_hash,
                                object_instance_graph_id=request.object_instance_graph_id,
                                graph_hash_pre=request.graph_hash_pre,
                                state_index_hash=state_index_hash,
                            )
                        )
                    perf["pre_state_index_hash_count"] = (
                        perf.get("pre_state_index_hash_count", 0) + 1
                    )
                else:
                    pre_hash_state = compute_oig_lane_hash_state(
                        graph=request.before_oig,
                        schema_attribute_configs_by_id=(
                            request.schema_attribute_configs_by_id
                        ),
                        expected_hash=request.graph_hash_pre,
                    )
                    if not pre_hash_state.matches(request.graph_hash_pre):
                        raise LaneBeforeOigHashMismatchError(
                            details=LaneBeforeOigHashMismatchDetails(
                                branch_id=branch_id,
                                projection_hash=projection_hash,
                                object_instance_graph_id=request.object_instance_graph_id,
                                graph_hash_pre=request.graph_hash_pre,
                                lane_hash=pre_hash_state.lane_hash,
                                raw_hash=pre_hash_state.raw_hash,
                            )
                        )
                _validate_body_draft_against_pre_state_index(
                    body_draft=request.body_draft,
                    pre_state_index=request.pre_state_index,
                )
                previous_graph_hash_post = request.graph_hash_post
            perf["pre_hash_validate_ms"] = self._elapsed_ms(
                started=pre_hash_validate_started
            )

        with commit_perf_span(
            phase="runtime.invoke_function.domain_commit.record_batch_head_resolve",
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            head_resolve_started = time.monotonic()
            head = await self._store.head(
                branch_id=branch_id,
                projection_hash=projection_hash,
            )
            perf["head_resolve_ms"] = self._elapsed_ms(started=head_resolve_started)
        head_state = _decode_lane_head_state(head=head)
        head_commit_id = head_state.commit_id
        if (
            head_state.object_instance_graph_id is not None
            and head_state.object_instance_graph_id != expected_oig_id
        ):
            raise LaneCommitError(
                "Lane OIG id mismatch: "
                + f"head_object_instance_graph_id={head_state.object_instance_graph_id} "
                + f"expected_object_instance_graph_id={expected_oig_id}"
            )
        if (
            head_state.graph_hash_post
            and head_state.graph_hash_post != first_request.graph_hash_pre
        ):
            raise LaneHeadPreHashMismatchError(
                details=LaneHeadPreHashMismatchDetails(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    object_instance_graph_id=expected_oig_id,
                    head_commit_id=head_commit_id,
                    head_graph_hash_post=head_state.graph_hash_post,
                    graph_hash_pre=first_request.graph_hash_pre,
                )
            )

        records: list[ObjectInstanceGraphCommitBodyRecord] = []
        parent_commit_id = head_commit_id
        with commit_perf_span(
            phase="runtime.invoke_function.domain_commit.record_batch_build_records",
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            build_records_started = time.monotonic()
            for request in request_tuple:
                body_draft = request.body_draft
                root_metadata = request.root_metadata
                if body_draft is None or root_metadata is None:
                    raise LaneCommitError(
                        "Record-native batch request lost required draft metadata"
                    )
                graph_hash_source: ObjectInstanceGraphCommitGraphHashSource = (
                    request.pre_state_evidence.graph_hash_source
                    if request.pre_state_evidence is not None
                    else "state_hash"
                )
                record = build_object_instance_graph_commit_record_from_body_draft(
                    root_metadata=root_metadata,
                    body_draft=body_draft,
                    branch_id=branch_id,
                    object_instance_graph_identity_id=(
                        request.object_instance_graph_identity_id
                    ),
                    object_instance_graph_id=request.object_instance_graph_id,
                    projection_hash=projection_hash,
                    graph_hash_pre=request.graph_hash_pre,
                    graph_hash_post=request.graph_hash_post,
                    author_id=request.author_id,
                    parent_commit_id=parent_commit_id,
                    commit_id=request.commit_id,
                    source_language=(
                        request.source_language or DEFAULT_SOURCE_LANGUAGE
                    ),
                    status=request.status or DEFAULT_COMMIT_STATUS,
                    graph_hash_source=graph_hash_source,
                )
                expected_parents = (
                    () if parent_commit_id is None else (parent_commit_id,)
                )
                if record.envelope.parent_commit_ids != expected_parents:
                    raise LaneCommitError(
                        "Record-native batch parent chain mismatch: "
                        + f"expected={expected_parents} "
                        + f"got={record.envelope.parent_commit_ids}"
                    )
                if (
                    record.envelope.object_instance_graph_identity_id
                    != expected_oigi_id
                ):
                    raise LaneCommitError("Invalid record-native batch OIGI id")
                if record.envelope.object_instance_graph_id != expected_oig_id:
                    raise LaneCommitError("Invalid record-native batch OIG id")
                if record.body.commit_id != record.envelope.commit_id:
                    raise LaneCommitError("Invalid record-native batch body commit id")
                records.append(record)
                parent_commit_id = record.commit_id
            perf["build_commit_payload_ms"] = self._elapsed_ms(
                started=build_records_started
            )
            perf["build_commit_record_from_body_draft_count"] = len(records)

        record_tuple = tuple(records)
        with commit_perf_span(
            phase="runtime.invoke_function.domain_commit.record_batch_store_append_records",
            category="meta.runtime.invoke_function",
            metadata=metadata,
        ):
            append_started = time.monotonic()
            append_perf = await self._store.append_records(
                branch_id=branch_id,
                projection_hash=projection_hash,
                records=record_tuple,
                root_object_ids=tuple(
                    request.root_object_id for request in request_tuple
                ),
                commit_actions=tuple(
                    request.commit_action for request in request_tuple
                ),
                object_projection_graph_identity_id=expected_opgi_id,
                write_health_index=all(
                    request.write_health_index for request in request_tuple
                ),
            )
            perf["append_records_ms"] = self._elapsed_ms(started=append_started)
        for metric_name, metric_value in append_perf.items():
            try:
                coerced_value = int(metric_value)
            except Exception:
                continue
            perf[f"append_{metric_name}"] = max(coerced_value, 0)
        perf["total_ms"] = self._elapsed_ms(started=commit_started)
        self._last_commit_perf_profile = perf
        return record_tuple

    async def commit_record_seed(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        object_projection_graph_identity_id: UUID | None = None,
        object_instance_graph_identity_id: UUID,
        object_instance_graph_id: UUID,
        pre_state_index: CommitStateIndex,
        root_metadata: ObjectInstanceGraphCommitRootMetadata,
        root_object_id: UUID | None = None,
        graph_hash_pre: str,
        graph_hash_post: str,
        author_id: UUID,
        commit_id: UUID | None = None,
        source_language: CodeLanguage = DEFAULT_SOURCE_LANGUAGE,
        status: CommitStatus = DEFAULT_COMMIT_STATUS,
        commit_action: CommitActionDescriptor | None = None,
        graph_hash_source: ObjectInstanceGraphCommitGraphHashSource = "state_hash",
    ) -> ObjectInstanceGraphCommitBodyRecord:
        """Append an empty-lane seed commit without the legacy ORM wrapper."""
        commit_started = time.monotonic()
        perf: dict[str, int] = {}
        if not projection_hash:
            raise LaneCommitError("projection_hash is required")
        if not graph_hash_pre:
            raise LaneCommitError("graph_hash_pre is required for seed append")
        if not graph_hash_post:
            raise LaneCommitError("graph_hash_post is required")
        if graph_hash_pre != graph_hash_post:
            raise LaneCommitError(
                "Seed append requires graph_hash_pre == graph_hash_post: "
                + f"pre={graph_hash_pre} post={graph_hash_post}"
            )

        graph_hash_check_started = time.monotonic()
        if graph_hash_source == "state_hash":
            state_index_hash = pre_state_index.compute_hash()
            perf["state_index_hash_ms"] = self._elapsed_ms(
                started=graph_hash_check_started
            )
            perf["seed_graph_hash_source_state_hash_hit"] = 1
        elif graph_hash_source == "witness_hash":
            state_index_hash = build_commit_state_witness_ref(
                pre_state_index,
            ).witness_hash
            perf["witness_hash_ms"] = self._elapsed_ms(started=graph_hash_check_started)
            perf["seed_graph_hash_source_witness_hash_hit"] = 1
        elif graph_hash_source == "witness_cursor_hash":
            state_index_hash = build_commit_state_witness_cursor(
                build_commit_state_witness_ref(pre_state_index),
            ).cursor_hash
            perf["witness_cursor_hash_ms"] = self._elapsed_ms(
                started=graph_hash_check_started
            )
            perf["seed_graph_hash_source_witness_cursor_hash_hit"] = 1
        else:
            raise LaneCommitError(
                f"Unsupported seed graph_hash_source: {graph_hash_source!r}"
            )
        if state_index_hash != graph_hash_pre:
            raise LaneStateIndexPreHashMismatchError(
                details=LaneStateIndexPreHashMismatchDetails(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    object_instance_graph_id=object_instance_graph_id,
                    graph_hash_pre=graph_hash_pre,
                    state_index_hash=state_index_hash,
                )
            )

        head_resolve_started = time.monotonic()
        head = await self._store.head(
            branch_id=branch_id, projection_hash=projection_hash
        )
        perf["head_resolve_ms"] = self._elapsed_ms(started=head_resolve_started)
        head_state = _decode_lane_head_state(head=head)
        head_commit_id = head_state.commit_id
        head_post_hash = head_state.graph_hash_post
        head_oig_id = head_state.object_instance_graph_id
        if head_oig_id is not None and head_oig_id != object_instance_graph_id:
            raise LaneCommitError(
                "Lane OIG id mismatch: "
                + f"head_object_instance_graph_id={head_oig_id} "
                + f"expected_object_instance_graph_id={object_instance_graph_id}"
            )

        if commit_id is not None and head_commit_id == commit_id:
            if head_post_hash and head_post_hash != graph_hash_post:
                raise LaneCommitError(
                    "Lane HEAD already at seed commit_id, but graph_hash_post mismatch: "
                    + f"head={head_post_hash} expected={graph_hash_post}"
                )
            _ = await _require_idempotent_head_envelope(
                store=self._store,
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                object_instance_graph_id=object_instance_graph_id,
                graph_hash_post=graph_hash_post,
            )
            record = await self._store.get_commit_record(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
            )
            if record is None:
                raise LaneCommitError(
                    f"Lane HEAD points to seed {commit_id} but commit record is missing"
                )
            perf["idempotent_head_hit"] = 1
            perf["total_ms"] = self._elapsed_ms(started=commit_started)
            self._last_commit_perf_profile = perf
            return record

        if head_commit_id is not None:
            raise LaneCommitError(
                "Seed append requires an empty lane: "
                + f"head_commit_id={head_commit_id}"
            )

        build_record_started = time.monotonic()
        record = build_object_instance_graph_seed_commit_record(
            root_metadata=root_metadata,
            branch_id=branch_id,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            object_instance_graph_id=object_instance_graph_id,
            projection_hash=projection_hash,
            graph_hash_pre=graph_hash_pre,
            graph_hash_post=graph_hash_post,
            author_id=author_id,
            commit_id=commit_id,
            source_language=source_language,
            status=status,
            graph_hash_source=graph_hash_source,
        )
        perf["build_commit_record_ms"] = self._elapsed_ms(started=build_record_started)

        validate_record_started = time.monotonic()
        if record.envelope.projection_hash != projection_hash:
            raise LaneCommitError("Invalid OIG seed record projection_hash")
        if (
            record.envelope.object_instance_graph_identity_id
            != object_instance_graph_identity_id
        ):
            raise LaneCommitError("Invalid OIG seed record OIGI id")
        if record.envelope.object_instance_graph_id != object_instance_graph_id:
            raise LaneCommitError("Invalid OIG seed record OIG id")
        if record.envelope.parent_commit_ids:
            raise LaneCommitError("Invalid OIG seed record parent commits")
        if record.body.commit_id != record.envelope.commit_id:
            raise LaneCommitError("Invalid OIG seed record body commit id")
        if record.body.payload.get("r"):
            raise LaneCommitError("Invalid OIG seed record contains changes")
        perf["validate_commit_record_ms"] = self._elapsed_ms(
            started=validate_record_started
        )

        append_started = time.monotonic()
        append_perf = await self._store.append_record(
            branch_id=branch_id,
            projection_hash=projection_hash,
            record=record,
            root_object_id=root_object_id or root_metadata.root_source_object_id,
            commit_action=commit_action,
            object_projection_graph_identity_id=object_projection_graph_identity_id,
        )
        perf["append_record_ms"] = self._elapsed_ms(started=append_started)
        for metric_name, metric_value in append_perf.items():
            try:
                coerced_value = int(metric_value)
            except Exception:
                continue
            perf[f"append_{metric_name}"] = max(coerced_value, 0)
        perf["total_ms"] = self._elapsed_ms(started=commit_started)
        self._last_commit_perf_profile = perf
        return record

    async def commit_record_shallow(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        object_projection_graph_identity_id: UUID | None = None,
        object_instance_graph_identity_id: UUID,
        object_instance_graph_id: UUID,
        pre_state_index: CommitStateIndex,
        root_metadata: ObjectInstanceGraphCommitRootMetadata,
        root_object_id: UUID | None = None,
        changes: list[ObjectInstanceGraphChange],
        body_draft: OigCommitBodyDraft | None = None,
        graph_hash_pre: str,
        graph_hash_post: str,
        author_id: UUID,
        commit_id: UUID | None = None,
        source_language: CodeLanguage = DEFAULT_SOURCE_LANGUAGE,
        status: CommitStatus = DEFAULT_COMMIT_STATUS,
        commit_action: CommitActionDescriptor | None = None,
    ) -> ObjectInstanceGraphCommitBodyRecord:
        """
        Append a shallow commit and return the durable envelope/body record.

        This is the hot path for callers that only need commit ids and lane
        metadata after append. It avoids constructing the legacy
        ObjectInstanceGraphCommit wrapper before the store write.
        """
        commit_started = time.monotonic()
        perf: dict[str, int] = {}
        if not projection_hash:
            raise LaneCommitError("projection_hash is required")
        if not graph_hash_pre:
            raise LaneCommitError("graph_hash_pre is required for shallow append")
        if not graph_hash_post:
            raise LaneCommitError("graph_hash_post is required")
        if not changes and (body_draft is None or not body_draft.roots):
            raise LaneCommitError(
                "changes or a non-empty body draft are required for shallow append"
            )

        state_index_hash_started = time.monotonic()
        state_index_hash = pre_state_index.compute_hash()
        perf["state_index_hash_ms"] = self._elapsed_ms(started=state_index_hash_started)
        if state_index_hash != graph_hash_pre:
            raise LaneStateIndexPreHashMismatchError(
                details=LaneStateIndexPreHashMismatchDetails(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    object_instance_graph_id=object_instance_graph_id,
                    graph_hash_pre=graph_hash_pre,
                    state_index_hash=state_index_hash,
                )
            )

        for ch in changes:
            if (
                ch.object_instance_graph_identity_id
                != object_instance_graph_identity_id
            ):
                raise LaneCommitError(
                    "ObjectInstanceGraphChange targets unexpected "
                    + "object_instance_graph_identity_id: "
                    + f"expected={object_instance_graph_identity_id} "
                    + f"got={ch.object_instance_graph_identity_id}"
                )
            if ch.object_instance_graph_id != object_instance_graph_id:
                raise LaneCommitError(
                    "ObjectInstanceGraphChange targets unexpected object_instance_graph_id: "
                    + f"expected={object_instance_graph_id} got={ch.object_instance_graph_id}"
                )

        head_resolve_started = time.monotonic()
        head = await self._store.head(
            branch_id=branch_id, projection_hash=projection_hash
        )
        perf["head_resolve_ms"] = self._elapsed_ms(started=head_resolve_started)
        head_state = _decode_lane_head_state(head=head)
        head_commit_id = head_state.commit_id
        head_post_hash = head_state.graph_hash_post
        head_oig_id = head_state.object_instance_graph_id
        if head_oig_id is not None and head_oig_id != object_instance_graph_id:
            raise LaneCommitError(
                "Lane OIG id mismatch: "
                + f"head_object_instance_graph_id={head_oig_id} "
                + f"expected_object_instance_graph_id={object_instance_graph_id}"
            )

        if commit_id is not None and head_commit_id == commit_id:
            if head_post_hash and head_post_hash != graph_hash_post:
                raise LaneCommitError(
                    "Lane HEAD already at commit_id, but graph_hash_post mismatch: "
                    + f"head={head_post_hash} expected={graph_hash_post}"
                )
            _ = await _require_idempotent_head_envelope(
                store=self._store,
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                object_instance_graph_id=object_instance_graph_id,
                graph_hash_post=graph_hash_post,
            )
            record = await self._store.get_commit_record(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
            )
            if record is None:
                raise LaneCommitError(
                    f"Lane HEAD points to {commit_id} but commit record is missing"
                )
            perf["idempotent_head_hit"] = 1
            perf["total_ms"] = self._elapsed_ms(started=commit_started)
            self._last_commit_perf_profile = perf
            return record

        if head_post_hash and head_post_hash != graph_hash_pre:
            raise LaneHeadPreHashMismatchError(
                details=LaneHeadPreHashMismatchDetails(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    object_instance_graph_id=object_instance_graph_id,
                    head_commit_id=head_commit_id,
                    head_graph_hash_post=head_post_hash,
                    graph_hash_pre=graph_hash_pre,
                )
            )

        build_record_started = time.monotonic()
        if body_draft is not None:
            record = build_object_instance_graph_commit_record_from_body_draft(
                root_metadata=root_metadata,
                body_draft=body_draft,
                branch_id=branch_id,
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                object_instance_graph_id=object_instance_graph_id,
                projection_hash=projection_hash,
                graph_hash_pre=graph_hash_pre,
                graph_hash_post=graph_hash_post,
                author_id=author_id,
                parent_commit_id=head_commit_id,
                commit_id=commit_id,
                source_language=source_language,
                status=status,
            )
            perf["build_commit_record_from_body_draft"] = 1
        else:
            record = build_object_instance_graph_commit_record_from_shallow_changes(
                root_metadata=root_metadata,
                changes=changes,
                branch_id=branch_id,
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                object_instance_graph_id=object_instance_graph_id,
                projection_hash=projection_hash,
                graph_hash_pre=graph_hash_pre,
                graph_hash_post=graph_hash_post,
                author_id=author_id,
                parent_commit_id=head_commit_id,
                commit_id=commit_id,
                source_language=source_language,
                status=status,
            )
        perf["build_commit_record_ms"] = self._elapsed_ms(started=build_record_started)

        validate_record_started = time.monotonic()
        if record.envelope.projection_hash != projection_hash:
            raise LaneCommitError(
                "Invalid OIG shallow commit record projection_hash: "
                + f"{record.envelope.projection_hash}"
            )
        if (
            record.envelope.object_instance_graph_identity_id
            != object_instance_graph_identity_id
        ):
            raise LaneCommitError("Invalid OIG shallow commit record OIGI id")
        if record.envelope.object_instance_graph_id != object_instance_graph_id:
            raise LaneCommitError("Invalid OIG shallow commit record OIG id")
        if record.body.commit_id != record.envelope.commit_id:
            raise LaneCommitError("Invalid OIG shallow commit record body commit id")
        _validate_body_draft_against_pre_state_index(
            body_draft=body_draft,
            pre_state_index=pre_state_index,
        )
        perf["validate_commit_record_ms"] = self._elapsed_ms(
            started=validate_record_started
        )

        append_started = time.monotonic()
        append_perf = await self._store.append_record(
            branch_id=branch_id,
            projection_hash=projection_hash,
            record=record,
            root_object_id=root_object_id or root_metadata.root_source_object_id,
            commit_action=commit_action,
            object_projection_graph_identity_id=object_projection_graph_identity_id,
        )
        perf["append_record_ms"] = self._elapsed_ms(started=append_started)
        for metric_name, metric_value in append_perf.items():
            try:
                coerced_value = int(metric_value)
            except Exception:
                continue
            perf[f"append_{metric_name}"] = max(coerced_value, 0)
        perf["total_ms"] = self._elapsed_ms(started=commit_started)
        self._last_commit_perf_profile = perf
        return record

    async def commit_record_shallow_from_pre_state_evidence(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        object_projection_graph_identity_id: UUID | None = None,
        object_instance_graph_identity_id: UUID,
        object_instance_graph_id: UUID,
        pre_state_evidence: ObjectInstanceGraphCommitPreStateEvidence,
        pre_state_index: CommitStateIndex | None = None,
        root_metadata: ObjectInstanceGraphCommitRootMetadata,
        root_object_id: UUID | None = None,
        changes: list[ObjectInstanceGraphChange],
        body_draft: OigCommitBodyDraft | None = None,
        graph_hash_pre: str,
        graph_hash_post: str,
        author_id: UUID,
        commit_id: UUID | None = None,
        source_language: CodeLanguage = DEFAULT_SOURCE_LANGUAGE,
        status: CommitStatus = DEFAULT_COMMIT_STATUS,
        commit_action: CommitActionDescriptor | None = None,
        write_health_index: bool = True,
    ) -> ObjectInstanceGraphCommitBodyRecord:
        """
        Append a shallow record using trusted pre-state hash evidence.

        This is for callers that already hold file-witnessed snapshot state and
        should not rebuild a full previous CommitStateIndex only to recompute
        `graph_hash_pre`.
        """
        commit_started = time.monotonic()
        perf: dict[str, int] = {}
        if not projection_hash:
            raise LaneCommitError("projection_hash is required")
        if not graph_hash_pre:
            raise LaneCommitError("graph_hash_pre is required for shallow append")
        if not graph_hash_post:
            raise LaneCommitError("graph_hash_post is required")
        if not changes and (body_draft is None or not body_draft.roots):
            raise LaneCommitError(
                "changes or a non-empty body draft are required for shallow append"
            )

        trace_metadata: dict[str, object] = {
            "branch_id": str(branch_id),
            "projection_hash": projection_hash,
            "commit_id": str(commit_id) if commit_id is not None else None,
            "object_instance_graph_id": str(object_instance_graph_id),
            "object_instance_graph_identity_id": str(object_instance_graph_identity_id),
            "change_count": len(changes),
            "body_draft": bool(body_draft is not None and body_draft.roots),
            "mode": "record_shallow_from_pre_state_evidence",
            "write_health_index": write_health_index,
        }

        pre_state_evidence_started = time.monotonic()
        _require_matching_pre_state_evidence(
            pre_state_evidence=pre_state_evidence,
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_instance_graph_id=object_instance_graph_id,
            graph_hash_pre=graph_hash_pre,
            perf=perf,
        )
        perf["pre_state_evidence_check_ms"] = self._elapsed_ms(
            started=pre_state_evidence_started
        )
        _record_lane_committer_elapsed(
            phase="record_shallow_pre_state_evidence.pre_state_evidence_check",
            started=pre_state_evidence_started,
            metadata=trace_metadata,
        )

        for ch in changes:
            if (
                ch.object_instance_graph_identity_id
                != object_instance_graph_identity_id
            ):
                raise LaneCommitError(
                    "ObjectInstanceGraphChange targets unexpected "
                    + "object_instance_graph_identity_id: "
                    + f"expected={object_instance_graph_identity_id} "
                    + f"got={ch.object_instance_graph_identity_id}"
                )
            if ch.object_instance_graph_id != object_instance_graph_id:
                raise LaneCommitError(
                    "ObjectInstanceGraphChange targets unexpected object_instance_graph_id: "
                    + f"expected={object_instance_graph_id} got={ch.object_instance_graph_id}"
                )

        head_resolve_started = time.monotonic()
        head = await self._store.head(
            branch_id=branch_id, projection_hash=projection_hash
        )
        perf["head_resolve_ms"] = self._elapsed_ms(started=head_resolve_started)
        _record_lane_committer_elapsed(
            phase="record_shallow_pre_state_evidence.head_resolve",
            started=head_resolve_started,
            metadata=trace_metadata,
        )
        head_state = _decode_lane_head_state(head=head)
        head_commit_id = head_state.commit_id
        head_post_hash = head_state.graph_hash_post
        head_oig_id = head_state.object_instance_graph_id
        if head_oig_id is not None and head_oig_id != object_instance_graph_id:
            raise LaneCommitError(
                "Lane OIG id mismatch: "
                + f"head_object_instance_graph_id={head_oig_id} "
                + f"expected_object_instance_graph_id={object_instance_graph_id}"
            )

        if commit_id is not None and head_commit_id == commit_id:
            if head_post_hash and head_post_hash != graph_hash_post:
                raise LaneCommitError(
                    "Lane HEAD already at commit_id, but graph_hash_post mismatch: "
                    + f"head={head_post_hash} expected={graph_hash_post}"
                )
            _ = await _require_idempotent_head_envelope(
                store=self._store,
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                object_instance_graph_id=object_instance_graph_id,
                graph_hash_post=graph_hash_post,
            )
            record = await self._store.get_commit_record(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
            )
            if record is None:
                raise LaneCommitError(
                    f"Lane HEAD points to {commit_id} but commit record is missing"
                )
            perf["idempotent_head_hit"] = 1
            perf["total_ms"] = self._elapsed_ms(started=commit_started)
            self._last_commit_perf_profile = perf
            return record

        if head_post_hash and head_post_hash != graph_hash_pre:
            raise LaneHeadPreHashMismatchError(
                details=LaneHeadPreHashMismatchDetails(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    object_instance_graph_id=object_instance_graph_id,
                    head_commit_id=head_commit_id,
                    head_graph_hash_post=head_post_hash,
                    graph_hash_pre=graph_hash_pre,
                )
            )

        build_record_started = time.monotonic()
        if body_draft is not None:
            body_draft_shape = _body_draft_shape_metrics(body_draft)
            perf.update(body_draft_shape)
            body_draft_record_started = time.monotonic()
            with commit_perf_span(
                phase=(
                    "oig_lane_committer.record_shallow_pre_state_evidence."
                    "build_body_draft_commit_record"
                ),
                category="meta.oig.lane_committer",
                metadata={**trace_metadata, **body_draft_shape},
            ):
                record = build_object_instance_graph_commit_record_from_body_draft(
                    root_metadata=root_metadata,
                    body_draft=body_draft,
                    branch_id=branch_id,
                    object_instance_graph_identity_id=(
                        object_instance_graph_identity_id
                    ),
                    object_instance_graph_id=object_instance_graph_id,
                    projection_hash=projection_hash,
                    graph_hash_pre=graph_hash_pre,
                    graph_hash_post=graph_hash_post,
                    author_id=author_id,
                    parent_commit_id=head_commit_id,
                    commit_id=commit_id,
                    source_language=source_language,
                    status=status,
                    graph_hash_source=pre_state_evidence.graph_hash_source,
                )
            perf["build_body_draft_commit_record_ms"] = self._elapsed_ms(
                started=body_draft_record_started
            )
            perf["build_commit_record_from_body_draft"] = 1
        else:
            record = build_object_instance_graph_commit_record_from_shallow_changes(
                root_metadata=root_metadata,
                changes=changes,
                branch_id=branch_id,
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                object_instance_graph_id=object_instance_graph_id,
                projection_hash=projection_hash,
                graph_hash_pre=graph_hash_pre,
                graph_hash_post=graph_hash_post,
                author_id=author_id,
                parent_commit_id=head_commit_id,
                commit_id=commit_id,
                source_language=source_language,
                status=status,
                graph_hash_source=pre_state_evidence.graph_hash_source,
            )
        perf["build_commit_record_ms"] = self._elapsed_ms(started=build_record_started)
        _record_lane_committer_elapsed(
            phase="record_shallow_pre_state_evidence.build_commit_record",
            started=build_record_started,
            metadata=trace_metadata,
        )

        validate_record_started = time.monotonic()
        if record.envelope.projection_hash != projection_hash:
            raise LaneCommitError(
                "Invalid OIG shallow commit record projection_hash: "
                + f"{record.envelope.projection_hash}"
            )
        if (
            record.envelope.object_instance_graph_identity_id
            != object_instance_graph_identity_id
        ):
            raise LaneCommitError("Invalid OIG shallow commit record OIGI id")
        if record.envelope.object_instance_graph_id != object_instance_graph_id:
            raise LaneCommitError("Invalid OIG shallow commit record OIG id")
        if record.body.commit_id != record.envelope.commit_id:
            raise LaneCommitError("Invalid OIG shallow commit record body commit id")
        _validate_body_draft_against_pre_state_index(
            body_draft=body_draft,
            pre_state_index=pre_state_index,
        )
        perf["validate_commit_record_ms"] = self._elapsed_ms(
            started=validate_record_started
        )
        _record_lane_committer_elapsed(
            phase="record_shallow_pre_state_evidence.validate_commit_record",
            started=validate_record_started,
            metadata=trace_metadata,
        )

        append_started = time.monotonic()
        append_perf = await self._store.append_record(
            branch_id=branch_id,
            projection_hash=projection_hash,
            record=record,
            root_object_id=root_object_id or root_metadata.root_source_object_id,
            commit_action=commit_action,
            object_projection_graph_identity_id=object_projection_graph_identity_id,
            write_health_index=write_health_index,
        )
        perf["append_record_ms"] = self._elapsed_ms(started=append_started)
        _record_lane_committer_elapsed(
            phase="record_shallow_pre_state_evidence.append_record",
            started=append_started,
            metadata=trace_metadata,
        )
        for metric_name, metric_value in append_perf.items():
            try:
                coerced_value = int(metric_value)
            except Exception:
                continue
            perf[f"append_{metric_name}"] = max(coerced_value, 0)
        perf["total_ms"] = self._elapsed_ms(started=commit_started)
        self._last_commit_perf_profile = perf
        return record

    async def commit_shallow(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        object_projection_graph_identity_id: UUID | None = None,
        object_instance_graph_identity_id: UUID,
        object_instance_graph_id: UUID,
        pre_state_index: CommitStateIndex,
        root_metadata: ObjectInstanceGraphCommitRootMetadata,
        root_object_id: UUID | None = None,
        changes: list[ObjectInstanceGraphChange],
        graph_hash_pre: str,
        graph_hash_post: str,
        author_id: UUID,
        commit_id: UUID | None = None,
        source_language: CodeLanguage = DEFAULT_SOURCE_LANGUAGE,
        status: CommitStatus = DEFAULT_COMMIT_STATUS,
        commit_action: CommitActionDescriptor | None = None,
    ) -> ObjectInstanceGraphCommit | None:
        """
        Append a commit using supplied root metadata and an indexed pre-state.

        This is the delta-first precondition path. It deliberately avoids
        hydrating or hashing a full before_oig object; callers must provide the
        canonical state index for the lane head they are advancing from.
        """
        commit_started = time.monotonic()
        perf: dict[str, int] = {}
        if not projection_hash:
            raise LaneCommitError("projection_hash is required")
        if not graph_hash_pre:
            raise LaneCommitError("graph_hash_pre is required for shallow append")
        if not graph_hash_post:
            raise LaneCommitError("graph_hash_post is required")
        if not changes:
            raise LaneCommitError("changes are required for shallow append")

        state_index_hash_started = time.monotonic()
        state_index_hash = pre_state_index.compute_hash()
        perf["state_index_hash_ms"] = self._elapsed_ms(started=state_index_hash_started)
        if state_index_hash != graph_hash_pre:
            raise LaneStateIndexPreHashMismatchError(
                details=LaneStateIndexPreHashMismatchDetails(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    object_instance_graph_id=object_instance_graph_id,
                    graph_hash_pre=graph_hash_pre,
                    state_index_hash=state_index_hash,
                )
            )

        for ch in changes:
            if (
                ch.object_instance_graph_identity_id
                != object_instance_graph_identity_id
            ):
                raise LaneCommitError(
                    "ObjectInstanceGraphChange targets unexpected "
                    + "object_instance_graph_identity_id: "
                    + f"expected={object_instance_graph_identity_id} "
                    + f"got={ch.object_instance_graph_identity_id}"
                )
            if ch.object_instance_graph_id != object_instance_graph_id:
                raise LaneCommitError(
                    "ObjectInstanceGraphChange targets unexpected object_instance_graph_id: "
                    + f"expected={object_instance_graph_id} got={ch.object_instance_graph_id}"
                )

        head_resolve_started = time.monotonic()
        head = await self._store.head(
            branch_id=branch_id, projection_hash=projection_hash
        )
        perf["head_resolve_ms"] = self._elapsed_ms(started=head_resolve_started)
        head_state = _decode_lane_head_state(head=head)
        head_commit_id = head_state.commit_id
        head_post_hash = head_state.graph_hash_post
        head_oig_id = head_state.object_instance_graph_id
        if head_oig_id is not None and head_oig_id != object_instance_graph_id:
            raise LaneCommitError(
                "Lane OIG id mismatch: "
                + f"head_object_instance_graph_id={head_oig_id} "
                + f"expected_object_instance_graph_id={object_instance_graph_id}"
            )

        if commit_id is not None and head_commit_id == commit_id:
            if head_post_hash and head_post_hash != graph_hash_post:
                raise LaneCommitError(
                    "Lane HEAD already at commit_id, but graph_hash_post mismatch: "
                    + f"head={head_post_hash} expected={graph_hash_post}"
                )
            parent_commit_ids = await _require_idempotent_head_envelope(
                store=self._store,
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                object_instance_graph_id=object_instance_graph_id,
                graph_hash_post=graph_hash_post,
            )
            existing = build_object_instance_graph_commit_from_shallow_changes(
                root_metadata=root_metadata,
                changes=changes,
                branch_id=branch_id,
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                object_instance_graph_id=object_instance_graph_id,
                projection_hash=projection_hash,
                graph_hash_pre=graph_hash_pre,
                graph_hash_post=graph_hash_post,
                author_id=author_id,
                parent_commit_id=parent_commit_ids[0] if parent_commit_ids else None,
                commit_id=commit_id,
                source_language=source_language,
                status=status,
            )
            perf["idempotent_head_hit"] = 1
            perf["total_ms"] = self._elapsed_ms(started=commit_started)
            self._last_commit_perf_profile = perf
            return existing

        if head_post_hash and head_post_hash != graph_hash_pre:
            raise LaneHeadPreHashMismatchError(
                details=LaneHeadPreHashMismatchDetails(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    object_instance_graph_id=object_instance_graph_id,
                    head_commit_id=head_commit_id,
                    head_graph_hash_post=head_post_hash,
                    graph_hash_pre=graph_hash_pre,
                )
            )

        build_payload_started = time.monotonic()
        oig_commit = build_object_instance_graph_commit_from_shallow_changes(
            root_metadata=root_metadata,
            changes=changes,
            branch_id=branch_id,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            object_instance_graph_id=object_instance_graph_id,
            projection_hash=projection_hash,
            graph_hash_pre=graph_hash_pre,
            graph_hash_post=graph_hash_post,
            author_id=author_id,
            parent_commit_id=head_commit_id,
            commit_id=commit_id,
            source_language=source_language,
            status=status,
        )
        perf["build_commit_payload_ms"] = self._elapsed_ms(
            started=build_payload_started
        )

        try:
            validate_payload_started = time.monotonic()
            validate_object_instance_graph_commit(
                commit=oig_commit,
                expected_object_instance_graph_identity_id=object_instance_graph_identity_id,
                expected_object_instance_graph_id=object_instance_graph_id,
                expected_projection_hash=projection_hash,
                require_linear_history=True,
            )
            perf["validate_commit_payload_ms"] = self._elapsed_ms(
                started=validate_payload_started
            )
        except OigCommitValidationError as e:
            raise LaneCommitError(f"Invalid OIG shallow commit payload: {e}") from e

        append_started = time.monotonic()
        append_perf = await self._store.append(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit=oig_commit,
            root_object_id=root_object_id or root_metadata.root_source_object_id,
            commit_action=commit_action,
            object_projection_graph_identity_id=object_projection_graph_identity_id,
        )
        perf["append_ms"] = self._elapsed_ms(started=append_started)
        for metric_name, metric_value in append_perf.items():
            try:
                coerced_value = int(metric_value)
            except Exception:
                continue
            perf[f"append_{metric_name}"] = max(coerced_value, 0)
        perf["total_ms"] = self._elapsed_ms(started=commit_started)
        self._last_commit_perf_profile = perf
        return oig_commit

    async def commit(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        object_projection_graph_identity_id: UUID | None = None,
        object_instance_graph_identity_id: UUID,
        object_instance_graph_id: UUID,
        before_oig: ObjectInstanceGraph,
        root_object_id: UUID | None = None,
        changes: list[ObjectInstanceGraphChange],
        graph_hash_pre: str,
        graph_hash_post: str,
        author_id: UUID,
        commit_id: UUID | None = None,
        source_language: CodeLanguage = DEFAULT_SOURCE_LANGUAGE,
        status: CommitStatus = DEFAULT_COMMIT_STATUS,
        commit_action: CommitActionDescriptor | None = None,
        schema_attribute_configs_by_id: Mapping[UUID, AttributeConfig] | None = None,
        body_draft: OigCommitBodyDraft | None = None,
    ) -> ObjectInstanceGraphCommit | None:
        """
        Append a new commit to the lane.

        Returns:
            The appended commit, or None when `changes` is empty.

        Raises:
            LaneCommitError on any precondition mismatch.
        """
        commit_started = time.monotonic()
        perf: dict[str, int] = {}
        if body_draft is not None:
            if changes:
                raise LaneCommitError(
                    "Domain commit cannot mix changes and body-draft evidence"
                )
            with commit_perf_span(
                phase=(
                    "runtime.invoke_function.domain_commit."
                    "hydrate_body_draft_compatibility_changes"
                ),
                category="meta.runtime.invoke_function",
                metadata={"body_draft_root_count": len(body_draft.roots)},
            ):
                changes = list(
                    object_instance_graph_changes_from_body_draft(
                        draft=body_draft,
                        object_instance_graph_identity_id=(
                            object_instance_graph_identity_id
                        ),
                        object_instance_graph_id=object_instance_graph_id,
                    )
                )
        trace_metadata = _lane_commit_trace_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            object_instance_graph_id=object_instance_graph_id,
            change_count=len(changes),
            commit_action=commit_action,
        )
        if not projection_hash:
            raise LaneCommitError("projection_hash is required")
        if not graph_hash_post:
            raise LaneCommitError("graph_hash_post is required")
        if before_oig.id != object_instance_graph_id:
            raise LaneCommitError(
                "before_oig.id must match object_instance_graph_id: "
                + f"before_oig.id={before_oig.id} object_instance_graph_id={object_instance_graph_id}"
            )
        with commit_perf_span(
            phase="runtime.invoke_function.domain_commit.pre_hash_validate",
            category="meta.runtime.invoke_function",
            metadata=trace_metadata,
        ):
            pre_hash_state = compute_oig_lane_hash_state(
                graph=before_oig,
                schema_attribute_configs_by_id=schema_attribute_configs_by_id,
                expected_hash=graph_hash_pre,
            )
        if graph_hash_pre and not pre_hash_state.matches(graph_hash_pre):
            raise LaneBeforeOigHashMismatchError(
                details=LaneBeforeOigHashMismatchDetails(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    object_instance_graph_id=object_instance_graph_id,
                    graph_hash_pre=graph_hash_pre,
                    lane_hash=pre_hash_state.lane_hash,
                    raw_hash=pre_hash_state.raw_hash,
                )
            )
        before_oig.hash = pre_hash_state.matched_hash_or_default(graph_hash_pre)

        # Sanity: ensure change trees target the expected OIG.
        for ch in changes:
            if ch.object_instance_graph_id != object_instance_graph_id:
                raise LaneCommitError(
                    "ObjectInstanceGraphChange targets unexpected object_instance_graph_id: "
                    + f"expected={object_instance_graph_id} got={ch.object_instance_graph_id}"
                )

        with commit_perf_span(
            phase="runtime.invoke_function.domain_commit.head_resolve",
            category="meta.runtime.invoke_function",
            metadata=trace_metadata,
        ):
            head_resolve_started = time.monotonic()
            head = await self._store.head(
                branch_id=branch_id, projection_hash=projection_hash
            )
            perf["head_resolve_ms"] = self._elapsed_ms(started=head_resolve_started)
        head_state = _decode_lane_head_state(head=head)
        head_commit_id = head_state.commit_id
        head_post_hash = head_state.graph_hash_post
        head_oig_id = head_state.object_instance_graph_id
        if head_oig_id is not None and head_oig_id != object_instance_graph_id:
            raise LaneCommitError(
                "Lane OIG id mismatch: "
                + f"head_object_instance_graph_id={head_oig_id} "
                + f"expected_object_instance_graph_id={object_instance_graph_id}"
            )

        if not changes:
            if head_commit_id is not None:
                with commit_perf_span(
                    phase="runtime.invoke_function.domain_commit.no_op_head_hit",
                    category="meta.runtime.invoke_function",
                    metadata=trace_metadata,
                ):
                    self._last_commit_perf_profile = {
                        "head_resolve_ms": perf.get("head_resolve_ms", 0),
                        "total_ms": self._elapsed_ms(started=commit_started),
                    }
                return None
            if root_object_id is None:
                raise LaneCommitError(
                    "root_object_id is required for initial rooted seed commit"
                )
            if graph_hash_pre != graph_hash_post:
                raise LaneCommitError(
                    "Initial rooted seed commit requires graph_hash_pre == graph_hash_post: "
                    + f"pre={graph_hash_pre} post={graph_hash_post}"
                )

            with commit_perf_span(
                phase="runtime.invoke_function.domain_commit.build_commit_payload",
                category="meta.runtime.invoke_function",
                metadata=trace_metadata,
            ):
                build_payload_started = time.monotonic()
                oig_commit = build_object_instance_graph_seed_commit(
                    rooted_oig=before_oig,
                    branch_id=branch_id,
                    object_instance_graph_identity_id=object_instance_graph_identity_id,
                    projection_hash=projection_hash,
                    graph_hash_pre=graph_hash_pre,
                    graph_hash_post=graph_hash_post,
                    author_id=author_id,
                    commit_id=commit_id,
                    source_language=source_language,
                    status=status,
                )
                perf["build_commit_payload_ms"] = self._elapsed_ms(
                    started=build_payload_started
                )
            try:
                with commit_perf_span(
                    phase="runtime.invoke_function.domain_commit.validate_commit_payload",
                    category="meta.runtime.invoke_function",
                    metadata=trace_metadata,
                ):
                    validate_payload_started = time.monotonic()
                    validate_object_instance_graph_commit(
                        commit=oig_commit,
                        expected_object_instance_graph_identity_id=object_instance_graph_identity_id,
                        expected_object_instance_graph_id=object_instance_graph_id,
                        expected_projection_hash=projection_hash,
                        require_linear_history=True,
                    )
                    perf["validate_commit_payload_ms"] = self._elapsed_ms(
                        started=validate_payload_started
                    )
            except OigCommitValidationError as e:
                raise LaneCommitError(f"Invalid OIG seed commit payload: {e}") from e

            with commit_perf_span(
                phase="runtime.invoke_function.domain_commit.store_append",
                category="meta.runtime.invoke_function",
                metadata=trace_metadata,
            ):
                append_started = time.monotonic()
                append_perf = await self._store.append(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    commit=oig_commit,
                    root_object_id=root_object_id,
                    commit_action=commit_action,
                    object_projection_graph_identity_id=object_projection_graph_identity_id,
                )
                perf["append_ms"] = self._elapsed_ms(started=append_started)
            for metric_name, metric_value in append_perf.items():
                try:
                    coerced_value = int(metric_value)
                except Exception:
                    continue
                perf[f"append_{metric_name}"] = max(coerced_value, 0)
            perf["total_ms"] = self._elapsed_ms(started=commit_started)
            self._last_commit_perf_profile = perf
            return oig_commit

        # Idempotency (v0): if caller supplies commit_id and lane head already equals it,
        # treat as already committed and return the stored commit.
        if commit_id is not None and head_commit_id == commit_id:
            if head_post_hash and head_post_hash != graph_hash_post:
                raise LaneCommitError(
                    "Lane HEAD already at commit_id, but graph_hash_post mismatch: "
                    + f"head={head_post_hash} expected={graph_hash_post}"
                )
            with commit_perf_span(
                phase="runtime.invoke_function.domain_commit.idempotent_head_envelope",
                category="meta.runtime.invoke_function",
                metadata=trace_metadata,
            ):
                parent_commit_ids = await _require_idempotent_head_envelope(
                    store=self._store,
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    commit_id=commit_id,
                    object_instance_graph_identity_id=object_instance_graph_identity_id,
                    object_instance_graph_id=object_instance_graph_id,
                    graph_hash_post=graph_hash_post,
                )
            existing = build_object_instance_graph_commit_from_changes(
                before_oig=before_oig,
                changes=changes,
                branch_id=branch_id,
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                object_instance_graph_id=object_instance_graph_id,
                projection_hash=projection_hash,
                graph_hash_pre=graph_hash_pre,
                graph_hash_post=graph_hash_post,
                author_id=author_id,
                parent_commit_id=parent_commit_ids[0] if parent_commit_ids else None,
                commit_id=commit_id,
                source_language=source_language,
                status=status,
            )
            perf["idempotent_head_hit"] = 1
            perf["total_ms"] = self._elapsed_ms(started=commit_started)
            self._last_commit_perf_profile = perf
            return existing

        # Pre-hash must match the lane's current head post-hash (when present).
        if head_post_hash and graph_hash_pre and head_post_hash != graph_hash_pre:
            raise LaneHeadPreHashMismatchError(
                details=LaneHeadPreHashMismatchDetails(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    object_instance_graph_id=object_instance_graph_id,
                    head_commit_id=head_commit_id,
                    head_graph_hash_post=head_post_hash,
                    graph_hash_pre=graph_hash_pre,
                )
            )

        with commit_perf_span(
            phase="runtime.invoke_function.domain_commit.build_commit_payload",
            category="meta.runtime.invoke_function",
            metadata=trace_metadata,
        ):
            build_payload_started = time.monotonic()
            oig_commit = build_object_instance_graph_commit_from_changes(
                before_oig=before_oig,
                changes=changes,
                branch_id=branch_id,
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                object_instance_graph_id=object_instance_graph_id,
                projection_hash=projection_hash,
                graph_hash_pre=graph_hash_pre,
                graph_hash_post=graph_hash_post,
                author_id=author_id,
                parent_commit_id=head_commit_id,
                commit_id=commit_id,
                source_language=source_language,
                status=status,
            )
            perf["build_commit_payload_ms"] = self._elapsed_ms(
                started=build_payload_started
            )

        try:
            with commit_perf_span(
                phase="runtime.invoke_function.domain_commit.validate_commit_payload",
                category="meta.runtime.invoke_function",
                metadata=trace_metadata,
            ):
                validate_payload_started = time.monotonic()
                validate_object_instance_graph_commit(
                    commit=oig_commit,
                    expected_object_instance_graph_identity_id=object_instance_graph_identity_id,
                    expected_object_instance_graph_id=object_instance_graph_id,
                    expected_projection_hash=projection_hash,
                    require_linear_history=True,
                )
                perf["validate_commit_payload_ms"] = self._elapsed_ms(
                    started=validate_payload_started
                )
        except OigCommitValidationError as e:
            raise LaneCommitError(f"Invalid OIG commit payload: {e}") from e

        with commit_perf_span(
            phase="runtime.invoke_function.domain_commit.store_append",
            category="meta.runtime.invoke_function",
            metadata=trace_metadata,
        ):
            append_started = time.monotonic()
            append_perf = await self._store.append(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit=oig_commit,
                root_object_id=root_object_id,
                commit_action=commit_action,
                object_projection_graph_identity_id=object_projection_graph_identity_id,
            )
            perf["append_ms"] = self._elapsed_ms(started=append_started)
        for metric_name, metric_value in append_perf.items():
            try:
                coerced_value = int(metric_value)
            except Exception:
                continue
            perf[f"append_{metric_name}"] = max(coerced_value, 0)
        perf["total_ms"] = self._elapsed_ms(started=commit_started)
        self._last_commit_perf_profile = perf

        return oig_commit

    async def commit_to_lane(
        self,
        *,
        lane: Lane,
        object_instance_graph_identity_id: UUID,
        object_instance_graph_id: UUID,
        before_oig: ObjectInstanceGraph,
        root_object_id: UUID | None = None,
        changes: list[ObjectInstanceGraphChange],
        graph_hash_pre: str,
        graph_hash_post: str,
        author_id: UUID,
        commit_id: UUID | None = None,
        source_language: CodeLanguage = DEFAULT_SOURCE_LANGUAGE,
        status: CommitStatus = DEFAULT_COMMIT_STATUS,
        commit_action: CommitActionDescriptor | None = None,
        schema_attribute_configs_by_id: Mapping[UUID, AttributeConfig] | None = None,
    ) -> ObjectInstanceGraphCommit | None:
        """Commit using a canonical `Lane` identity object (Lane.branch_id + Lane.lane_hash)."""
        return await self.commit(
            branch_id=lane.branch_id,
            projection_hash=lane.lane_hash,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            object_instance_graph_id=object_instance_graph_id,
            before_oig=before_oig,
            root_object_id=root_object_id,
            changes=changes,
            graph_hash_pre=graph_hash_pre,
            graph_hash_post=graph_hash_post,
            author_id=author_id,
            commit_id=commit_id,
            source_language=source_language,
            status=status,
            commit_action=commit_action,
            schema_attribute_configs_by_id=schema_attribute_configs_by_id,
        )

    async def commit_to_lane_shallow(
        self,
        *,
        lane: Lane,
        object_projection_graph_identity_id: UUID | None = None,
        object_instance_graph_identity_id: UUID,
        object_instance_graph_id: UUID,
        pre_state_index: CommitStateIndex,
        root_metadata: ObjectInstanceGraphCommitRootMetadata,
        root_object_id: UUID | None = None,
        changes: list[ObjectInstanceGraphChange],
        graph_hash_pre: str,
        graph_hash_post: str,
        author_id: UUID,
        commit_id: UUID | None = None,
        source_language: CodeLanguage = DEFAULT_SOURCE_LANGUAGE,
        status: CommitStatus = DEFAULT_COMMIT_STATUS,
        commit_action: CommitActionDescriptor | None = None,
    ) -> ObjectInstanceGraphCommit | None:
        """Commit using a canonical `Lane` without hydrating before_oig."""
        return await self.commit_shallow(
            branch_id=lane.branch_id,
            projection_hash=lane.lane_hash,
            object_projection_graph_identity_id=object_projection_graph_identity_id,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            object_instance_graph_id=object_instance_graph_id,
            pre_state_index=pre_state_index,
            root_metadata=root_metadata,
            root_object_id=root_object_id,
            changes=changes,
            graph_hash_pre=graph_hash_pre,
            graph_hash_post=graph_hash_post,
            author_id=author_id,
            commit_id=commit_id,
            source_language=source_language,
            status=status,
            commit_action=commit_action,
        )


__all__ = [
    "LaneCommitError",
    "LaneBeforeOigHashMismatchDetails",
    "LaneBeforeOigHashMismatchError",
    "LaneStateIndexPreHashMismatchDetails",
    "LaneStateIndexPreHashMismatchError",
    "LaneHeadPreHashMismatchDetails",
    "LaneHeadPreHashMismatchError",
    "FSLaneCommitter",
]
