from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from aware_meta.graph.instance.commit.committer import FSLaneCommitter
from aware_meta.graph.instance.commit.body_codec import (
    OigCommitBodyDraft,
    object_instance_graph_changes_from_body_draft,
)
from aware_meta.graph.instance.commit.contract import (
    CommitActionDescriptor,
    LaneCommitBatchRequest,
)
from aware_meta.graph.instance.commit.perf_trace import commit_perf_span
from aware_meta.runtime.invocation_commit_actions import MetaInvocationCommitAction
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)


class InvocationLaneCommitter(Protocol):
    async def commit(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        object_projection_graph_identity_id: UUID | None = None,
        object_instance_graph_identity_id: UUID,
        object_instance_graph_id: UUID,
        before_oig: ObjectInstanceGraph,
        root_object_id: UUID | None,
        changes: list[ObjectInstanceGraphChange],
        graph_hash_pre: str,
        graph_hash_post: str,
        author_id: UUID,
        commit_action: CommitActionDescriptor | None,
        body_draft: OigCommitBodyDraft | None = None,
    ) -> ObjectInstanceGraphCommit | None: ...

    async def commit_many(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        requests: tuple[LaneCommitBatchRequest, ...],
    ) -> tuple[ObjectInstanceGraphCommit, ...]: ...

    def last_commit_perf_profile_snapshot(self) -> dict[str, int]: ...


@dataclass(frozen=True)
class InvocationDomainCommitAppendResult:
    commit: ObjectInstanceGraphCommit | None
    perf_profile: dict[str, int]


async def append_invocation_domain_commit(
    *,
    branch_id: UUID,
    projection_hash: str,
    object_projection_graph_identity_id: UUID | None = None,
    object_instance_graph_identity_id: UUID,
    object_instance_graph_id: UUID,
    before_oig: ObjectInstanceGraph,
    root_object_id: UUID | None,
    changes: list[ObjectInstanceGraphChange],
    graph_hash_pre: str,
    graph_hash_post: str,
    author_id: UUID,
    action: MetaInvocationCommitAction,
    body_draft: OigCommitBodyDraft | None = None,
    committer: InvocationLaneCommitter | None = None,
) -> InvocationDomainCommitAppendResult:
    metadata = {
        "branch_id": str(branch_id),
        "projection_hash": projection_hash,
        "object_instance_graph_identity_id": str(object_instance_graph_identity_id),
        "object_instance_graph_id": str(object_instance_graph_id),
        "change_count": len(changes),
        "body_draft_root_count": len(body_draft.roots) if body_draft else 0,
        "operation_label": action.operation_label,
    }
    with commit_perf_span(
        phase="runtime.invoke_function.domain_commit.resolve_committer",
        category="meta.runtime.invoke_function",
        metadata=metadata,
    ):
        lane_committer = committer if committer is not None else FSLaneCommitter()
    with commit_perf_span(
        phase="runtime.invoke_function.domain_commit.invoke_committer",
        category="meta.runtime.invoke_function",
        metadata=metadata,
    ):
        commit = await lane_committer.commit(
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_projection_graph_identity_id=object_projection_graph_identity_id,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            object_instance_graph_id=object_instance_graph_id,
            before_oig=before_oig,
            root_object_id=root_object_id,
            changes=changes,
            body_draft=body_draft,
            graph_hash_pre=graph_hash_pre,
            graph_hash_post=graph_hash_post,
            author_id=author_id,
            commit_action=_commit_action_descriptor(action),
        )
    with commit_perf_span(
        phase="runtime.invoke_function.domain_commit.perf_profile_snapshot",
        category="meta.runtime.invoke_function",
        metadata=metadata,
    ):
        perf_profile = lane_committer.last_commit_perf_profile_snapshot()
    return InvocationDomainCommitAppendResult(
        commit=commit,
        perf_profile=perf_profile,
    )


async def append_invocation_domain_commit_batch(
    *,
    branch_id: UUID,
    projection_hash: str,
    requests: Sequence[LaneCommitBatchRequest],
    committer: InvocationLaneCommitter | None = None,
) -> tuple[InvocationDomainCommitAppendResult, ...]:
    request_tuple = tuple(requests)
    metadata = {
        "branch_id": str(branch_id),
        "projection_hash": projection_hash,
        "batch_request_count": len(request_tuple),
        "change_count": sum(len(tuple(request.changes)) for request in request_tuple),
    }
    with commit_perf_span(
        phase="runtime.invoke_function.domain_commit.resolve_committer",
        category="meta.runtime.invoke_function",
        metadata=metadata,
    ):
        lane_committer = committer if committer is not None else FSLaneCommitter()
    with commit_perf_span(
        phase="runtime.invoke_function.domain_commit.invoke_committer_batch",
        category="meta.runtime.invoke_function",
        metadata=metadata,
    ):
        commits = await lane_committer.commit_many(
            branch_id=branch_id,
            projection_hash=projection_hash,
            requests=request_tuple,
        )
    if len(commits) != len(request_tuple):
        raise RuntimeError(
            "Invocation domain commit batch returned an unexpected commit count: "
            f"expected={len(request_tuple)} got={len(commits)}"
        )
    with commit_perf_span(
        phase="runtime.invoke_function.domain_commit.perf_profile_snapshot",
        category="meta.runtime.invoke_function",
        metadata=metadata,
    ):
        perf_profile = lane_committer.last_commit_perf_profile_snapshot()
    return tuple(
        InvocationDomainCommitAppendResult(
            commit=commit,
            perf_profile=dict(perf_profile),
        )
        for commit in commits
    )


def build_invocation_lane_commit_batch_request(
    *,
    object_projection_graph_identity_id: UUID | None = None,
    object_instance_graph_identity_id: UUID,
    object_instance_graph_id: UUID,
    before_oig: ObjectInstanceGraph,
    root_object_id: UUID | None,
    changes: Sequence[ObjectInstanceGraphChange],
    graph_hash_pre: str,
    graph_hash_post: str,
    author_id: UUID,
    action: MetaInvocationCommitAction,
    body_draft: OigCommitBodyDraft | None = None,
) -> LaneCommitBatchRequest:
    compatibility_changes = tuple(changes)
    if body_draft is not None and not compatibility_changes:
        compatibility_changes = object_instance_graph_changes_from_body_draft(
            draft=body_draft,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            object_instance_graph_id=object_instance_graph_id,
        )
    return LaneCommitBatchRequest(
        object_projection_graph_identity_id=object_projection_graph_identity_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
        before_oig=before_oig,
        root_object_id=root_object_id,
        changes=compatibility_changes,
        body_draft=body_draft,
        graph_hash_pre=graph_hash_pre,
        graph_hash_post=graph_hash_post,
        author_id=author_id,
        commit_action=_commit_action_descriptor(action),
    )


def _commit_action_descriptor(
    action: MetaInvocationCommitAction,
) -> CommitActionDescriptor:
    return CommitActionDescriptor(
        operation_label=action.operation_label,
        call_target=action.call_target,
        function_id=action.function_id,
        object_id=action.object_id,
        class_instance_identity_id=action.class_instance_identity_id,
    )


__all__ = [
    "InvocationDomainCommitAppendResult",
    "InvocationLaneCommitter",
    "LaneCommitBatchRequest",
    "append_invocation_domain_commit",
    "append_invocation_domain_commit_batch",
    "build_invocation_lane_commit_batch_request",
]
