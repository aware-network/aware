from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from aware_meta.graph.instance.commit.committer import FSLaneCommitter
from aware_meta.graph.instance.commit.fs_store import CommitActionDescriptor
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
    ) -> ObjectInstanceGraphCommit | None: ...

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
    committer: InvocationLaneCommitter | None = None,
) -> InvocationDomainCommitAppendResult:
    lane_committer = committer if committer is not None else FSLaneCommitter()
    commit = await lane_committer.commit(
        branch_id=branch_id,
        projection_hash=projection_hash,
        object_projection_graph_identity_id=object_projection_graph_identity_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
        before_oig=before_oig,
        root_object_id=root_object_id,
        changes=changes,
        graph_hash_pre=graph_hash_pre,
        graph_hash_post=graph_hash_post,
        author_id=author_id,
        commit_action=_commit_action_descriptor(action),
    )
    return InvocationDomainCommitAppendResult(
        commit=commit,
        perf_profile=lane_committer.last_commit_perf_profile_snapshot(),
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
    "append_invocation_domain_commit",
]
