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

from collections.abc import Mapping
from dataclasses import dataclass
import time
from typing import cast
from uuid import UUID

from aware_history_ontology.commit.commit_enums import CommitStatus
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
    build_object_instance_graph_seed_commit,
)
from aware_meta.graph.instance.commit.contract import (
    CommitActionDescriptor,
    CommitStateIndex,
    ObjectInstanceGraphCommitRootMetadata,
)
from aware_meta.graph.instance.commit.hash_contract import compute_oig_lane_hash_state
from aware_meta.graph.instance.commit.fs_store import FSCommitStore
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
            existing = await self._store.get_commit(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
            )
            if existing is None:
                raise LaneCommitError(
                    f"Lane HEAD points to {commit_id} but commit file is missing"
                )
            existing, repaired_identity = (
                _canonicalize_existing_commit_identity_metadata(
                    commit=existing,
                    object_instance_graph_identity_id=object_instance_graph_identity_id,
                    object_instance_graph_id=object_instance_graph_id,
                )
            )
            if repaired_identity:
                _ = await self._store.put_commit_file(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    commit=existing,
                    commit_action=commit_action,
                )
            perf["idempotent_head_hit"] = 1
            if repaired_identity:
                perf["idempotent_repaired_commit_identity_metadata"] = 1
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
        if not projection_hash:
            raise LaneCommitError("projection_hash is required")
        if not graph_hash_post:
            raise LaneCommitError("graph_hash_post is required")
        if before_oig.id != object_instance_graph_id:
            raise LaneCommitError(
                "before_oig.id must match object_instance_graph_id: "
                + f"before_oig.id={before_oig.id} object_instance_graph_id={object_instance_graph_id}"
            )
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
            existing = await self._store.get_commit(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
            )
            if existing is None:
                raise LaneCommitError(
                    f"Lane HEAD points to {commit_id} but commit file is missing"
                )
            existing, repaired_identity = (
                _canonicalize_existing_commit_identity_metadata(
                    commit=existing,
                    object_instance_graph_identity_id=object_instance_graph_identity_id,
                    object_instance_graph_id=object_instance_graph_id,
                )
            )
            if repaired_identity:
                _ = await self._store.put_commit_file(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    commit=existing,
                    commit_action=commit_action,
                )
            perf["idempotent_head_hit"] = 1
            if repaired_identity:
                perf["idempotent_repaired_commit_identity_metadata"] = 1
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
