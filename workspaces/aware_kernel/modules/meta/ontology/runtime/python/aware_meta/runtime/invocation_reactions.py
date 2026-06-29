from __future__ import annotations

from collections.abc import Awaitable, Callable
from uuid import UUID

from aware_meta.runtime.commit.required_reactions import (
    RuntimeCommitReactionContext,
    RuntimeCommitReactionReceipt,
    run_required_runtime_commit_reactions,
)
from aware_meta.runtime.invocation_commit_actions import MetaInvocationCommitAction
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_orm.session.execution_guard import (
    reset_mutation_owner,
    set_mutation_owner,
)


InvocationRequiredReactionRunner = Callable[
    [RuntimeCommitReactionContext],
    Awaitable[tuple[RuntimeCommitReactionReceipt, ...]],
]


async def run_invocation_required_commit_reactions(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID,
    domain_branch_id: UUID,
    domain_projection_hash: str,
    domain_commit: ObjectInstanceGraphCommit,
    action: MetaInvocationCommitAction | None = None,
    source_class_instance_identity_id: UUID | None = None,
    perf_ms: dict[str, int] | None = None,
    runner: InvocationRequiredReactionRunner = run_required_runtime_commit_reactions,
) -> tuple[RuntimeCommitReactionReceipt, ...]:
    source_identity_id = source_class_instance_identity_id
    if source_identity_id is None and action is not None:
        source_identity_id = action.class_instance_identity_id

    token = set_mutation_owner(None)
    try:
        return await runner(
            RuntimeCommitReactionContext(
                index=index,
                actor_id=actor_id,
                domain_branch_id=domain_branch_id,
                domain_projection_hash=domain_projection_hash,
                domain_commit=domain_commit,
                source_class_instance_identity_id=source_identity_id,
                perf_ms=perf_ms,
            )
        )
    finally:
        reset_mutation_owner(token)


__all__ = [
    "InvocationRequiredReactionRunner",
    "run_invocation_required_commit_reactions",
]
